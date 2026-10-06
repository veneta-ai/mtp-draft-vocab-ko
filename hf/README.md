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

# mtp-draft-vocab-ko

Korean draft vocabularies for MTP speculative decoding, one file per tokenizer family, built from Korean Wikipedia and
measured before and after on the same machine. FR-Spec-style: the draft head's output projection is computed over a
frequency-ranked subset of the vocabulary; the target verifies over the full vocabulary, so outputs are exactly the same.

**Status:** files and numbers are added as they are measured. Nothing here is claimed before it is measured.

## Files

| file | family | rows | built from | measured |
| --- | --- | --- | --- | --- |
| (first file lands with stage 1) | | | | |

Every file: one token id per line, 65,536 rows — the family's shipped floor, all byte-fallback ids pinned, then ids by
Korean frequency. The first line is a header carrying the corpus, its licence and the build date.

## Use (vLLM, Qwen3.8-Flash-Next, MiaAI-Lab overlay)

```bash
MTP_DRAFT_VOCAB=draft_vocab_ko_qwen3.8_en_code_65k.txt
```

## Measurements

See the results table in the GitHub repository (protocol: same kit's en+code vocabulary as the baseline, same machine,
twenty fixed Korean prompts, temperature 0, three repeats, median; quality checked by byte-identical greedy outputs).

## Credit and licence

Method: FR-Spec (Zhao et al., ACL 2025) and MiaAI-Lab's DGX Spark kits for Qwen3.8-Flash-Next (the `MTP_DRAFT_VOCAB`
overlay, the 47k floor, byte-fallback pinning, the language-extension method). Frequency source: Korean Wikipedia,
CC BY-SA 4.0, attributed in every file header; the files contain token ids, not text. Everything here is Apache-2.0.
No customer or private corpus is used. Source and issues: https://github.com/veneta-ai/mtp-draft-vocab-ko
