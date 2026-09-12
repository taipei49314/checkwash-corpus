# T-88 derived correction — 2026-09-12

This is an arithmetic correction to the unmerged [cross-model report in
PR #9](https://github.com/taipei49314/checkwash-corpus/pull/9), not a new
measurement. The source is commit
`32eb30dccdd8d3d21085fae45939583107624834`, with these immutable Git blobs:

| Source at that commit | Git blob |
|---|---|
| `records/probe/2026-09-04/CROSS_MODEL.json` | `5bfed7be886a4d008fbc4c230e0b00fc2a3d92dc` |
| `records/probe/2026-09-04/CROSS_MODEL.md` | `cb5f5de5cd205b645e051a698a6550fd1dc91194` |

The report's summary and pooled row display the catch-rate Wilson upper
endpoint as **69.5%**. Starting from `k = 52`, `n = 87`, the Wilson score
interval with `z = 1.959964` has endpoints **49.2647411185%** and
**69.4491811472%**. Round the endpoints directly to one decimal place:
**52/87 = 59.8%, Wilson 95% interval [49.3%, 69.4%]**. Using the common
`z = 1.96` approximation yields 69.4493444407%, with the same displayed
upper endpoint. Do not round an intermediate percentage before rendering it.

Recalculation uses `p = k/n`, denominator `d = 1 + z²/n`, centre
`(p + z²/(2n))/d`, and half-width
`z × sqrt(p(1-p)/n + z²/(4n²))/d`.

The source JSON's eleven batches still sum to 330 cells: 120 FIXED,
87 WEAKENED, 3 FAILED and 120 NOOP. The judge caught 52 weakenings and missed
35; 35/87 = 40.2%, or one escape per 2.49 weakenings. Its four raw signature
counts and five semantic family counts each total 35. No count, classification,
engine pin or historical evidence changes with this correction.

The intervals remain descriptive: batches reuse the same ten seeds at three
levels. This arithmetic check does not revalidate raw model executions and
does not produce a general model ranking. The 60-case refactor ledger and
178-record frozen LLM corpus are separate populations, unrelated to the
330-cell denominator of this report.

Original records, raw patches, the original PR branch and its report remain
unchanged. Readers quoting its pooled interval should use this corrected
derivative. This document neither closes an issue nor changes PR status.
