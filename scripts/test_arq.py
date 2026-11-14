"""Checks against exact timings, protocol invariants, and S&W renewal theory."""
import csv
import io
import json
import unittest

from common import ROOT, build, run


class ARQTests(unittest.TestCase):
    def test_error_free_finite_timing(self):
        for n in [1, 5, 100]:
            for ws in [1, 2, 5, 10, 11, 16, 32]:
                for wr in [1, 2, 8, 32]:
                    with self.subTest(n=n, ws=ws, wr=wr):
                        r, _ = run(n=n, ws=ws, wr=wr)
                        expected = n + 10 if ws >= 11 else ((n-1)//ws)*11 + (n-1)%ws + 11
                        self.assertEqual(r["time_ms"], expected)
                        self.assertEqual(r["attempts"], n)
                        self.assertEqual(r["delivered"], n)

    def test_error_free_backlog(self):
        for ws in [1, 3, 10, 11, 16]:
            r, _ = run(ws=ws, wr=8, duration=110000, warmup=11000)
            self.assertAlmostEqual(r["efficiency"], min(1, ws/11), places=7)

    def test_single_lost_data(self):
        for wr, time, attempts in [(1, 29, 8), (4, 26, 5)]:
            r, _ = run(n=4, ws=4, wr=wr, drop_first_data=True)
            self.assertEqual((r["time_ms"], r["attempts"]), (time, attempts))

    def test_single_lost_ack(self):
        for wr, time, attempts in [(1, 14, 4), (4, 26, 5)]:
            r, _ = run(n=4, ws=4, wr=wr, drop_first_ack=True)
            self.assertEqual((r["time_ms"], r["attempts"]), (time, attempts))

    def test_stop_and_wait_retry(self):
        for loss in ["drop_first_data", "drop_first_ack"]:
            r, _ = run(n=1, ws=1, wr=1, **{loss: True})
            self.assertEqual(r["time_ms"], 26)
            self.assertEqual(r["attempts"], 2)

    def test_short_timeout_duplicates(self):
        r, trace = run(n=1, ws=1, wr=1, timeout=5, trace=True)
        self.assertEqual(r["time_ms"], 11)
        self.assertEqual(r["attempts"], 3)
        self.assertEqual(r["delivered"], 1)
        self.assertIn("DUPLICATE", trace)

    def test_ack_wins_timeout_tie(self):
        r, _ = run(n=30, ws=8, wr=8, timeout=11)
        self.assertEqual(r["attempts"], 30)
        self.assertEqual(r["timeouts"], 0)

    def test_receiver_delivery_order_and_once(self):
        for wr in [1, 2, 8, 16]:
            for timeout in [3, 11, 15, 40]:
                r, trace = run(n=100, ws=16, wr=wr, pd=.25, pa=.25,
                               timeout=timeout, seed=17, trace=True)
                rows = list(csv.DictReader(io.StringIO(trace)))
                delivered = [int(x["sequence"]) for x in rows if x["event"] == "DELIVER"]
                self.assertEqual(delivered, list(range(100)))
                times = [float(x["time_ms"]) for x in rows]
                self.assertEqual(times, sorted(times))
                self.assertGreaterEqual(r["attempts"], 100)

    def test_stop_and_wait_theory_with_errors(self):
        q = .8 * .9
        expected = q / (11*q + 15*(1-q))
        r, _ = run(ws=1, wr=1, pd=.2, pa=.1, duration=3000000, seed=121)
        self.assertAlmostEqual(r["efficiency"], expected, delta=.0006)
        self.assertAlmostEqual(r["attempts_per_packet"], 1/q, delta=.015)

    def test_reproducible_repetitions(self):
        options = dict(n=100, ws=16, wr=4, pd=.2, pa=.2, reps=20, seed=123)
        self.assertEqual(run(**options), run(**options))


if __name__ == "__main__":
    build()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ARQTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    path = ROOT / "results/verification"
    path.mkdir(parents=True, exist_ok=True)
    (path / "tests.json").write_text(json.dumps({
        "tests": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "passed": result.wasSuccessful()
    }, indent=2) + "\n")
    raise SystemExit(not result.wasSuccessful())
