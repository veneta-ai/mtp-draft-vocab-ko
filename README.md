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

EXAONE 4.5(실제 체크포인트 LGAI-EXAONE/EXAONE-4.5-33B로 확인, architectures: Exaone4_5_ForConditionalGeneration, MTP 레이어 1개)는 같은 패턴의 두 번째 확인 사례입니다. vLLM의 exaone4_5_mtp.py를 코드로 전부 읽었고(2026-10-07), compute_logits()가 평범한 ParallelLMHead 위의 표준 호출이라 get_top_tokens()도 내장 제한도 없습니다 — Qwen3.8처럼 파일만으로는 안 되고, get_top_tokens()를 추가하는 엔진 패치가 있어야 하는 쪽입니다. GLM 5.3 Flash와 DeepSeek V4.1 Flash는 처음에 같은 부류로 짐작했는데 틀렸습니다. 실제 체크포인트의 config.json을 직접 확인해보니 GLM 5.3 Flash는 Glm5NextForConditionalGeneration(glm5_next)으로, 짐작했던 Glm4Moe 계열이 아니었고, 보유한 vLLM 두 버전(안정판 0.27.1, MiaAI 키트가 쓰는 개발 나이틀리) 어디에도 glm5_next를 아는 코드가 없어서 MTP 배선을 확인할 수 없었습니다. DeepSeek V4.1 Flash도 DeepseekV41ForCausalLM(deepseek_v41)으로, 짐작했던 구버전 파일이 아니었습니다. 개발 나이틀리에 점(.) 없는 DeepSeek V4 자체는 등록되어 있지만, 그 모델 전용 엔비디아 파일에도 get_top_tokens()가 없어서 — 엔비디아가 Qwen3.8 이후로 아직 다른 가족에 이 패치를 확장하지 않았다는 뜻입니다. 이 둘은 버전 문제로 막힌 미확인 상태로 남겨둡니다. Qwen3-Next도 아직 실제 config로 재확인하지 못했으니 같은 "미확인" 쪽에 둡니다.

본 모델과 별도의 더 작은 EAGLE 방식 드래프터 모델을 함께 쓰는 구조(예: EAGLE-3을 쓰는 Llama 3.3 70B)에도 같은 패치가 필요합니다. 처음에는 로짓 마스킹(전체 어휘로 계산한 뒤 일부만 고르는 방식)으로 범용 패치를 만들어 EAGLE-1(Llama 3.1 8B, 한국어 프롬프트 10개, 2026-10-07)로 실측했는데, 정확성은 지켰지만 속도는 전혀 빨라지지 않았습니다(연산량이 줄지 않는 구조였기 때문). 그래서 올바른 훅 지점인 get_top_tokens() 자체로 다시 만들었습니다 — MiaAI가 Qwen3.8에서 이미 쓴 바로 그 방법(lm_head 가중치에서 남길 어휘 행만 index_select로 새 텐서에 모으고, 더 작은 행렬로만 곱하고, 결과를 원래 어휘 id로 재매핑)을 EAGLE과 MTP 헤드 모델 모두에 적용되는 범용 패치로 포팅했습니다. 같은 EAGLE-1 환경, 같은 프롬프트, 같은 어휘 파일로 다시 측정한 결과: **디코딩 15.83 → 17.95 tok/s(+13.4%), 수락률 1.55 → 1.57, 대체 문자 0개 — 이번에는 진짜로 빨라졌습니다.** 부트 로그에서 lm_head 읽기 크기가 실제로 51.1%로 줄어든 것도 확인했습니다(65,536 / 128,256과 거의 정확히 일치). Qwen3.8의 54%보다는 작은데, EAGLE-1 자체의 드래프트 트랜스포머 연산이 lm_head 하나보다 턴당 비중이 훨씬 크고, 이 장비는 GPU 1개(TP=1)라 통신 절감 효과도 없기 때문으로 보입니다 — 구조상 설명이 되는 차이입니다. 드래프터가 타깃과 lm_head 가중치를 공유하는 경우(EAGLE에서 흔함)는 공유 텐서를 직접 잘라내지 않고 항상 새 텐서로 gather하고, get_top_tokens()는 공유 클래스가 아니라 해당 드래프터 인스턴스에만 types.MethodType으로 붙여서 "타깃 검증 경로는 절대 안 건드린다"는 안전 원칙을 지켰습니다. EXAONE 4.5로 두 번째 확인을 진행 중입니다.

**어시스턴트 드래프터를 쓰는 Gemma 4는 이 패치로 되는 대상이 아닙니다 — 2026-10-07 정정.** 같은 범용 패치가 통할 거라 가정했는데, 실제로 걸어 보니 아니었습니다. vLLM은 Gemma 4에 전용 코드 경로(Gemma4Proposer)를 따로 두고 있고, Gemma 4의 compute_logits()는 이미 masked_embedding이라는 레이어를 거칩니다 — 체크포인트 자체가 자기만의 어휘 제한 메커니즘(centroid projection과 token_ordering 버퍼)을 학습 때부터 내장하고 있다는 뜻입니다. MTP 헤드의 드래프트 어휘처럼 런타임에 파일이나 엔진 패치로 바꿀 수 있는 게 아닙니다. 이 내장 메커니즘이 한국어를 이미 잘 다루는지, 아니면 이 저장소 전체가 고치려는 바로 그 영어 편향 문제를 똑같이 안고 있는지, 그리고 애초에 바꿀 수 있는 것인지는 완전히 별도의, 아직 답하지 않은 질문입니다 — 끝났다고 하지 않습니다. (이 구조는 veneta 자신의 통신 스택 구조라서 따로 추적하고 있습니다.)

한국어 다음은 아시아·아프리카·서구권의 다른 언어들도 같은 방식으로 만들 계획입니다. 아직 측정 전이라 위의 모든 숫자와 같은 규칙을 따릅니다 — 측정되기 전에는 주장하지 않습니다.

| 가족 | 구조 | 상태 |
| --- | --- | --- |
| Qwen3.8 (Qwen3.8-Flash-Next, nvidia 체크포인트) | 자체 MTP 헤드 + 엔비디아가 이미 패치한 get_top_tokens() | **측정 완료, 공개됨** |
| Llama 3.1 8B + EAGLE-1 | 별도 드래프터 모델 | **get_top_tokens() 패치 실측: 15.83 → 17.95 tok/s(+13.4%), 수락률 1.55 → 1.57, 대체 문자 0개** |
| EXAONE 4.5(LGAI-EXAONE/EXAONE-4.5-33B) · Llama 3.3 70B + EAGLE-3(그 외 EAGLE 방식 스택) | 자체 MTP 헤드 또는 별도 드래프터, 둘 다 get_top_tokens()가 없는 표준 vLLM 경로로 확인됨 | 같은 패치가 작동함을 EAGLE-1로 확인; EXAONE 4.5로 두 번째(자체 MTP 헤드) 확인 진행 중 |
| GLM 5.3 Flash · DeepSeek V4.1 Flash · Qwen3-Next | 실제 체크포인트가 알려지지 않은/더 새 아키텍처(glm5_next, deepseek_v41) | 미확인 — 보유한 vLLM 버전이 이 아키텍처를 모름, 상류 지원 기다리는 중 |
| Gemma 4 + 어시스턴트 드래프터 | 체크포인트에 내장된 자체 제한 방식(FR-Spec식이 아닌 centroid projection) | 이 패치의 대상이 아닌 별도 질문 — 조사 중 |

## 선행 연구 — 먼저 한 사람들이 있습니다 (2026-10-07 추가)

드래프터의 어휘를 줄이는 아이디어 자체는 저희가 처음이 아닙니다. vLLM 저장소에서 찾았습니다. akapug님이 저희보다 먼저(2026-09-24) 이슈 #58578에서 같은 아이디어(타깃과 lm_head를 공유하는 MTP 드래프터의 어휘를 줄이자)를 제안하고 Intel Arc에서 Qwen3.5 계열로 +25~29%를 측정했습니다. stecasta님의 PR #59740("Context Aware Sparse LM Head", 2026-10-02 오픈, 아직 미병합)은 이 이슈를 정면으로 다루는, 저희보다 훨씬 정교한 구현입니다 — 저희처럼 고정된 빈도 목록 하나가 아니라 고정 32k 목록에 드래프트 토큰마다 rank-256 SVD로 고르는 16k를 더합니다. **같은 모델(Qwen3.8-Flash-Next-NVFP4), 같은 하드웨어(DGX Spark 1대)로 측정했는데 숫자는 +15.2%(BF16)·+22.6%(NVFP4)로, MiaAI의 +54%(저희 Qwen3.8 결과가 기대는 바로 그 패치)와 꽤 다릅니다.** 이유는 추측하지 않습니다 — 프롬프트 구성, 동시 요청 수, 정적 대 동적 선택, 기준선 차이 등 여러 가능성이 있을 뿐 확인된 바 없습니다. 다만 "같은 것"이라는 두 숫자가 이렇게 다르다는 사실 자체는 숨기지 않고 적어둡니다.

PR #59740의 변경 파일 목록을 직접 확인했습니다. `qwen3_5_mtp.py`, `qwen3_eagle3.py`, `qwen3_dflash.py`, `qwen3_dspark.py`, `llama_eagle3.py`, `deepseek_eagle3.py`, `gemma4_dspark.py`, `qwen4_exp/{nvidia,amd}/mtp.py` 같은 신형 모델 파일만 건드리고, 저희가 오늘 밤 작업한 평범한 `eagle.py`, `exaone4_5_mtp.py`, `glm4_moe_mtp.py`, `deepseek_mtp.py` 같은 구형 범용 MTP/EAGLE 파일은 건드리지 않습니다. 그래서 저희 작업이 같은 걸 다시 만든 게 아니라, 그 PR이 다루지 않는 모델군을 더 단순한 방식(고정 빈도 목록 하나)으로 다룬 것이라고 봅니다. upstream PR로는 이 둘을 구분해서 — #58578/#59740에 보완 관계임을 댓글로 남기고, 별도 PR로 제출할 계획입니다.

## 라이선스와 크레딧

이 저장소의 모든 것은 Apache-2.0(`LICENSE`, `NOTICE`). 빈도 출처인 한국어 위키백과는 CC BY-SA 4.0이며 모든 파일 머리에 표기합니다. 방법은 FR-Spec(ACL 2025)과 MiaAI-Lab의 DGX Spark 키트를 따릅니다. vLLM 이슈 #58578(akapug)과 PR #59740(stecasta, "Context Aware Sparse LM Head")가 드래프터 어휘 축소라는 아이디어를 저희보다 먼저 제안·구현했고, 저희 작업은 그 PR이 다루지 않는 모델군을 다루는 보완적인 것입니다. 공개 파일에 고객 문서나 비공개 코퍼스는 쓰지 않습니다.

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

EXAONE 4.5 (confirmed against the real checkpoint, `LGAI-EXAONE/EXAONE-4.5-33B`, `architectures:
Exaone4_5_ForConditionalGeneration`, one native MTP layer) is a second confirmed example of this. Its vLLM model file,
`exaone4_5_mtp.py`, was read in full (2026-10-07): `compute_logits()` is a plain call over a standard `ParallelLMHead`,
no `get_top_tokens()`, no baked-in restriction — it needs the same engine patch as Llama+EAGLE, not just a vocabulary
file. GLM 5.3 Flash and DeepSeek V4.1 Flash were first guessed to be the same case from their family names; that guess
was wrong. Their real checkpoints' `config.json` show `Glm5NextForConditionalGeneration` (`glm5_next`) and
`DeepseekV41ForCausalLM` (`deepseek_v41`) — architectures neither of the two vLLM builds on hand (stable 0.27.1, nor
the dev nightly the MiaAI kit itself uses) recognize, so their MTP wiring can't be determined yet; it needs a newer
vLLM than what's available. The dev nightly does register a DeepSeek-V4 family (no ".1"), but even its own NVIDIA
vendor file has no `get_top_tokens()` — NVIDIA hasn't extended its Qwen3.8 fast path to other families yet either.
Both stay marked unverified, blocked on upstream vLLM support, not "expected to work". Qwen3-Next hasn't been checked
against a real config either, so it's grouped with them rather than assumed confirmed on the same kind of
family-name inference that was wrong for GLM and DeepSeek.

A model that pairs a full-size target with a separate, smaller EAGLE-style drafter (e.g. Llama 3.3 70B with EAGLE-3)
needs that same patch too. We first built it as logit masking and measured it (EAGLE-1, Llama 3.1 8B, 10 Korean
prompts, 2026-10-07) — correctness held but there was no speedup at all, because masking logits happens *after* the
full-vocabulary matmul already ran, cutting zero FLOPs. So we rebuilt it around the real hook, `get_top_tokens()` —
porting the exact mechanism MiaAI already proved on Qwen3.8 (`index_select` the kept-vocabulary rows out of
`lm_head`'s weight into a fresh tensor, a smaller matmul against only those rows, map the reduced argmax index back to
the true vocabulary id) into a generic patch that covers both MTP-head models and EAGLE drafters. Measured again on
the same EAGLE-1 setup, same prompts, same vocabulary file: **decode 15.83 → 17.95 tok/s (+13.4%), acceptance 1.55 →
1.57, zero replacement characters — a real speedup this time.** The boot log confirms the mechanism is actually
engaging, not a measurement artifact: the `lm_head` read shrank to 51.1% of its original size, matching the
kept-vocabulary fraction (65,536 / 128,256) almost exactly. Smaller than Qwen3.8's +54%, which makes architectural
sense — EAGLE-1's own one-layer draft transformer is a much bigger share of per-step compute than a single `lm_head`
read, and this machine runs one GPU (TP=1), so there's no tensor-parallel communication saving either way. Where a
drafter shares `lm_head` weights with its target (common for EAGLE), the kept rows are gathered into a fresh tensor,
never sliced from the shared one in place, and `get_top_tokens()` is attached via `types.MethodType` to the specific
drafter instance only, never the shared class, to keep the "target verification path stays untouched" safety
property. A second confirmation on EXAONE 4.5 (a native MTP-head model) is in progress.

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
| Llama 3.1 8B + EAGLE-1 | separate drafter model | **`get_top_tokens()` patch measured: 15.83 → 17.95 tok/s (+13.4%), acceptance 1.55 → 1.57, zero replacement characters** |
| EXAONE 4.5 (`LGAI-EXAONE/EXAONE-4.5-33B`) · Llama 3.3 70B + EAGLE-3 (and other EAGLE-style stacks) | built-in MTP head or separate drafter, both confirmed to hit stock vLLM's `get_top_tokens()`-less path | same patch confirmed working via EAGLE-1; a second confirmation (a native MTP head) via EXAONE 4.5 is in progress |
| GLM 5.3 Flash · DeepSeek V4.1 Flash · Qwen3-Next | real checkpoints use an architecture (`glm5_next`, `deepseek_v41`) not yet in either vLLM build on hand | unverified — blocked on a newer vLLM than we have, not yet checked |
| Gemma 4 + assistant drafter | its own checkpoint-baked restriction (centroid projection, not FR-Spec-style) | not a target for this patch — separate question, under investigation |

## Prior art — we are not first (added 2026-10-07)

The idea of trimming a drafter's vocabulary isn't ours. We found it in the vLLM repository. akapug proposed the same
idea (trim an MTP drafter's vocabulary when it shares `lm_head` with its target) in issue #58578 before we started
(2026-09-24), measuring +25-29% on Qwen3.5-family models on Intel Arc. stecasta's PR #59740 ("Context Aware Sparse LM
Head", opened 2026-10-02, still open) addresses that issue directly, with a materially more sophisticated mechanism
than ours — a static 32k list plus 16k rows picked per draft token by a rank-256 SVD scorer, not a single fixed
frequency list. **Measured on the exact same model (Qwen3.8-Flash-Next-NVFP4) and hardware class (one DGX Spark) as
ours, their numbers are +15.2% (BF16 rows) and +22.6% (NVFP4 rows) — notably different from MiaAI's +54% that our own
Qwen3.8 result rests on.** We don't know why; prompt composition, concurrency, static-vs-dynamic row selection and
baseline choice are all plausible candidates, none confirmed. We're not hiding that two numbers for "the same thing"
disagree this much.

We checked PR #59740's changed-file list directly: it touches newer model files (`qwen3_5_mtp.py`, `qwen3_eagle3.py`,
`qwen3_dflash.py`, `qwen3_dspark.py`, `llama_eagle3.py`, `deepseek_eagle3.py`, `gemma4_dspark.py`,
`qwen4_exp/{nvidia,amd}/mtp.py`) and does not touch the plain, older-style files we worked on tonight (`eagle.py`,
`exaone4_5_mtp.py`, `glm4_moe_mtp.py`, `deepseek_mtp.py`). So our work isn't a duplicate of theirs — it covers the
model families their PR doesn't reach, with a simpler, static-list-only mechanism. We plan to submit it as its own PR
and comment on #58578/#59740 to credit them and cross-link rather than let a silent parallel effort stand.

## Licence and credit

Apache-2.0 for everything in this repository (see `LICENSE`, `NOTICE`). Korean Wikipedia is the frequency source,
CC BY-SA 4.0, attributed in every file header. The method follows FR-Spec (ACL 2025) and MiaAI-Lab's DGX Spark kits.
vLLM issue #58578 (akapug) and PR #59740 (stecasta, "Context Aware Sparse LM Head") proposed and built drafter
vocabulary trimming before we did; our work is a complementary piece covering the model families that PR doesn't
reach. No customer or private corpus is used in any published file.
