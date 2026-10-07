# vocabulary files land here (one per tokenizer family)

Each file is one token id per line, ascending, nothing else — the MiaAI-Lab kit's `MTP_DRAFT_VOCAB` loader
(`files/patch_mtp_draft_vocab.py`) parses every line as `int(line)` with no comment support, so **no header line
goes inside the file**; its provenance is tracked here instead.

| file | tokenizer | corpus | licence | built | rows |
| --- | --- | --- | --- | --- | --- |
| `draft_vocab_ko_qwen3.8_en_code_65k.txt` | nvidia/Qwen3.8-Flash-Next-NVFP4 | Korean Wikipedia (668 MiB sample, kowiki-latest-pages-articles, 2026-10-01 dump) | CC BY-SA 4.0 | 2026-10-07 | 65,536 |

Built with `scripts/build_draft_vocab_ko.py` from the shipped 47k en+code floor (MiaAI-Lab's
`files/draft_vocab_en_code_47k.txt`, kept whole — see NOTICE) plus this corpus, byte-fallback ids pinned, the rest
by raw frequency (FR-Spec: Zhao et al., ACL 2025). No customer or private corpus is used in any file here.
