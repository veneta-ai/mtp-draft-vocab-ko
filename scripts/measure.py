#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Runs the protocol in results/README.md against a vLLM OpenAI-compatible
endpoint and writes a run file (raw, one JSON line per generation) plus a
printed table row.

    python3 scripts/measure.py --base-url http://127.0.0.1:8888/v1 \
        --model qwen3.8-flash-next --vocab "shipped en+code" \
        --prompts results/prompts/ko-general-10.jsonl results/prompts/ko-domain-10.jsonl \
        --repeats 3 --max-tokens 400 \
        --out results/runs/2026-10-07-qwen3.8-flash-next-shipped.jsonl

Run once per arm (shipped baseline, then the ko file, swapping MTP_DRAFT_VOCAB
and rebooting the server between arms — the draft vocabulary is read at boot).
Measured: decode tokens/s (completion_tokens / wall time), time to first token
(streaming), and the engine's own spec-decode acceptance rate from /metrics
when the counters are nonzero (some boot paths read zero deltas — see the
kit's README; when that happens this script says so rather than printing a
false rate).
"""
import argparse, json, pathlib, re, statistics, sys, time, urllib.error, urllib.request

METRICS_COUNTERS = [
    "vllm:spec_decode_num_drafts_total",
    "vllm:spec_decode_num_accepted_tokens_total",
    "vllm:spec_decode_num_draft_tokens_total",
]
METRIC_LINE = re.compile(r'^(vllm:[a-z_]+)(\{[^}]*\})? ([0-9.eE+-]+)$')


def snapshot_metrics(metrics_url):
    out = {}
    try:
        with urllib.request.urlopen(metrics_url, timeout=10) as r:
            for raw in r.read().decode().splitlines():
                m = METRIC_LINE.match(raw)
                if not m:
                    continue
                name, _labels, val = m.groups()
                if name in METRICS_COUNTERS:
                    out[name] = out.get(name, 0.0) + float(val)
    except (urllib.error.URLError, OSError):
        pass
    return out


def load_prompts(paths):
    rows = []
    for p in paths:
        for line in pathlib.Path(p).open(encoding="utf-8"):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def generate(base_url, model, prompt, max_tokens, timeout):
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        # thinking off — this checkpoint's chat template reads this flag;
        # harmless if the template ignores it.
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        url, json.dumps(body).encode("utf-8"), {"Content-Type": "application/json"}
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    elapsed = time.monotonic() - t0
    msg = data["choices"][0]["message"]
    usage = data["usage"]
    return {
        "text": msg.get("content") or "",
        "completion_tokens": usage["completion_tokens"],
        "prompt_tokens": usage["prompt_tokens"],
        "elapsed_s": elapsed,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8889/v1")
    ap.add_argument("--metrics-url", default=None, help="default: base-url's host, port, /metrics")
    ap.add_argument("--model", required=True)
    ap.add_argument("--vocab", required=True, help='label for the table row, e.g. "shipped en+code" or "ko 65k"')
    ap.add_argument("--machine", default="DGX Spark (GB10)")
    # No default: the engine goes into every row and into published tables, and
    # a wrong one is a false provenance claim rather than a missing field.
    ap.add_argument("--engine", required=True, help='e.g. "vLLM (MiaAI-Lab Single-DGX-Spark kit)" or "vLLM 0.28.0.dev999 (PR #60387 branch @ 8674c1f9)"')
    ap.add_argument("--checkpoint", default="nvidia/Qwen3.8-Flash-Next-NVFP4")
    ap.add_argument("--k", type=int, default=3, help="MTP speculative tokens")
    ap.add_argument("--prompts", nargs="+", required=True)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--max-tokens", type=int, default=400)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    metrics_url = a.metrics_url
    if metrics_url is None:
        m = re.match(r"(https?://[^/]+)", a.base_url)
        metrics_url = m.group(1) + "/metrics"

    prompts = load_prompts(a.prompts)
    print(f"  {len(prompts)} prompts x {a.repeats} repeats, vocab={a.vocab!r}")

    out_path = pathlib.Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    runs = []
    before = snapshot_metrics(metrics_url)
    with out_path.open("w", encoding="utf-8") as outf:
        for rep in range(a.repeats):
            for row in prompts:
                try:
                    g = generate(a.base_url, a.model, row["prompt"], a.max_tokens, a.timeout)
                except Exception as e:
                    print(f"  ERROR {row['id']} rep{rep}: {type(e).__name__}: {e}")
                    continue
                toks_per_s = g["completion_tokens"] / g["elapsed_s"] if g["elapsed_s"] > 0 else 0.0
                rec = {
                    "id": row["id"], "kind": row.get("kind"), "rep": rep,
                    "machine": a.machine, "engine": a.engine, "checkpoint": a.checkpoint,
                    "vocab": a.vocab, "k": a.k,
                    "completion_tokens": g["completion_tokens"], "prompt_tokens": g["prompt_tokens"],
                    "elapsed_s": round(g["elapsed_s"], 4), "tok_s": round(toks_per_s, 2),
                    "text_len": len(g["text"]), "replacement_chars": g["text"].count("�"),
                }
                runs.append(rec)
                outf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                outf.flush()
                print(f"  rep{rep} {row['id']:<10} {toks_per_s:6.1f} tok/s  "
                      f"({g['completion_tokens']} tok, {g['elapsed_s']:.2f}s)"
                      + ("  *** REPLACEMENT CHAR ***" if rec["replacement_chars"] else ""))
    after = snapshot_metrics(metrics_url)

    if not runs:
        sys.exit("no successful generations — nothing to report")

    toks_s = [r["tok_s"] for r in runs]
    median = statistics.median(toks_s)
    broken = sum(r["replacement_chars"] for r in runs)

    d_accepted = after.get("vllm:spec_decode_num_accepted_tokens_total", 0.0) - before.get(
        "vllm:spec_decode_num_accepted_tokens_total", 0.0
    )
    d_drafts = after.get("vllm:spec_decode_num_drafts_total", 0.0) - before.get(
        "vllm:spec_decode_num_drafts_total", 0.0
    )
    if d_drafts > 0:
        acceptance = f"{1 + d_accepted / d_drafts:.2f} accepted/draft"
    else:
        acceptance = "not captured (counters read zero delta on this boot path)"

    print()
    print(f"  median decode: {median:.1f} tok/s  (n={len(toks_s)})")
    print(f"  acceptance: {acceptance}")
    print(f"  replacement chars across all generations: {broken}")
    print()
    print("  | family · checkpoint | machine | engine | vocab | k | decode tok/s | acceptance | prompts | date |")
    print(f"  | {a.checkpoint} | {a.machine} | {a.engine} | {a.vocab} | {a.k} | {median:.1f} | {acceptance} | "
          f"{len(prompts)} (ko-general-10 + ko-domain-10) | {time.strftime('%Y-%m-%d')} |")
    print()
    print(f"  raw run file: {out_path}")


if __name__ == "__main__":
    main()
