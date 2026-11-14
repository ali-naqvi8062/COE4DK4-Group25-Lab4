/* COE4DK4 Lab 4, Group 25. Times are in milliseconds. */
#include <assert.h>
#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { ACK, RECEIVE, TIMEOUT, TX_DONE };
typedef struct {
    double time;
    int type;
    int64_t seq;
    uint64_t token, order;
} Event;
typedef struct {
    int64_t seq;
    uint64_t token;
    bool acked, retry;
} Packet;
typedef struct {
    int ws, wr, n, reps;
    uint64_t seed;
    double pd, pa, timeout, duration, warmup;
    bool trace, drop_data, drop_ack;
} Config;
typedef struct {
    Config c;
    Event *heap;
    size_t size, capacity;
    Packet *packets;
    int64_t *received;
    int64_t base, next, receive_base;
    uint64_t order, timer, data_rng, ack_rng;
    uint64_t attempts, delivered, data_errors, ack_errors, timeouts;
    double now;
    bool busy, dropped_data, dropped_ack;
} Simulation;
typedef struct {
    double time, efficiency, attempts_per_packet;
    uint64_t attempts, delivered, data_errors, ack_errors, timeouts;
} Result;

static void *allocate(size_t count, size_t bytes) {
    void *p = calloc(count, bytes);
    if (!p) { fprintf(stderr, "Out of memory\n"); exit(1); }
    return p;
}

/* SplitMix64 gives reproducible, separate data and ACK streams. */
static uint64_t random_bits(uint64_t *state) {
    uint64_t z = (*state += UINT64_C(0x9e3779b97f4a7c15));
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}
static double uniform(uint64_t *state) {
    return (random_bits(state) >> 11) * 0x1.0p-53;
}
static bool before(Event a, Event b) {
    if (a.time != b.time) return a.time < b.time;
    if (a.type != b.type) return a.type < b.type;
    return a.order < b.order;
}
static void schedule(Simulation *s, double time, int type, int64_t seq, uint64_t token) {
    assert(time >= s->now);
    if (s->size == s->capacity) {
        s->capacity = s->capacity ? 2 * s->capacity : 128;
        s->heap = realloc(s->heap, s->capacity * sizeof(Event));
        if (!s->heap) exit(1);
    }
    Event e = {time, type, seq, token, s->order++};
    size_t i = s->size++;
    while (i && before(e, s->heap[(i - 1) / 2])) {
        s->heap[i] = s->heap[(i - 1) / 2]; i = (i - 1) / 2;
    }
    s->heap[i] = e;
}
static Event pop(Simulation *s) {
    Event first = s->heap[0], last = s->heap[--s->size];
    size_t i = 0;
    while (2 * i + 1 < s->size) {
        size_t j = 2 * i + 1;
        if (j + 1 < s->size && before(s->heap[j + 1], s->heap[j])) j++;
        if (!before(s->heap[j], last)) break;
        s->heap[i] = s->heap[j]; i = j;
    }
    if (s->size) s->heap[i] = last;
    return first;
}
static Packet *packet(Simulation *s, int64_t seq) {
    return &s->packets[seq % s->c.ws];
}
static bool measured(Simulation *s) {
    return s->c.n > 0 || s->now >= s->c.warmup;
}
static void trace(Simulation *s, const char *event, int64_t seq) {
    if (s->c.trace)
        fprintf(stderr, "%.3f,%s,%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64 "\n",
                s->now, event, seq, s->base, s->next, s->receive_base);
}
static void gbn_timer(Simulation *s) {
    s->timer++;
    if (s->base < s->next)
        schedule(s, s->now + s->c.timeout, TIMEOUT, s->base, s->timer);
}
static void transmit(Simulation *s) {
    if (s->busy) return;
    int64_t seq = -1;
    for (int64_t i = s->base; i < s->next; i++) {
        Packet *p = packet(s, i);
        if (p->retry && !p->acked) { seq = i; break; }
    }
    if (seq < 0) {
        if (s->next - s->base >= s->c.ws || (s->c.n && s->next >= s->c.n)) return;
        seq = s->next++;
        *packet(s, seq) = (Packet){.seq = seq};
        trace(s, "SEND", seq);
    } else trace(s, "RETRY", seq);
    Packet *p = packet(s, seq);
    p->retry = false;
    p->token++;
    s->busy = true;
    if (measured(s)) s->attempts++;
    schedule(s, s->now + 1, TX_DONE, seq, 0);
    schedule(s, s->now + 6, RECEIVE, seq, 0);
    if (s->c.wr == 1) {
        if (seq == s->base) gbn_timer(s);
    } else schedule(s, s->now + s->c.timeout, TIMEOUT, seq, p->token);
}
static void receive(Simulation *s, int64_t seq) {
    bool lost = uniform(&s->data_rng) < s->c.pd;
    if (s->c.drop_data && !s->dropped_data) { lost = true; s->dropped_data = true; }
    if (lost) {
        if (measured(s)) s->data_errors++;
        trace(s, "DATA_LOSS", seq); return;
    }
    int64_t ack = seq;
    if (seq < s->receive_base) trace(s, "DUPLICATE", seq);
    else if (seq >= s->receive_base + s->c.wr) {
        trace(s, "OUTSIDE_WINDOW", seq);
        if (s->c.wr > 1) return;
    } else {
        s->received[seq % s->c.wr] = seq;
        trace(s, "ACCEPT", seq);
        while (s->received[s->receive_base % s->c.wr] == s->receive_base) {
            s->received[s->receive_base % s->c.wr] = -1;
            if (measured(s)) s->delivered++;
            trace(s, "DELIVER", s->receive_base);
            s->receive_base++;
        }
    }
    if (s->c.wr == 1) ack = s->receive_base - 1;
    trace(s, "ACK_SEND", ack);
    bool ack_lost = uniform(&s->ack_rng) < s->c.pa;
    if (s->c.drop_ack && !s->dropped_ack) { ack_lost = true; s->dropped_ack = true; }
    if (ack_lost) {
        if (measured(s)) s->ack_errors++;
        trace(s, "ACK_LOSS", ack);
    } else schedule(s, s->now + 5, ACK, ack, 0);
}
static void acknowledge(Simulation *s, int64_t seq) {
    trace(s, "ACK_RECEIVE", seq);
    if (seq < s->base || seq >= s->next) return;
    int64_t old_base = s->base;
    if (s->c.wr == 1) s->base = seq + 1;
    else {
        packet(s, seq)->acked = true;
        packet(s, seq)->retry = false;
        while (s->base < s->next && packet(s, s->base)->acked) s->base++;
    }
    if (s->c.wr == 1 && s->base != old_base) gbn_timer(s);
}
static void timeout(Simulation *s, Event e) {
    if (s->c.wr == 1) {
        if (e.token != s->timer || s->base == s->next) return;
        for (int64_t i = s->base; i < s->next; i++) packet(s, i)->retry = true;
    } else {
        if (e.seq < s->base || e.seq >= s->next) return;
        Packet *p = packet(s, e.seq);
        if (p->acked || p->token != e.token) return;
        p->retry = true;
    }
    if (measured(s)) s->timeouts++;
    trace(s, "TIMEOUT", e.seq);
}
static Result run(Config c, unsigned repetition) {
    Simulation s = {.c = c};
    uint64_t seed = c.seed + UINT64_C(0xd1342543de82ef95) * repetition;
    s.data_rng = random_bits(&seed); s.ack_rng = random_bits(&seed);
    s.packets = allocate(c.ws, sizeof(Packet));
    s.received = allocate(c.wr, sizeof(int64_t));
    for (int i = 0; i < c.wr; i++) s.received[i] = -1;
    double end = c.warmup + c.duration;
    if (c.trace) fprintf(stderr, "time_ms,event,sequence,send_base,next_sequence,receive_base\n");
    transmit(&s);
    while (s.size) {
        double time = s.heap[0].time;
        if (!c.n && time >= end) { s.now = end; break; }
        s.now = time;
        do {
            Event e = pop(&s);
            switch (e.type) {
                case ACK: acknowledge(&s, e.seq); break;
                case RECEIVE: receive(&s, e.seq); break;
                case TIMEOUT: timeout(&s, e); break;
                case TX_DONE: s.busy = false; break;
            }
        } while (s.size && s.heap[0].time == time);
        assert(s.base <= s.next && s.next - s.base <= c.ws);
        assert(s.receive_base <= s.next);
        if (c.n && s.base == c.n) break;
        transmit(&s);
        if (s.now > 1e10) { fprintf(stderr, "Run exceeded time limit\n"); exit(1); }
    }
    if (c.n) assert(s.base == c.n && s.delivered == (uint64_t)c.n);
    double elapsed = c.n ? s.now : c.duration;
    Result r = {elapsed, s.delivered / elapsed,
                s.delivered ? (double)s.attempts / s.delivered : 0,
                s.attempts, s.delivered, s.data_errors, s.ack_errors, s.timeouts};
    free(s.packets); free(s.received); free(s.heap);
    return r;
}
int main(int argc, char **argv) {
    Config c = {.ws=16, .wr=16, .reps=1, .seed=1, .timeout=15,
                .duration=500000, .warmup=50000};
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--trace")) c.trace = true;
        else if (!strcmp(argv[i], "--drop-first-data")) c.drop_data = true;
        else if (!strcmp(argv[i], "--drop-first-ack")) c.drop_ack = true;
        else {
            if (i + 1 == argc) { fprintf(stderr, "Missing value\n"); return 2; }
            const char *key = argv[i++], *value = argv[i];
            if (!strcmp(key, "--ws")) c.ws = atoi(value);
            else if (!strcmp(key, "--wr")) c.wr = atoi(value);
            else if (!strcmp(key, "--n")) c.n = atoi(value);
            else if (!strcmp(key, "--reps")) c.reps = atoi(value);
            else if (!strcmp(key, "--seed")) c.seed = strtoull(value, NULL, 10);
            else if (!strcmp(key, "--pd")) c.pd = atof(value);
            else if (!strcmp(key, "--pa")) c.pa = atof(value);
            else if (!strcmp(key, "--timeout")) c.timeout = atof(value);
            else if (!strcmp(key, "--duration")) c.duration = atof(value);
            else if (!strcmp(key, "--warmup")) c.warmup = atof(value);
            else { fprintf(stderr, "Unknown argument: %s\n", key); return 2; }
        }
    }
    if (c.ws < 1 || c.wr < 1 || c.ws > 10000 || c.wr > 10000 || c.n < 0 ||
        c.reps < 1 || !(c.pd >= 0 && c.pd < 1) || !(c.pa >= 0 && c.pa < 1) ||
        !(c.timeout > 0) || !isfinite(c.timeout) || !(c.duration > 0) ||
        !isfinite(c.duration) || !(c.warmup >= 0) || !isfinite(c.warmup) ||
        (c.trace && c.reps != 1)) {
        fprintf(stderr, "Invalid simulation parameters\n"); return 2;
    }
    double mean = 0, m2 = 0, efficiency = 0, attempts = 0;
    uint64_t tx = 0, delivered = 0, de = 0, ae = 0, to = 0;
    for (int i = 0; i < c.reps; i++) {
        Result r = run(c, (unsigned)i);
        double delta = r.time - mean;
        mean += delta / (i + 1); m2 += delta * (r.time - mean);
        efficiency += r.efficiency; attempts += r.attempts_per_packet;
        tx += r.attempts; delivered += r.delivered;
        de += r.data_errors; ae += r.ack_errors; to += r.timeouts;
    }
    printf("{\"time_ms\":%.9f,\"time_sd\":%.9f,\"efficiency\":%.9f,"
           "\"attempts_per_packet\":%.9f,\"attempts\":%" PRIu64 ","
           "\"delivered\":%" PRIu64 ",\"data_errors\":%" PRIu64 ","
           "\"ack_errors\":%" PRIu64 ",\"timeouts\":%" PRIu64 "}\n",
           mean, c.reps > 1 ? sqrt(m2 / (c.reps - 1)) : 0,
           efficiency / c.reps, attempts / c.reps, tx, delivered, de, ae, to);
    return 0;
}
