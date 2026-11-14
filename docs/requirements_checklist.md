# Lab 4 requirements checklist

All page references refer to the final 25-page report.

| Manual requirement | Implementation or evidence | Report pages |
| --- | --- | --- |
| General SR model with Ws and Wr; GBN and S&W settings | `src/arq.c`, `docs/design.md` | 2-3 |
| 1000 bits, 1 Mbps, 5 ms propagation each way, 15 ms default timeout | Model timing and all experiment configurations | 2-4 |
| Independent data and ACK errors | Separate random streams and loss events | 3 |
| Multiple common seeds including a student number | Five seeds; three student numbers; recorded in raw CSV files | 4 |
| State assumptions and design choices | Timer origin, GBN restart, ACK types, event ties, retry priority, receiver overflow, sequence numbers | 2-3 |
| 1: no-error and pd=pa=0.5 traces for all three protocols | Six complete CSV traces in `results/verification/`; selected entries in report | 5-8 |
| 1: explain verification | Exact timing tests, isolated losses, duplicates, ties, delivery order, analytical S&W check | 5-8 |
| 2: efficiency versus Ws, GBN/SR, three Wr values, S&W reference | Figure 1; Wr=2,8,32; Ws both sides of 11 | 9 |
| 2: analytical comparison and discussion | Exact no-error efficiency and feedback-cycle calculation | 5, 9 |
| 3(a): efficiency versus pd including zero, large Ws, three Wr>1 | Figure 2; Ws=32; Wr=4,16,32 | 10 |
| 3(a): analytical comparison | Exact S&W renewal result, ideal SR bound, GBN approximation with limitations | 5, 10 |
| 3(b): efficiency and attempts versus Ws at nonzero pd | Figures 3-4; pd=0.1; three Wr>1 and S&W reference | 11-12 |
| 4: efficiency and attempts versus pa from zero | Figures 5-6; pd=0.1; windows match 3(a) | 13-14 |
| 4: compare data/ACK errors and window effects | Cumulative ACK recovery, individual ACK waiting, small receive window | 13-14 |
| 5: timeout below, near, and well above round-trip delay | Figures 7-8; 2 to 120 ms; three Wr>1; common errors | 15-16 |
| 5: efficiency, attempts, protocol-specific discussion | Duplicate overhead, recovery waiting, S&W idle link, GBN group retries | 15-16 |
| 6: N=100 finite transfers, three specified error cases | Figures 9-11; 1000 repetitions per noisy point; three Wr>1 | 17-19 |
| 6: completion includes all ACKs at source | Sender base stopping condition and exact timing checks | 3, 5, 17-19 |
| 6: window, data error, ACK error discussion | Per-case numerical comparisons and final-ACK effects | 17-19 |
| 7: substantially smaller and larger N | N=10 and N=1000, all three error cases, Figures 12-17 | 20-23 |
| 7: explain size/window relationship | Serialization, final feedback overhead, sustained losses, small receiver limitation | 23 |
| Submission: full simulation program separately | `output/COE4DK4_Group25_Lab4_Code.zip` | 25 |
| Submission: selected code/pseudocode only in report | One concise algorithm listing | 3 |
| Submission: labeled axes, units, curves, parameters and measured markers | All 17 numbered figures; PNG and PDF copies | 9-22 |
| Submission: sufficient runs and variability analysis | Five-seed intervals, 1000 finite transfers, longer runs | 4, 24 |
| Rubric 2.1 / 4.4: principles and design justification | Shared event engine, ACK/timer rules, receiver buffering, assumptions | 2-5 |
| Rubric 2.2: substantiated analysis and limitations | Numerical observations, model-based explanations, analytical limits | 9-25 |
| Rubric 3.1: suitable ranges and reliability | Dense points near Ws=11 and Tout=11; five seeds; size range 10-1000 | 4, 24 |

Straight segments join measured markers at the user's request. They are visual
guides only; there is no fitting, added intermediate data, or smoothing. Theory
curves are explicitly labeled and are not simulation data.

The course's lecture slides were not supplied. Analytical comparisons use the
standard ARQ expressions, with an external university reference identified in
the report, and exact expressions derived for the stated simulator assumptions.
