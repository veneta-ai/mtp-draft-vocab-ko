#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Quality gate for a Korean draft-vocabulary file served via MTP_DRAFT_VOCAB
on a vLLM OpenAI-compatible endpoint (point --port / PORT at it; the vocab
file itself is a server-side launch setting, not an argument here).

Same shape as the MiaAI-Lab Single-DGX-Spark kit's audit-spanish.py — rejection
sampling means the *output distribution* cannot change when the draft
vocabulary changes (a trimmed drafter only proposes fewer tokens; the target
model verifies every one with the full vocabulary), so this gate exists to
catch an implementation bug, not a theoretical risk. It checks:
  - replacement characters (broken byte-fallback -> broken jamo composition)
  - unwanted script drift: Han ideographs or Kana where plain Korean prose
    is expected (the risk analogous to Spanish's Asturian drift — the model
    reaching for a neighboring script instead of the trimmed vocabulary's
    Korean coverage)
  - genuinely fluent Korean: common particles and sentence-final endings
    present, per long paragraph, not just in the set
  - degradation across a multi-turn conversation
  - empty output from reasoning-budget exhaustion

Note (2026-10-07): the full battery below (max_tokens 2000/1800, 8 long-form
prompts + a 5-turn conversation) tripped this host's memory watchdog twice at
16k context — see results/runs/2026-10-07-watchdog-note.md in this repo. The
numbers actually reported for the ko 65k arm used the reduced mt=600/500
below, run against a freshly booted server, immediately on health (no idle
gap) to avoid the boot-time memory ramp the note describes.
"""
import os
import json, re, sys, urllib.request
import functools
print = functools.partial(print, flush=True)

PORT = os.environ.get("PORT", "8889")
URL = f"http://127.0.0.1:{PORT}/v1/chat/completions"
MODEL = os.environ.get("SERVED_MODEL_NAME", "qwen3.8-flash-next")
API_KEY = os.environ.get("API_KEY", "")
HEADERS = {"Content-Type": "application/json"}
if API_KEY:
    HEADERS["Authorization"] = f"Bearer {API_KEY}"

# Thinking OFF sampling per the model card (mixing modes causes language mixing).
THINKING = False
SAMPLING = {"temperature": 0.7, "top_p": 0.80, "top_k": 20, "presence_penalty": 1.5}

def chat(messages, mt=600, temp=None):
    body = {"model": MODEL, "messages": messages, "max_tokens": mt,
            "chat_template_kwargs": {"enable_thinking": THINKING}, **SAMPLING}
    if temp is not None: body["temperature"] = temp
    req = urllib.request.Request(URL, json.dumps(body).encode(), HEADERS)
    d = json.loads(urllib.request.urlopen(req, timeout=900).read())
    m = d["choices"][0]["message"]; u = d["usage"]
    return ((m.get("content") or "").strip(), u["completion_tokens"],
            (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0))

# --- script / fluency detection --------------------------------------------
HANGUL = re.compile(r"[가-힣]")          # 가-힣 (composed syllables)
HAN = re.compile(r"[一-鿿]")             # Chinese ideographs (Hanja)
KANA = re.compile(r"[぀-ヿ]")            # hiragana/katakana
JAMO_LONE = re.compile(r"[ㄱ-ㅎㅏ-ㅣ]")  # uncomposed jamo = broken rendering

PARTICLES = ["은", "는", "이", "가", "을", "를", "에", "의", "도", "로", "과", "와"]
ENDINGS = [r"습니다", r"해요", r"했다", r"한다", r"됩니다", r"입니다", r"예요", r"죠"]

def analiza(txt):
    """Returns (replacement_chars, broken_jamo, han_ratio, kana_hits, suspect_paragraphs)."""
    roto = txt.count("�")
    broken_jamo = len(JAMO_LONE.findall(txt))
    hangul_n = len(HANGUL.findall(txt))
    han_n = len(HAN.findall(txt))
    kana_n = len(KANA.findall(txt))
    han_ratio = han_n / hangul_n if hangul_n else (1.0 if han_n else 0.0)

    sosp = []
    def is_prose(p):
        ls = [l for l in p.strip().split("\n") if l.strip()]
        marks = sum(1 for l in ls if l.lstrip().startswith(("-", "*", "|", "#", "1.", "2.", "3.")))
        return len(ls) > 0 and marks / len(ls) < 0.4
    for i, par in enumerate(p for p in txt.split("\n\n") if len(p.strip()) > 80 and is_prose(p)):
        particles = sum(1 for w in PARTICLES if w in par)
        endings = sum(1 for rx in ENDINGS if re.search(rx, par))
        if particles < 3 and endings < 1:
            sosp.append((i, particles, endings, par[:110]))
    return roto, broken_jamo, han_ratio, kana_n, sosp

# --- battery -----------------------------------------------------------------
LARGOS = [
 ("essay-history",  "한국 반도체 산업의 역사를 1980년대부터 지금까지, 구체적인 회사 이름과 연도를 포함해 천 단어 이상으로 설명해 주세요."),
 ("essay-technical", "리눅스의 가상 메모리 관리가 어떻게 동작하는지 페이징, TLB, 페이지 폴트, 회수, 스왑을 포함해 아주 자세히 설명해 주세요. 필요한 만큼 길게 써도 됩니다."),
 ("narrative",       "출시 전날 밤 치명적인 결함을 발견한 엔지니어에 대한 800자 이상의 긴 이야기를 써 주세요. 문체와 분위기에 신경 써 주세요."),
 ("explanation",     "기술 배경이 없는 사람에게 비유를 들어 언어모델이 무엇이고 어떻게 학습되는지, 왜 때때로 틀리는지 길게 설명해 주세요."),
 ("formal-report",   "서버 인프라를 컨테이너로 이전하는 작업에 대한 정식 기술 보고서를 서론, 위험 분석, 단계별 계획, 결론의 형식으로 작성해 주세요."),
 ("hanja-stress",    "다음 한자어를 자연스럽게 녹여서 세 단락을 써 주세요: 경제, 정치, 사회, 문화, 과학, 기술, 환경, 교육."),
 ("code-ko",         "도서관 관리를 위한 완전한 파이썬 모듈을 작성해 주세요: 클래스, ISBN 검증, JSON 저장, 테스트 포함. 모든 주석과 문서는 한국어로."),
 ("json-ko",         "한국 도시 다섯 곳을 이름, 도, 인구, 두 문장짜리 한국어 설명과 함께 JSON으로만 반환해 주세요. JSON 밖에 다른 텍스트는 쓰지 마세요."),
]

MULTITURN = [
 "안녕하세요, 온라인 쇼핑몰을 위한 REST API를 설계하고 싶어요.",
 "JWT 인증을 추가하고 리프레시 토큰을 어떻게 관리할지 설명해 주세요.",
 "이제 그 API의 버전 관리와 예전 클라이언트의 마이그레이션을 어떻게 할지 설명해 주세요.",
 "마지막으로 엔드포인트 세 개의 문서를 한국어로, 예시를 포함해서 작성해 주세요.",
 "지금까지 이야기한 내용을 긴 문단 하나로 요약해 주세요.",
]

fallos = []
print(f"  {'test':<16} {'tok':>5} {'reason':>6} {'roto':>5} {'jamo':>5} {'han%':>5} {'kana':>5}  verdict")
print("  " + "-" * 78)

for nombre, p in LARGOS:
    try:
        txt, n, rz = chat([{"role": "user", "content": p}])
    except Exception as e:
        print(f"  {nombre:<16} ERROR {type(e).__name__}"); fallos.append(nombre); continue
    if not txt:
        print(f"  {nombre:<16} {n:>5} {rz:>6}  EMPTY"); fallos.append(nombre); continue
    roto, jamo, han_ratio, kana, sosp = analiza(txt)
    need_han = nombre == "hanja-stress"
    ok = roto == 0 and jamo == 0 and kana == 0 and not sosp and (han_ratio < 0.15 or need_han)
    if not ok: fallos.append(nombre)
    print(f"  {nombre:<16} {n:>5} {rz:>6} {roto:>5} {jamo:>5} {han_ratio*100:>4.1f}% {kana:>5}  {'OK' if ok else '*** REVIEW ***'}")
    if sosp:
        for i, part, end, frag in sosp[:2]:
            print(f"      paragraph {i}: particles={part} endings={end} :: {frag!r}")
    if roto or jamo:
        print(f"      *** {roto} replacement chars, {jamo} uncomposed jamo -- broken byte-fallback")

print()
print("  --- multi-turn conversation (drift usually shows up in later turns) ---")
msgs = []
for t, turno in enumerate(MULTITURN, 1):
    msgs.append({"role": "user", "content": turno})
    try:
        txt, n, rz = chat(msgs, mt=500)
    except Exception as e:
        print(f"  turn {t}: ERROR {type(e).__name__}"); fallos.append(f"turn{t}"); break
    msgs.append({"role": "assistant", "content": txt})
    if not txt:
        print(f"  turn {t}: {n:>5} tok, {rz} reasoning, EMPTY"); fallos.append(f"turn{t}"); continue
    roto, jamo, han_ratio, kana, sosp = analiza(txt)
    ok = roto == 0 and jamo == 0 and kana == 0 and not sosp
    if not ok: fallos.append(f"turn{t}")
    print(f"  turn {t:<2} {n:>5} tok  roto={roto} jamo={jamo} han%={han_ratio*100:.1f} kana={kana}  {'OK' if ok else '*** REVIEW ***'}")
    if sosp: print(f"      {sosp[0][3]!r}")

print()
print(f"  accumulated thread context: {sum(len(m['content']) for m in msgs):,} chars")
print()
if fallos:
    print(f"  *** {len(fallos)} to review: {', '.join(fallos)}"); sys.exit(1)
print("  === ALL TESTS PASS ===")
