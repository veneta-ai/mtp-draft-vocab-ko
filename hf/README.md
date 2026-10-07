---
license: apache-2.0
language:
  - ko
tags:
  - speculative-decoding
  - mtp
  - draft-vocabulary
  - fr-spec
  - vllm
  - korean
pretty_name: Korean draft vocabularies for MTP speculative decoding
---

![mtp-draft-vocab-ko](assets/banner.svg)

# mtp-draft-vocab-ko

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-5b4fb5)](https://github.com/veneta-ai/mtp-draft-vocab-ko/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-veneta--ai%2Fmtp--draft--vocab--ko-181717)](https://github.com/veneta-ai/mtp-draft-vocab-ko)
[![Method: FR-Spec](https://img.shields.io/badge/method-FR--Spec%20(ACL%202025)-2fd58a)](https://aclanthology.org/2025.acl-long.198.pdf)

Korean draft vocabularies for MTP speculative decoding, one file per tokenizer family, built from Korean Wikipedia and
measured before and after on the same machine. FR-Spec-style: the draft head's output projection is computed over a
frequency-ranked subset of the vocabulary; the target verifies over the full vocabulary, so outputs are exactly the same.

![Qwen3.8-Flash-Next decode speed, shipped vocabulary vs. +ko 65k: 16.9 to 26.1 tokens per second, +54%](assets/speedup-qwen3.8.svg)

**Status (2026-10-07):** first file measured and verified — Qwen3.8. Other families below are not yet measured; nothing is
claimed before it is.

## Files

| file | family | rows | built from | measured |
| --- | --- | --- | --- | --- |
| `draft_vocab_ko_qwen3.8_en_code_65k.txt` | Qwen3.8 (nvidia/Qwen3.8-Flash-Next-NVFP4) | 65,536 | Korean Wikipedia (668 MiB sample, kowiki-latest-pages-articles, 2026-10-01 dump), CC BY-SA 4.0 | 2026-10-07: decode 16.9 → 26.1 tok/s (+54%), acceptance 1.33 → 2.16, zero replacement chars, zero Korean-script drift, veneta-bench 12/12 unaffected |

Every file: one token id per line, ascending, nothing else — the family's shipped floor kept whole, every byte-fallback id
pinned, the rest filled by Korean frequency. No header line: the serving kit's loader parses each line as a bare integer
with no comment support, so provenance (corpus, licence, build date) is tracked in the table above instead.

## Use (vLLM, Qwen3.8-Flash-Next, MiaAI-Lab overlay)

```bash
MTP_DRAFT_VOCAB=draft_vocab_ko_qwen3.8_en_code_65k.txt
```

## Measurements

See the full results table and raw run files in the GitHub repository (protocol: same kit's en+code vocabulary as the
baseline, same machine, twenty fixed Korean prompts, temperature 0, three repeats, median). Quality gate: zero
replacement characters across every generation in both arms, a dedicated Korean-script fidelity check, and veneta-bench's
12 memory-ability cases run against the draft-vocab arm (12/12). A literal byte-identical diff of greedy outputs was
tried and dropped as not meaningful on this engine — vLLM's continuous batching changes the floating-point reduction
order per batch, so even repeat runs within one arm vary slightly in token count; see results/README.md for the exact
example that showed this.

## Credit and licence

Method: FR-Spec (Zhao et al., ACL 2025) and MiaAI-Lab's DGX Spark kits for Qwen3.8-Flash-Next (the `MTP_DRAFT_VOCAB`
overlay, the 47k floor, byte-fallback pinning, the language-extension method). Frequency source: Korean Wikipedia,
CC BY-SA 4.0, attributed in every file header; the files contain token ids, not text. Everything here is Apache-2.0.
No customer or private corpus is used. Source and issues: https://github.com/veneta-ai/mtp-draft-vocab-ko
