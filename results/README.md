# Measurement protocol

Every number in this repository carries these conditions, in this order: machine · engine and version · checkpoint
and quantization · draft vocabulary file (or "shipped en+code") · speculative tokens k · prompts · sampling · repeats ·
what was measured.

**Baseline.** The same kit's shipped en+code vocabulary on the same machine — never a different engine, never a different
machine. MiaAI-Lab's six languages were measured this way (5 prompts × 2 repeats, temp 0, thinking off, median), so the
Korean numbers are comparable to theirs.

**Prompts.** `prompts/ko-general-10.jsonl` (everyday Korean: explanation, summary, email, list, translation…) and
`prompts/ko-domain-10.jsonl` (telecom operations, retail, finance — public wording only, no customer text). Output
200–512 tokens, temperature 0, thinking off, 3 repeats, median.

**Measured.** decode tokens/s, draft acceptance rate when the engine exposes it, time to first token (should not move).

**Quality.** Rejection sampling makes the output distribution identical, so quality must not change; the check is
veneta-bench's 12 memory-ability cases run with and without the file (same 12/12 expected) plus a byte-identical diff of the
greedy outputs on the 20 prompts.

**Quality, as actually measured (2026-10-07).** A literal byte-identical diff of greedy outputs between arms was not
meaningful on this engine: at temp 0, repeat token counts on the same prompt varied slightly run-to-run even within
one arm (e.g. ko-gen-01: 143/132/125 tokens across 3 repeats, shipped-vocab arm) — continuous batching changes the
floating-point reduction order per batch, a known vLLM determinism caveat (the kit ships `patch_determinism.py` for
part of this, not all of it). What was run instead:

- Zero replacement characters across all 120 generations in both arms (`measure.py`'s own counter).
- A dedicated Korean-script fidelity check against the ko 65k arm: `scripts/audit-korean.py` in this repo (a trimmed,
  self-contained copy of the MiaAI-Lab kit's `bench/audit-korean.py`), 4 short prompts at `max_tokens=200` after the
  full 8-prompt/5-turn battery tripped this host's memory watchdog twice — see
  `results/runs/2026-10-07-watchdog-note.md` for both incidents. Result: zero replacement chars, zero uncomposed
  jamo, zero stray Han/Kana characters, all Hangul.
- **veneta-bench's 12-case quality gate: 12/12 passed against the ko 65k arm** (`telemem:run` in the worldmodel-core
  checkout; graded with `telemem:score`). Run in two parts after the watchdog incidents above: 4 of 12
  (`results/runs/2026-10-07-veneta-bench-ko65k-part1.json`, abilities M1–M2) on the first attempt, the remaining 8
  (`...-part2.json`, M3–M6) on a later attempt once host memory genuinely freed up (confirmed with the oss room
  before retrying — `nvidia-smi -L` still showed one GPU, this was contention easing, not a second machine). Same
  question set the paper's core twelve use; this run used the memory-on arm only (the vocab swap is the variable
  under test, not the memory-vs-no-memory axis).

**Table format.**

| family · checkpoint | machine | engine | vocab | k | decode tok/s (shipped → ko) | acceptance | prompts | date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nvidia/Qwen3.8-Flash-Next-NVFP4 | DGX Spark (GB10) | vLLM (MiaAI-Lab Single-DGX-Spark kit) | shipped 47k → ko 65k | 3 | 16.9 → 26.1 (+54%) | 1.33 → 2.16 accepted/draft | 20 (ko-general-10 + ko-domain-10), 3 repeats, 400 max tokens | 2026-10-07 |

Raw run files go next to the table as `runs/<date>-<family>-<vocab>.jsonl`.
