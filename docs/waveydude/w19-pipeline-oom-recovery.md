# W-19 pipeline recovery experiment

W-18 reached a later area on base PS5 13.60. In that session, 557
graphics pipeline failures reported out of host memory and parts of
some models were missing. The log does not identify the individual draws.

Patch 0936 builds on the existing graphics worker OOM retry and
low-memory guard. After requesting reclaim, the worker can wait up to
128 ms longer before its final retry if the largest free block is
still below 16 MiB. The switch is off by default. A terminally failed
pipeline already cached in the current session is outside this patch's
scope. The separate CPUCore_1 invalid read remains unresolved.

Compare the same route with W-18. Check missing geometry, failed
pipelines, longest hitches and whether the run progresses. This is
an experiment and has no console gameplay result yet.
