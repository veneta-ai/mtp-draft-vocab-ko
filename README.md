<p align="center"><img src="assets/banner.svg" alt="mtp-draft-vocab-ko" width="720"></p>

# mtp-draft-vocab-ko

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-5b4fb5)](LICENSE)
[![Hugging Face dataset](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-veneta--ai%2Fmtp--draft--vocab--ko-ffcc4d)](https://huggingface.co/datasets/veneta-ai/mtp-draft-vocab-ko)
[![Method: FR-Spec](https://img.shields.io/badge/method-FR--Spec%20(ACL%202025)-2fd58a)](https://aclanthology.org/2025.acl-long.198.pdf)

MTP 추측 디코딩용 한국어 드래프트 어휘사전입니다. 토크나이저 가족마다 파일 하나를 한국어 위키백과로 만들고, 같은 장비에서 적용 전후를 재서 올립니다. 영어 사용자가 체감하는 LLM 답변 속도를 한국어 사용자도 누릴 수 있게 만드는 목적으로 만들었습니다.

**상태: 첫 결과 (2026-10-07).** Qwen3.8(nvidia/Qwen3.8-Flash-Next-NVFP4): 디코딩 16.9 → 26.1 tok/s(+54%), 드래프트당 수락 토큰 1.33 → 2.16, 대체 문자(U+FFFD) 0개, 한국어 스크립트 오염 0개, veneta-bench 12개 기억 능력 문항 영향 없음(12/12). 조건과 원시 실행 파일은 results/README.md에 있습니다. 아래 다른 LLM들은 아직 측정 전이며, 그 전까지 없는 내용을 주장하지 않습니다.

<p align="center"><img src="assets/speedup-qwen3.8.svg" alt="Qwen3.8-Flash-Next 디코딩 속도, 기본 어휘 대 +한국어 65k: 초당 16.9에서 26.1 토큰, +54%" width="560"></p>

## 왜 만들나요?

MTP 헤드가 토큰 몇 개를 미리 제안하고 본 모델이 검증하는 것이 추측 디코딩입니다. FR-Spec 방식은 드래프트 헤드의 출력 투영을 빈도 상위 어휘 부분집합으로만 계산합니다. 검증은 전체 어휘로 하므로 출력은 정확히 같고 드래프트만 싸집니다. 지금 배포되는 부분집합은 영어와 코드 기준이라 한국어 토큰이 빠지고, 한국어 드래프트는 거절되어 속도가 느려집니다. MiaAI-Lab의 언어 확장 파일이 중·일·독·포·불·러·스페인어에 속도를 향상시켰고(DGX Spark 1대에서 디코드 +10~77 %), 한국어 파일은 없습니다. 이 저장소가 토크나이저 가족별로 그것을 더하고, 빌드 스크립트와 측정값을 함께 둡니다.

## 사용 (vLLM, Qwen3.8-Flash-Next, MiaAI 오버레이)

```bash
MTP_DRAFT_VOCAB=files/draft_vocab_ko_qwen3.8_en_code_65k.txt   # 비우면 기본 en+code
```

## 어떤 모델에 적용되는가

**지금 바로 쓸 수 있는 건 Qwen3.8-Flash-Next(nvidia/Qwen3.8-Flash-Next-NVFP4) 하나뿐입니다.** 나머지는 전부 같은 범용 vLLM 패치 하나를 직접 만들고 있는 중이니 기다려 주세요. 아래는 왜 그런지에 대한 전체 설명입니다 — 2026-10-07 재구성: 처음에는 "자체 MTP 헤드가 있으면 파일만 있으면 된다"와 "별도 드래프터는 엔진 패치가 필요하다"를 서로 다른 두 부류로 나눴는데, 틀렸습니다. 실제로는 거의 전부가 같은 부류입니다.

Qwen3.8-Flash-Next의 +54%는 범용 vLLM 기능이 아니라, nvidia/Qwen3.8-Flash-Next-NVFP4 체크포인트 전용으로 엔비디아가 배포한 모델 파일(mtp.py)에 MiaAI-Lab의 패치가 get_top_tokens()라는 메서드를 추가해서 나온 결과입니다. 이 메서드가 하는 일: lm_head 가중치에서 남길 어휘의 행만 골라(index_select) 새 버퍼로 모으고, 그 작은 행렬로만 곱하고(그래서 행렬곱 자체가 작아짐), 결과를 원래 어휘 id로 다시 매핑합니다. 이게 진짜로 속도가 빨라지는 이유입니다.

GLM 5.3 Flash·DeepSeek V4.1 Flash·Qwen3-Next의 vLLM 모델 파일을 코드로 읽어보니(2026-10-07), 셋 다 평범한 MTP 헤드가 있지만, get_top_tokens()가 없는 상태의 표준 vLLM MTPSpeculator로 처리됩니다. 그리고 MTPSpeculator는 EagleSpeculator와 클래스 구조가 사실상 같습니다 — 둘 다 DraftModelSpeculator를 상속하고, use_local_argmax_reduction은 모델에 get_top_tokens()가 없으면 아예 에러를 냅니다. 즉 이 모델들을 그냥 vLLM에 올리면, EAGLE 방식 별도 드래프터와 똑같이 "파일만으로는 안 되고, get_top_tokens()를 추가하는 엔진 패치가 있어야" 합니다. 이 체크포인트들의 실제 architectures 필드가 이 추론과 맞는지는 아직 확인 중입니다 — 추론이지 확정된 사실이 아닙니다.

본 모델과 별도의 더 작은 EAGLE 방식 드래프터 모델을 함께 쓰는 구조(예: EAGLE-3을 쓰는 Llama 3.3 70B)에도 같은 패치가 필요합니다. 처음에는 로짓 마스킹(전체 어휘로 계산한 뒤 일부만 고르는 방식)으로 범용 패치를 만들어 EAGLE-1(Llama 3.1 8B, 한국어 프롬프트 10개, 2026-10-07)로 실측했는데, **정확성은 지켰지만 속도는 빨라지지 않았습니다**(수락률 1.55로 두 arm이 동일, 대체 문자 0개로 출력은 그대로였지만, 디코딩은 15.83 → 15.57 tok/s로 오히려 잡음 수준만큼 느려짐). 로짓 마스킹은 행렬곱을 다 계산한 뒤에 고르는 방식이라 연산량이 전혀 줄지 않기 때문입니다. 올바른 훅 지점은 get_top_tokens() 자체였습니다 — Qwen3.8에서 이미 검증된 바로 그 메서드를, EAGLE과 MTP 헤드 모델 양쪽에 똑같이 추가하는 패치 하나로 다시 만들고 있습니다. 드래프터가 타깃과 lm_head 가중치를 공유하는 경우(EAGLE에서 흔함)는 공유 텐서를 직접 잘라내지 않고 항상 새 텐서로 gather해야 "타깃 검증 경로는 절대 안 건드린다"는 안전 원칙이 지켜집니다.

**어시스턴트 드래프터를 쓰는 Gemma 4는 이 패치로 되는 대상이 아닙니다 — 2026-10-07 정정.** 같은 범용 패치가 통할 거라 가정했는데, 실제로 걸어 보니 아니었습니다. vLLM은 Gemma 4에 전용 코드 경로(Gemma4Proposer)를 따로 두고 있고, Gemma 4의 compute_logits()는 이미 masked_embedding이라는 레이어를 거칩니다 — 체크포인트 자체가 자기만의 어휘 제한 메커니즘(centroid projection과 token_ordering 버퍼)을 학습 때부터 내장하고 있다는 뜻입니다. MTP 헤드의 드래프트 어휘처럼 런타임에 파일이나 엔진 패치로 바꿀 수 있는 게 아닙니다. 이 내장 메커니즘이 한국어를 이미 잘 다루는지, 아니면 이 저장소 전체가 고치려는 바로 그 영어 편향 문제를 똑같이 안고 있는지, 그리고 애초에 바꿀 수 있는 것인지는 완전히 별도의, 아직 답하지 않은 질문입니다 — 끝났다고 하지 않습니다. (이 구조는 veneta 자신의 통신 스택 구조라서 따로 추적하고 있습니다.)

한국어 다음은 아시아·아프리카·서구권의 다른 언어들도 같은 방식으로 만들 계획입니다. 아직 측정 전이라 위의 모든 숫자와 같은 규칙을 따릅니다 — 측정되기 전에는 주장하지 않습니다.

| 가족 | 구조 | 상태 |
| --- | --- | --- |
| Qwen3.8 (Qwen3.8-Flash-Next, nvidia 체크포인트) | 자체 MTP 헤드 + 엔비디아가 이미 패치한 get_top_tokens() | **측정 완료, 공개됨** |
| GLM 5.3 Flash · DeepSeek V4.1 Flash · Qwen3-Next · EXAONE 4.x(미확인) · Llama 3.3 70B + EAGLE-3(그 외 EAGLE 방식 스택) | 자체 MTP 헤드 또는 별도 드래프터, 둘 다 get_top_tokens()가 없는 표준 vLLM 경로 | 같은 패치 하나가 필요 — 로짓 마스킹으로 1차 실측(EAGLE-1): 정확하지만 속도 효과 없음; get_top_tokens() 포팅으로 다시 만드는 중 |
| Gemma 4 + 어시스턴트 드래프터 | 체크포인트에 내장된 자체 제한 방식(FR-Spec식이 아닌 centroid projection) | 이 패치의 대상이 아닌 별도 질문 — 조사 중 |

## 라이선스와 크레딧

이 저장소의 모든 것은 Apache-2.0(`LICENSE`, `NOTICE`). 빈도 출처인 한국어 위키백과는 CC BY-SA 4.0이며 모든 파일 머리에 표기합니다. 방법은 FR-Spec(ACL 2025)과 MiaAI-Lab의 DGX Spark 키트를 따릅니다. 공개 파일에 고객 문서나 비공개 코퍼스는 쓰지 않습니다.

---

# mtp-draft-vocab-ko (English)

Korean draft vocabularies for MTP speculative decoding — one file per tokenizer family, built from Korean Wikipedia,
measured before and after on the same machine, so a model that answers in Korean gets the speed-up its English users
already get.

**Status: first result in (2026-10-07).** Qwen3.8 (`nvidia/Qwen3.8-Flash-Next-NVFP4`): decode 16.9 → 26.1 tok/s (+54%), draft acceptance 1.33 → 2.16 accepted/draft, zero replacement characters, zero Korean-script drift, veneta-bench's 12 memory-ability cases unaffected (12/12). Conditions and raw run files in `results/README.md`. Other families below are not yet measured; nothing is claimed before it is.

## Why

Speculative decoding with an MTP head drafts several tokens and lets the target model verify them. FR-Spec-style
trimming computes the draft head's output projection only over a frequency-ranked subset of the vocabulary; the target
still verifies over the full vocabulary, so the output is exactly the same — only the draft gets cheaper. The subsets
shipped today are ranked on English and code. Korean tokens fall outside them, Korean drafts are rejected, and
decoding slows down for Korean answers. MiaAI-Lab's language-extended files improved decode speed for zh · ja · de · pt · fr · ru · es
(+10 % to +77 % decode on one DGX Spark). There is no Korean file. This repository adds it, per tokenizer family, with
the build script and the measurements.

## What is here

| path | what |
| --- | --- |
| `files/draft_vocab_ko_<family>_65k.txt` | the vocabulary: one token id per line, 65,536 rows — the family's shipped floor, all byte-fallback ids pinned, then ids by Korean frequency |
| `scripts/` | the standalone build script (input: a tokenizer, a Korean corpus, the floor file; output: the 65k file) and the measurement harness |
| `results/` | the measurement protocol and the before/after table, with every condition |

## How to use (vLLM, Qwen3.8-Flash-Next, MiaAI overlay)

```bash
MTP_DRAFT_VOCAB=files/draft_vocab_ko_qwen3.8_en_code_65k.txt   # empty = the shipped en+code default
```

Other engines and families are added as they are measured; see `results/README.md`.

## Which models this applies to

**Qwen3.8-Flash-Next (`nvidia/Qwen3.8-Flash-Next-NVFP4`) is the only model that works today.** Everything else is
waiting on the same one generic vLLM patch we're building. The rest of this section explains why — **reframed
2026-10-07**: we originally split this into two buckets, "built-in MTP head needs only a file" and "separate drafter
needs an engine patch". That split was wrong. Almost everything actually needs the same patch.

Qwen3.8-Flash-Next's +54% isn't a generic vLLM feature — it comes from a `get_top_tokens()` method MiaAI-Lab's patch
adds to NVIDIA's own vendored model file (`mtp.py`) for the `nvidia/Qwen3.8-Flash-Next-NVFP4` checkpoint specifically.
What it does: `index_select` the kept-vocabulary rows out of `lm_head`'s weight into a fresh buffer, run a smaller
matmul against only those rows, map the reduced argmax index back to the true vocabulary id. That's a genuinely
smaller GEMM, which is why it actually delivers a speedup.

Reading GLM 5.3 Flash's, DeepSeek V4.1 Flash's and Qwen3-Next's vLLM model files (2026-10-07) shows a plain MTP head
in each, but all three are dispatched through vLLM's stock `MTPSpeculator` with no `get_top_tokens()` defined — and
`MTPSpeculator` is structurally the same as `EagleSpeculator`, both inheriting `DraftModelSpeculator`;
`use_local_argmax_reduction` raises an error outright when the model has no `get_top_tokens()`. So on stock vLLM these
models need the same engine patch as an EAGLE-style separate drafter, not just a vocabulary file. Whether these
checkpoints' actual `architectures` fields really resolve to the files we read is still being confirmed — an
inference, not yet a fact we're publishing as settled.

A model that pairs a full-size target with a separate, smaller EAGLE-style drafter (e.g. Llama 3.3 70B with EAGLE-3)
needs that same patch too. We first built it as logit masking and measured it (EAGLE-1, Llama 3.1 8B, 10 Korean
prompts, 2026-10-07) — **correctness held, but there was no speedup** (acceptance 1.55 identical in both arms, zero
replacement/garbled characters either way, but decode went 15.83 → 15.57 tok/s, noise-level but in the wrong
direction). We read the actual running code to find out why: masking logits happens *after* the full-vocabulary matmul
already ran, so it cuts zero FLOPs. The right hook was `get_top_tokens()` all along — the exact method already proven
on Qwen3.8 — and we're rebuilding the patch to add it to both MTP-head models and EAGLE drafters alike. Where a
drafter shares `lm_head` weights with its target (common for EAGLE), the kept rows must be gathered into a fresh
tensor, never sliced from the shared one in place, to keep the "target verification path stays untouched" safety
property.

**Gemma 4 with an assistant drafter is not a target for this patch at all — correction, 2026-10-07.** We assumed it
needed the same generic patch; trying it showed otherwise. vLLM gives Gemma 4 its own dedicated code path
(`Gemma4Proposer`), and Gemma 4's `compute_logits()` already routes through a `masked_embedding` layer — the
checkpoint carries its *own* vocabulary-restriction mechanism (a centroid projection and a `token_ordering` buffer),
baked in at training time, not something a runtime file or engine patch reaches. Whether that built-in mechanism
already covers Korean adequately, or has the same English-bias gap this whole repository exists to fix, and whether it
can be swapped at all, is a separate, open question — not yet answered. (This is VENETA's own telecom stack's
architecture, which is why we track it specifically rather than lump it in.)

After Korean, other languages across Asia, Africa and the West are planned on the same recipe. Not yet measured, same
rule as every number above — nothing claimed before it is.

| family | architecture | status |
| --- | --- | --- |
| Qwen3.8 (Qwen3.8-Flash-Next, NVIDIA's checkpoint) | built-in MTP head + NVIDIA's own `get_top_tokens()` patch | **measured, public** |
| GLM 5.3 Flash · DeepSeek V4.1 Flash · Qwen3-Next · EXAONE 4.x (unverified) · Llama 3.3 70B + EAGLE-3 (and other EAGLE-style stacks) | built-in MTP head or separate drafter — both hit stock vLLM's `get_top_tokens()`-less path | need the same one patch — logit-masking tried first (EAGLE-1): correct, no speedup; rebuilding as a `get_top_tokens()` port |
| Gemma 4 + assistant drafter | its own checkpoint-baked restriction (centroid projection, not FR-Spec-style) | not a target for this patch — separate question, under investigation |

## Licence and credit

Apache-2.0 for everything in this repository (see `LICENSE`, `NOTICE`). Korean Wikipedia is the frequency source,
CC BY-SA 4.0, attributed in every file header. The method follows FR-Spec (ACL 2025) and MiaAI-Lab's DGX Spark kits.
No customer or private corpus is used in any published file.
