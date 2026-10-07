# Memory-watchdog incidents, 2026-10-07

This DGX Spark (GB10, 121 GiB unified memory) runs the NVIDIA checkpoint of
Qwen3.8-Flash-Next-NVFP4 (weights 75.9 GiB + a 47.68 GiB PLE table, offloaded
to host memory) at `HOST_RESERVE_GIB=30`, `MAX_MODEL_LEN=16384` (reduced from
the native 262144 — see below). The kit's own watchdog (`files/memwatch.sh`)
stopped the container twice during this measurement session, both times with
an `EMERGENCY STOP MemFree under 2 GiB for 5 samples`:

1. **First stop**, during the Korean quality audit's long-form battery
   (`scripts/audit-korean.py` before this repo's copy was trimmed:
   `max_tokens` 2000 for the 8 essay-length prompts, 1800 for the 5-turn
   conversation). Host memory climbed steadily over about 3 minutes of
   sustained generation until the watchdog's floor tripped mid-response.
2. **Second stop**, about 20 minutes later, during a 12-case
   `telemem:run` (veneta-bench core set) against the same server: cases 1–4
   completed (M1, M2 abilities), then the watchdog fired again and the
   remaining 8 cases (M3–M6) failed with connection errors once the
   container exited. Memory had been climbing from idle shortly after boot
   in a separate attempt as well (observed once with no requests in flight),
   so this looks like a genuine, sustained memory-growth pattern on this
   checkpoint at this `HOST_RESERVE_GIB`/`MAX_MODEL_LEN` combination, not
   something tied only to long completions.

**What actually got measured cleanly on this host:** the two `measure.py`
arms (400 max tokens, single-turn, 60 generations each) and a 4-prompt,
200-max-token Korean quality spot-check fired immediately on a fresh boot —
all completed without tripping the watchdog. The pattern that survives both
incidents: short, single-turn generations stayed well inside the memory
budget; sustained longer sessions (long completions, or many sequential
cases through a tool-calling loop) did not.

**Not yet resolved:** whether this is specific to the PLE-offload worker's
own memory growth, to KV-cache fragmentation under `FULL_DECODE_ONLY` CUDA
graphs, or just this host's tight budget at `MAX_MODEL_LEN=16384` with no
slack — needs the two-GB10 cluster setup (flagged by the oss room,
2026-10-07) or a lower `MAX_MODEL_LEN`/`HOST_RESERVE_GIB` combination to
isolate. Filed as a follow-up, not blocking the speed/acceptance result this
repo reports, which came from the short-generation runs above.

**veneta-bench 12-case quality gate: not complete.** 4 of 12 cases ran
cleanly before the second stop (`data/eval/mtp-ko-check/` in the
worldmodel-core checkout, not this repo); the other 8 did not run. This gate
is not yet satisfied for the ko 65k arm — see `results/README.md`'s
"actually measured" note, which says this plainly rather than implying it
passed.
