# CMU eVTOL Measurement Summary

> Approved CC BY 4.0 cell-level evidence. Not pack-level proof and not
> candidate-ranking evidence.

## Status

- Quality status: blocked
- Timeseries files parsed: 21
- Impedance files parsed: 21
- Failed files: 1
- System boundary: cell-level eVTOL duty-cycle evidence only
- Pack-level evidence: False
- Candidate-ranking evidence: False

## Parsed Timeseries

| File | Rows | Voltage V | Temperature C | Current sign counts |
| --- | ---: | ---: | ---: | --- |
| `VAH07.csv` | 50000 | 2.500-4.201 | 22.54-54.77 | `{"negative": 39324, "positive": 6843, "zero": 3833}` |
| `VAH16.csv` | 50000 | 2.500-4.200 | 22.82-44.45 | `{"negative": 41689, "positive": 5186, "zero": 3125}` |
| `VAH15.csv` | 50000 | 2.500-4.200 | 22.38-47.21 | `{"negative": 40353, "positive": 6519, "zero": 3128}` |
| `VAH22.csv` | 50000 | 2.500-4.200 | 22.40-46.93 | `{"negative": 40192, "positive": 6508, "zero": 3300}` |
| `VAH20.csv` | 50000 | 2.500-4.200 | 23.51-46.77 | `{"negative": 41627, "positive": 5049, "zero": 3324}` |
| `VAH25.csv` | 50000 | 2.500-4.201 | 19.49-43.38 | `{"negative": 39753, "positive": 7217, "zero": 3030}` |
| `VAH23.csv` | 50000 | 2.500-4.201 | 21.72-49.15 | `{"negative": 34212, "positive": 9662, "zero": 6126}` |
| `VAH30.csv` | 50000 | 2.500-4.200 | 34.05-52.76 | `{"negative": 41450, "positive": 5263, "zero": 3287}` |
| `VAH24.csv` | 50000 | 2.500-4.201 | 21.85-46.09 | `{"negative": 34454, "positive": 9734, "zero": 5812}` |
| `VAH13.csv` | 50000 | 2.500-4.201 | 22.71-43.11 | `{"negative": 40576, "positive": 6072, "zero": 3352}` |
| `VAH17.csv` | 50000 | 2.500-4.200 | 21.93-44.39 | `{"negative": 41152, "positive": 6022, "zero": 2826}` |
| `VAH09.csv` | 50000 | 2.500-4.201 | 19.25-43.71 | `{"negative": 39784, "positive": 7247, "zero": 2969}` |
| `VAH26.csv` | 50000 | 2.500-4.201 | 21.76-42.69 | `{"negative": 40601, "positive": 6311, "zero": 3088}` |
| `VAH28.csv` | 50000 | 2.500-4.200 | 20.85-37.85 | `{"negative": 40749, "positive": 6704, "zero": 2547}` |
| `VAH06.csv` | 50000 | 2.500-4.201 | 23.08-45.73 | `{"negative": 33565, "positive": 9557, "zero": 6878}` |
| `VAH10.csv` | 50000 | 2.500-4.201 | 30.16-49.71 | `{"negative": 40209, "positive": 6293, "zero": 3498}` |
| `VAH05.csv` | 50000 | 2.500-4.200 | 22.56-39.53 | `{"negative": 40682, "positive": 6315, "zero": 3003}` |
| `VAH02.csv` | 50000 | 2.500-4.200 | 20.82-46.06 | `{"negative": 36426, "positive": 2631, "zero": 10943}` |
| `VAH01.csv` | 50000 | 2.500-4.200 | 20.85-45.23 | `{"negative": 35257, "positive": 2745, "zero": 11998}` |
| `VAH12.csv` | 50000 | 2.500-4.201 | 22.75-42.57 | `{"negative": 40195, "positive": 6072, "zero": 3733}` |
| `VAH11.csv` | 50000 | 2.500-4.201 | 21.75-34.50 | `{"negative": 41422, "positive": 5884, "zero": 2694}` |

## Failures

- `VAH27.csv`: VAH27.csv quality check failed: voltage outside positive plausible lithium-ion cell range

## Limitations

- This is cell-level experimental evidence from one approved dataset.
- The report does not create pack-level proof.
- The report does not allow candidate or chemistry ranking.
- Protocol details and cycleNumber caveats still require deeper audit.