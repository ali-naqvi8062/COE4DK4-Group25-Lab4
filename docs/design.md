# Simulation design

`src/arq.c` is a standalone C11 discrete-event simulator. The previous ALOHA
files are retained in `legacy/` for history and are not linked into it.

One sender uses one serialized data link. A packet takes 1 ms to transmit and
5 ms to propagate. ACKs take 5 ms to propagate; their transmission and
processing times are zero. Thus an undamaged packet's ACK arrives 11 ms after
its transmission starts. The default timeout is 15 ms, measured from the
start of transmission.

The shared sender and receiver are parameterized by send window Ws and
receive window Wr. With Wr > 1, the receiver buffers packets in its current
window and sends individual ACKs. The sender uses one timer per outstanding
packet. With Wr = 1, it discards out-of-order packets, sends cumulative ACKs,
and uses one timer for the oldest outstanding packet. On expiry, it queues
all outstanding packets for retransmission in order. Ws = Wr = 1 gives S&W.
This explicit change in ACK and timer behavior is needed to obtain conventional
GBN; reducing only an SR receive buffer would not provide cumulative ACKs or
GBN's retransmission rule.

## Events and state

The event heap holds ACK arrival, data arrival, timeout, and end of transmission.
Equal-time events are processed in that order, with insertion order breaking
remaining ties. A new transmission starts only after all events at that time
are handled. ACKs therefore take precedence over a simultaneous timeout.

Sender state consists of the oldest unacknowledged sequence number, next new
sequence number, link busy flag, and each outstanding packet's ACK flag,
retry flag, and timer version. The receiver stores the next sequence number
to deliver and a circular buffer of accepted sequence numbers. Increasing
64-bit sequence numbers avoid wraparound ambiguity. Packet payloads are not
stored; all packets are the specified fixed size.

GBN restarts its timer when a cumulative ACK advances the send base, and when
the base packet is transmitted. SR restarts a packet's timer when that packet
is transmitted. An expired timer queues a retry; it never interrupts a packet
already on the link. Retries precede new packets and use increasing sequence
order. ACKs cancel queued retries. Version numbers make superseded timer
events harmless. No NAKs or fast retransmission are used.

Data errors and ACK errors are independent Bernoulli trials on separate
SplitMix64 streams. A damaged data packet causes no ACK. A successfully
received duplicate is acknowledged again, without being delivered twice.
GBN acknowledges the last contiguous packet when it receives an out-of-order
packet. SR discards packets beyond its receive window without acknowledging
them, so a later retry can be accepted. Receiving and acknowledging a packet
can overlap transmission of another packet.

## Measurements

For a backlogged source, new packets are always available. Measurements cover
[warmup, warmup + duration), while events during warmup still update state.
Efficiency is newly delivered in-order packets times 1 ms divided by the
measurement duration. Attempts per delivered packet is transmission starts
in that interval divided by newly delivered packets. Boundary differences of
in-flight packets are negligible for long runs and are checked with longer runs.

For a finite source, N packets are available at time zero. Completion is the
time from the first transmission start until the sender has ACKs covering all
N packets. There is no warmup. Attempts include all transmissions started
before completion, including unnecessary duplicates from short timeouts.

Replications use the same base seeds for all protocols. Each repetition derives
two streams from the base seed and repetition index. Equal seeds do not mean
identical packet-by-packet loss histories: protocols consume random draws in
different orders. This is a comparison using shared seed sets, not a claim of
perfectly paired loss sequences.

## Verification

Run `python scripts/test_arq.py`. Exact checks cover error-free finite transfer
times, error-free saturated efficiency, a single lost data packet, a single
lost ACK, short timeouts, ACK/timeout ties, in-order delivery without duplicates,
and repeatability. A long S&W run is checked against its renewal expression.
`python scripts/verify.py` writes all six Experiment 1 traces.
