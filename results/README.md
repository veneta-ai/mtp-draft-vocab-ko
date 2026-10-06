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

**Table format.**

| family · checkpoint | machine | engine | vocab | k | decode tok/s (shipped → ko) | acceptance | prompts | date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (first row lands with stage 1) | | | | | | | | |

Raw run files go next to the table as `runs/<date>-<family>-<vocab>.jsonl`.
