#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Builds a language-extended MTP draft vocabulary from a frequency corpus.

Standalone — no path into any serving kit. Point --base at your kit's shipped
floor file (e.g. files/draft_vocab_en_code_47k.txt from the MiaAI-Lab
Single-DGX-Spark kit) and --corpus at a frequency source; this script does
not fetch or bundle either.

Method (FR-Spec: Zhao et al., ACL 2025 — https://aclanthology.org/2025.acl-long.198.pdf;
the extension recipe this follows is MiaAI-Lab's, credited in NOTICE):
  1. The floor file enters WHOLE. An id that already works in the shipped
     vocabulary is never dropped for a frequency-ranked one.
  2. Every byte-fallback id (< --byte-fallback-max) is pinned unconditionally,
     before any frequency ranking — BPE needs the full byte range to compose
     accented and non-Latin characters it has no multi-byte token for.
  3. Remaining slots, up to --size, are filled by raw frequency over the
     corpus. A dictionary is never used here: in a frequency list every
     inflected form earns its own rank, where a dictionary would weight a
     rare dictionary headword the same as a common one.

Usage:
    python3 build_draft_vocab_ko.py \
        --base /path/to/kit/files/draft_vocab_en_code_47k.txt \
        --corpus kowiki_corpus_668mib.txt \
        --model nvidia/Qwen3.8-Flash-Next-NVFP4 \
        --corpus-name "Korean Wikipedia (668 MiB sample)" \
        --corpus-licence "CC BY-SA 4.0" \
        --out files/draft_vocab_ko_qwen3.8_en_code_65k.txt

Writes one token id per line, ascending, nothing else — the MiaAI-Lab kit's
own MTP_DRAFT_VOCAB loader (files/patch_mtp_draft_vocab.py) parses the file
as a bare `int(line)` per line with no comment support, so a header line
inside it would crash serving. The provenance (corpus, licence, build date)
this would otherwise carry is printed to stdout and must go in
files/README.md's table instead — see that file.
"""
import argparse
import datetime
import json
import pathlib
import sys
from collections import Counter

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--base", required=True, help="the shipped floor vocabulary (ids, one per line) — kept whole")
ap.add_argument("--corpus", nargs="+", required=True, help="text file(s); suffix :N repeats a file N times")
ap.add_argument("--size", type=int, default=65536)
ap.add_argument("--model", required=True, help="tokenizer id or local path")
ap.add_argument("--byte-fallback-max", type=int, default=400, help="every id below this is pinned unconditionally")
ap.add_argument("--corpus-name", required=True, help="for the output header, e.g. 'Korean Wikipedia (668 MiB sample)'")
ap.add_argument("--corpus-licence", required=True, help="for the output header, e.g. 'CC BY-SA 4.0'")
ap.add_argument("--out", required=True)
a = ap.parse_args()

from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained(a.model, trust_remote_code=True)

base = {int(line) for line in pathlib.Path(a.base).read_text().splitlines() if line.strip() and not line.startswith("#")}
print(f"  floor (shipped): {len(base):,} ids")

counts = Counter()
CHUNK = 1 << 20
for spec in a.corpus:
    if ":" in spec and spec.rsplit(":", 1)[1].isdigit():
        path_str, repeat = spec.rsplit(":", 1)
        repeat = int(repeat)
    else:
        path_str, repeat = spec, 1
    p = pathlib.Path(path_str)
    for _ in range(repeat):
        if p.suffix == ".jsonl":
            for line in p.open(encoding="utf-8"):
                text = json.loads(line).get("text", "")
                if text:
                    counts.update(tok(text, add_special_tokens=False)["input_ids"])
        else:
            with p.open(encoding="utf-8") as f:
                while True:
                    chunk = f.read(CHUNK)
                    if not chunk:
                        break
                    counts.update(tok(chunk, add_special_tokens=False)["input_ids"])
    print(f"  {p.name} x{repeat}: {sum(counts.values()):,} occurrences so far, {len(counts):,} distinct ids")

pinned = {i for i in range(a.byte_fallback_max)} | set(tok.all_special_ids or [])
print(f"  pinned unconditionally (byte-fallback + special): {len(pinned):,}")

vocab = set(base) | pinned
if len(vocab) > a.size:
    sys.exit(f"  floor + pinned ({len(vocab):,}) already exceeds --size {a.size:,}")

room = a.size - len(vocab)
added = [i for i, _ in counts.most_common() if i not in vocab][:room]
vocab |= set(added)
print(f"  added by frequency: {len(added):,} -> total {len(vocab):,}")

total_occ = sum(counts.values())
covered = sum(c for i, c in counts.items() if i in vocab)
print(f"  coverage over the corpus: {covered / total_occ * 100:.3f}%" if total_occ else "  coverage: n/a (no corpus occurrences)")

out = pathlib.Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(str(i) for i in sorted(vocab)) + "\n")
print(f"  wrote {len(vocab):,} bare ids -> {out} (no header — the kit's loader parses every line as int(line))")
print(f"  add this row to files/README.md's table: | {out.name} | {a.model} | {a.corpus_name} | {a.corpus_licence} | {datetime.date.today().isoformat()} | {len(vocab)} |")
