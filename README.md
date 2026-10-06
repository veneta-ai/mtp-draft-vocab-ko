# mtp-draft-vocab-ko

Korean draft vocabularies for MTP speculative decoding — one file per tokenizer family, built from Korean Wikipedia,
measured before and after on the same machine, so a model that answers in Korean gets the speed-up its English users
already get.

**Status: in preparation (2026-10-06).** Files and numbers land here first; nothing is claimed before it is measured.

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

## Tokenizer families

| family | models it covers | stage |
| --- | --- | --- |
| Qwen3.8 | Qwen3.8-Flash-Next (measured first), other Qwen3.8 checkpoints with an MTP proposer | 1 |
| GLM | GLM 5.3 Flash | 2 |
| DeepSeek | DeepSeek V4.1 Flash | 2 |
| EXAONE 4 | EXAONE 4.x | 2 |
| Gemma 4 | Gemma 4 31B + assistant drafter | 3 — needs an engine switch for drafter-model stacks |
| Llama 3 | Llama 3.3 70B + EAGLE-3 | 3 — same |

## Licence and credit

Apache-2.0 for everything in this repository (see `LICENSE`, `NOTICE`). Korean Wikipedia is the frequency source,
CC BY-SA 4.0, attributed in every file header. The method follows FR-Spec (ACL 2025) and MiaAI-Lab's DGX Spark kits.
No customer or private corpus is used in any published file.

---

# mtp-draft-vocab-ko (한국어)

MTP 추측 디코딩용 한국어 드래프트 어휘사전입니다. 토크나이저 가족마다 파일 하나를 한국어 위키백과로 만들고, 같은
장비에서 적용 전후를 재서 올립니다. 한국어로 답하는 모델이 영어 사용자가 이미 받는 속도 이득을 받게 하는 것이 목적입니다.

**상태: 준비 중 (2026-10-06).** 파일과 숫자가 먼저 올라오고, 재기 전에는 아무것도 주장하지 않습니다.

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

## 라이선스와 크레딧

이 저장소의 모든 것은 Apache-2.0(`LICENSE`, `NOTICE`). 빈도 출처인 한국어 위키백과는 CC BY-SA 4.0이며 모든 파일 머리에
표기합니다. 방법은 FR-Spec(ACL 2025)과 MiaAI-Lab의 DGX Spark 키트를 따릅니다. 공개 파일에 고객 문서나 비공개 코퍼스는
쓰지 않습니다.
