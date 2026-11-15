# Lab 4 requirements checklist

Page references refer to the shortened 12-page PDF and Word reports.

| Requirement | Evidence | Pages |
| --- | --- | --- |
| Simulator design, events, state variables and assumptions | Shared ARQ model; send and receive windows; ACK rules; timers; independent errors | 2 |
| Default packet size, rate, propagation and timeout | 1000 bits, 1 Mbps, 5 ms each way, 15 ms | 2 |
| Experimental parameters and common student-number seeds | Table 1, exact sweep ranges, run lengths and repetitions | 3 |
| Verification traces at pd=pa=0 and pd=pa=0.5 for all protocols | Table 2; complete logs in results/verification/ | 4 |
| Verification and reliability explanation | Exact timing and loss checks; confidence intervals; longer-run comparison | 3-4 |
| 2: efficiency versus Ws, three SR Wr values and S&W reference | Figure 1; analytical comparison and discussion | 5 |
| 3(a): efficiency versus pd including zero, sufficiently large Ws | Figure 2; Wr=4,16,32; comparison with analytical expressions | 6 |
| 3(b): efficiency and attempts versus Ws | Figures 3-4; pd=0.1; three SR Wr values | 7 |
| 4: efficiency and attempts versus pa, same windows as 3(a) | Figures 5-6; comparison of data and ACK errors and window effects | 8 |
| 5: efficiency and attempts versus short, moderate and long timeouts | Figures 7-8; 2 to 120 ms; protocol-specific discussion | 9 |
| 6: N=100, all three required error cases, completion versus Ws | Figures 9-11; three SR Wr values and S&W reference; data/ACK error discussion | 10-11 |
| 7: at least two additional N values using a suitable subset of Part 6 | Figures 12-13; N=10 and N=1000; pd=pa=0.05; comparison with N=100 | 12 |
| Complete simulation program submitted separately | output/COE4DK4_Group25_Lab4_Code.zip | Separate submission |
| Labeled plots with measured markers | All 13 figures retain axes, units, curves and settings | 5-12 |

Connecting segments are visual guides between measured markers, with no fitted
curves or synthetic intermediate data. The underlying results retain the extra
Experiment 7 error cases, but the report uses one case as permitted by Part 7.

The course lecture slides were not supplied. The analytical comparisons cite
standard ARQ expressions and give the exact S&W expression for the model's
specified timeout.
