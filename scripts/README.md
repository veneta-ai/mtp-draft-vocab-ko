# scripts

Standalone, so the method survives any kit's deprecation.

- `build_draft_vocab_ko.py` (to land with stage 1): input = tokenizer id or path, the family's shipped floor file,
  a Korean corpus (the Korean Wikipedia dump by default; a private corpus path for a domain file that is NOT published);
  output = `files/draft_vocab_ko_<family>_65k.txt` with a header line carrying the corpus, its licence and the build date.
  Rules: keep every floor id, pin all byte-fallback ids, then add ids by frequency to 65,536 rows.
- `measure.py` (to land with stage 1): runs the protocol in `results/README.md` against a vLLM endpoint and writes the
  run file and the table row.

Every script carries the Apache-2.0 header.
