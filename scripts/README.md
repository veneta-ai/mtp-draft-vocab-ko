# scripts

Standalone, so the method survives any kit's deprecation.

- `build_draft_vocab_ko.py` (landed 2026-10-07): input = tokenizer id or path, the family's shipped floor file,
  a Korean corpus (a Korean Wikipedia text sample by default; a private corpus path for a domain file that is NOT
  published); output = `files/draft_vocab_ko_<family>_65k.txt`, bare token ids only. Rules: keep every floor id, pin
  all byte-fallback ids, then add ids by frequency to 65,536 rows. **Correction to the original plan here:** the
  provenance (corpus, licence, build date) does **not** go in a header line inside the file — the MiaAI-Lab kit's
  `MTP_DRAFT_VOCAB` loader parses every line as a bare `int(line)` with no comment support, so a header would crash
  serving. Provenance goes in `files/README.md`'s table instead; the script prints the row to add.
- `audit-korean.py` (landed 2026-10-07): a Korean-language quality gate (replacement characters, broken jamo, Han/Kana
  script drift, particle/ending fluency, multi-turn drift) against a served endpoint — the MiaAI-Lab kit's
  `bench/audit-spanish.py` pattern, adapted. Keep `max_tokens` modest (600/500, not 2000/1800): the full long-form
  battery tripped this measurement's host memory watchdog twice — see `results/runs/2026-10-07-watchdog-note.md`.
- `measure.py` (landed 2026-10-07): runs the protocol in `results/README.md` against a vLLM endpoint and writes the
  run file and the table row.

Every script carries the Apache-2.0 header.
