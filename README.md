<p align="center"><img src="assets/banner.svg" alt="mtp-draft-vocab-ko" width="720"></p>

# mtp-draft-vocab-ko

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-5b4fb5)](LICENSE)
[![Hugging Face dataset](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-veneta--ai%2Fmtp--draft--vocab--ko-ffcc4d)](https://huggingface.co/datasets/veneta-ai/mtp-draft-vocab-ko)
[![Method: FR-Spec](https://img.shields.io/badge/method-FR--Spec%20(ACL%202025)-2fd58a)](https://aclanthology.org/2025.acl-long.198.pdf)

Korean draft vocabularies for MTP speculative decoding — one file per tokenizer family, built from Korean Wikipedia,
measured before and after on the same machine, so a model that answers in Korean gets the speed-up its English users
already get.

**Status: first result in (2026-10-07).** Qwen3.8 (`nvidia/Qwen3.8-Flash-Next-NVFP4`): decode 16.9 → 26.1 tok/s (+54%), draft acceptance 1.33 → 2.16 accepted/draft, zero replacement characters, zero Korean-script drift, veneta-bench's 12 memory-ability cases unaffected (12/12). Conditions and raw run files in `results/README.md`. Other families below are not yet measured; nothing is claimed before it is.

<p align="center"><img src="assets/speedup-qwen3.8.svg" alt="Qwen3.8-Flash-Next decode speed, shipped vocabulary vs. +ko 65k: 16.9 to 26.1 tokens per second, +54%" width="560"></p>

## Why

Speculative decoding with an MTP head drafts several tokens and lets the target model verify them. FR-Spec-style
trimming computes the draft head's output projection only over a frequency-ranked subset of the vocabulary; the target
still verifies over the full vocabulary, so the output is exactly the same — only the draft gets cheaper. The subsets
shipped today are ranked on English and code. Korean tokens fall outside them, Korean drafts are rejected, and the
speed-up disappears for Korean answers. MiaAI-Lab's language-extended files restore it for zh · ja · de · pt · fr · ru · es
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

Two different architectures answer "what drafts the extra tokens", and that is what decides whether a file like this
one can even apply, not which company trained the model.

**A model with a built-in MTP head drafts its own extra tokens.** Its draft head's output projection can be restricted
to a subset of the vocabulary — that is what this file does, and what MiaAI-Lab's overlay already does for seven other
languages. Qwen3.8-Flash-Next is measured and public. GLM 5.3 Flash, DeepSeek V4.1 Flash, EXAONE 4.x and other
Qwen3.8/Qwen3-Next checkpoints also have an MTP head and are **expected to take the same kind of file**, but that is
not yet verified — MiaAI-Lab's overlay was built against Qwen3.8's `mtp.py`, and whether it attaches the same way to
each other family's own vLLM code is an open check, not an assumption we are publishing as fact. No file for those
families exists here yet; a claim awaits its own measurement, same as every number above.

**A model that pairs a full-size target with a separate, smaller drafter model (e.g. Gemma 4 with an assistant
drafter, or Llama 3.3 70B with EAGLE-3) cannot use this method at all today.** The thing to restrict there is the
separate drafter's own vocabulary head, not an MTP head inside the target, and no generic vLLM patch for that exists
yet — this is blocked on new engine code, not on building another file. (This is also VENETA's own telecom stack's
architecture, which is why we are tracking it, not because it is close.)

| family | architecture | status |
| --- | --- | --- |
| Qwen3.8 (Qwen3.8-Flash-Next) | built-in MTP head | **measured, public** |
| GLM 5.3 Flash · DeepSeek V4.1 Flash · EXAONE 4.x · other Qwen3.8/Qwen3-Next checkpoints | built-in MTP head | expected to work, unverified — no file yet |
| Gemma 4 + assistant drafter · Llama 3.3 70B + EAGLE-3 | separate drafter model | blocked — needs a vLLM engine patch that does not exist yet |

## Licence and credit

Apache-2.0 for everything in this repository (see `LICENSE`, `NOTICE`). Korean Wikipedia is the frequency source,
CC BY-SA 4.0, attributed in every file header. The method follows FR-Spec (ACL 2025) and MiaAI-Lab's DGX Spark kits.
No customer or private corpus is used in any published file.

---

# mtp-draft-vocab-ko (한국어)

MTP 추측 디코딩용 한국어 드래프트 어휘사전입니다. 토크나이저 가족마다 파일 하나를 한국어 위키백과로 만들고, 같은
장비에서 적용 전후를 재서 올립니다. 한국어로 답하는 모델이 영어 사용자가 이미 받는 속도 이득을 받게 하는 것이 목적입니다.

**상태: 첫 결과 (2026-10-07).** Qwen3.8(nvidia/Qwen3.8-Flash-Next-NVFP4): 디코딩 16.9 → 26.1 tok/s(+54%), 드래프트 수락률 1.33 → 2.16, 복제 문자 0개, 한국어 스크립트 오염 0개, veneta-bench 12개 기억 능력 문항 영향 없음(12/12). 조건과 원시 실행 파일은 results/README.md에 있습니다. 아래 다른 가족은 아직 측정 전이며, 재기 전에는 아무것도 주장하지 않습니다.

## 왜

MTP 헤드가 토큰 몇 개를 미리 제안하고 본 모델이 검증하는 것이 추측 디코딩입니다. FR-Spec 방식은 드래프트 헤드의 출력
투영을 빈도 상위 어휘 부분집합으로만 계산합니다. 검증은 전체 어휘로 하므로 출력은 정확히 같고 드래프트만 싸집니다.
지금 배포되는 부분집합은 영어와 코드 기준이라 한국어 토큰이 빠지고, 한국어 드래프트는 거절되어 속도 이득이 사라집니다.
MiaAI-Lab의 언어 확장 파일이 중·일·독·포·불·러·스페인어에 이득을 되살렸고(DGX Spark 1대에서 디코드 +10~77 %),
한국어 파일은 없습니다. 이 저장소가 토크나이저 가족별로 그것을 더하고, 빌드 스크립트와 측정값을 함께 둡니다.

## 사용 (vLLM, Qwen3.8-Flash-Next, MiaAI 오버레이)

```bash
MTP_DRAFT_VOCAB=files/draft_vocab_ko_qwen3.8_en_code_65k.txt   # 비우면 기본 en+code
```

## 어떤 모델에 적용되는가

"추가 토큰을 누가 제안하는가"를 가르는 구조가 둘이고, 이 파일이 적용되는지 안 되는지를 가르는 것도 이 구조이지, 어느 회사가 만들었는지가 아닙니다.

**자체 MTP 헤드가 있는 모델은 자기 안에서 추가 토큰을 제안합니다.** 이 드래프트 헤드의 출력 투영을 어휘 부분집합으로 제한할 수 있고, 이 파일이 하는 일과 MiaAI-Lab의 오버레이가 다른 일곱 언어에서 이미 하는 일이 바로 그것입니다. Qwen3.8-Flash-Next는 측정을 마치고 공개되어 있습니다. GLM 5.3 Flash, DeepSeek V4.1 Flash, EXAONE 4.x와 다른 Qwen3.8/Qwen3-Next 체크포인트도 MTP 헤드가 있어 같은 종류의 파일을 받을 것으로 예상하지만, 아직 확인된 사실은 아닙니다. MiaAI-Lab의 오버레이는 Qwen3.8의 mtp.py를 대상으로 만들어졌고, 다른 가족의 vLLM 코드에도 같은 방식으로 붙는지는 아직 열린 확인 과제이며 사실로 공개하는 가정이 아닙니다. 이 가족들의 파일은 아직 여기에 없고, 위의 모든 숫자와 마찬가지로 주장에는 자신의 측정이 따라야 합니다.

**본 모델과 별도의 더 작은 드래프터 모델을 함께 쓰는 구조(예: 어시스턴트 드래프터를 쓰는 Gemma 4, 또는 EAGLE-3을 쓰는 Llama 3.3 70B)는 지금은 이 방법을 전혀 쓸 수 없습니다.** 거기서 제한해야 할 대상은 본 모델 안의 MTP 헤드가 아니라 별도 드래프터 자신의 어휘 헤드이고, 그걸 위한 범용 vLLM 패치가 아직 없습니다. 이건 파일을 하나 더 만드는 문제가 아니라 새로운 엔진 코드가 필요한 문제입니다. (이 구조는 veneta 자신의 통신 스택 구조이기도 해서 추적하고 있는 것이고, 가까워서가 아닙니다.)

| 가족 | 구조 | 상태 |
| --- | --- | --- |
| Qwen3.8 (Qwen3.8-Flash-Next) | 자체 MTP 헤드 | **측정 완료, 공개됨** |
| GLM 5.3 Flash · DeepSeek V4.1 Flash · EXAONE 4.x · 다른 Qwen3.8/Qwen3-Next 체크포인트 | 자체 MTP 헤드 | 될 것으로 예상, 미확인 — 파일 아직 없음 |
| Gemma 4 + 어시스턴트 드래프터 · Llama 3.3 70B + EAGLE-3 | 별도 드래프터 모델 | 막힘 — 아직 없는 vLLM 엔진 패치가 필요 |

## 라이선스와 크레딧

이 저장소의 모든 것은 Apache-2.0(`LICENSE`, `NOTICE`). 빈도 출처인 한국어 위키백과는 CC BY-SA 4.0이며 모든 파일 머리에
표기합니다. 방법은 FR-Spec(ACL 2025)과 MiaAI-Lab의 DGX Spark 키트를 따릅니다. 공개 파일에 고객 문서나 비공개 코퍼스는
쓰지 않습니다.
