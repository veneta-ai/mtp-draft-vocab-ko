# vocabulary files land here (one per tokenizer family)

Each file is one token id per line, ascending, nothing else — the MiaAI-Lab kit's `MTP_DRAFT_VOCAB` loader
(`files/patch_mtp_draft_vocab.py`) parses every line as `int(line)` with no comment support, so **no header line
goes inside the file**; its provenance is tracked here instead.

| file | tokenizer | corpus | licence | built | rows |
| --- | --- | --- | --- | --- | --- |
| `draft_vocab_ko_qwen3.8_en_code_65k.txt` | nvidia/Qwen3.8-Flash-Next-NVFP4 | Korean Wikipedia (668 MiB sample, kowiki-latest-pages-articles, 2026-10-01 dump) | CC BY-SA 4.0 | 2026-10-07 | 65,536 |
| `draft_vocab_exaone45_ko_65k.txt` | LGAI-EXAONE/EXAONE-4.5-33B | Korean Wikipedia (streamed `wikimedia/wikipedia` ko sample, 2026-10-07) | CC BY-SA 4.0 | 2026-10-07 | 65,536 |
| `draft_vocab_llama31_ko_65k.txt` | meta-llama/Llama-3.1-8B-Instruct (EAGLE-1 drafter: `yuhuili/EAGLE-LLaMA3.1-Instruct-8B`) | Korean Wikipedia (streamed `wikimedia/wikipedia` ko sample, 400 MiB, 2026-10-09) | CC BY-SA 4.0 | 2026-10-09 | 65,536 |

Built with `scripts/build_draft_vocab_ko.py` from a floor kept whole plus this corpus, byte-fallback ids pinned, the
rest by raw frequency (FR-Spec: Zhao et al., ACL 2025). No customer or private corpus is used in any file here.

**The two files' floors are not built the same way, and that matters.** Qwen3.8's floor is MiaAI-Lab's own shipped
47k en+code file (`files/draft_vocab_en_code_47k.txt`, kept whole — see NOTICE) — a curated set MiaAI chose for
general English-and-code coverage. No equivalent shipped floor exists for EXAONE's tokenizer, so
`draft_vocab_exaone45_ko_65k.txt` uses the lowest 30,000 token ids as a stand-in floor instead (99.667% corpus
coverage, 400 byte-fallback/special ids pinned, 35,536 added by frequency). A low-numbered id is often a common or
structural token in BPE/SentencePiece training, but that is a tendency, not a guarantee the way a curated floor is —
this file's English-and-code robustness outside Korean has not been checked, since the measurement protocol here is
Korean-prompts-only (`results/prompts/`). The Korean decode result itself (+7.0%, zero replacement characters, zero
script drift) is unaffected by this — the floor choice only bears on non-Korean behavior, which nothing in this
repository measures.

**`draft_vocab_llama31_ko_65k.txt` is a 2026-10-09 regeneration, not the file the original EAGLE-1 measurement used.**
That original file was built the same night as the others but was never committed here; it was lost along with a
scratchpad wipe during a reboot. It uses the same stand-in-floor method as the EXAONE file above (lowest 30,000 ids,
not a curated MiaAI floor — Llama 3.1 has no MiaAI DGX Spark kit at all): 402 byte-fallback/special ids pinned,
35,534 added by frequency over a fresh 400 MiB Korean Wikipedia stream, 99.982% corpus coverage. It is built the same
way as the lost file, not guaranteed to be byte-identical to it — the retracted EAGLE-1 README numbers were never
about this file anyway (they're withdrawn because the activation flag, not the vocabulary file, was the open
question — see the main README's retraction note).
