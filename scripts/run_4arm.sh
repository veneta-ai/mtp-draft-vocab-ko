#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Runs the 4-arm use_local_argmax_reduction attribution protocol (2026-10-09,
# following the vLLM PR #60387 review that found our EAGLE-1/EXAONE 4.5
# numbers couldn't be attributed to the patch) for one model family.
#
# Arm a: no env,  flag off  -- baseline
# Arm b: env set, flag off  -- must equal (a); proves attach-without-activate is a no-op
# Arm c: env set, flag on   -- the patch's real effect, if any
# Arm d: no env,  flag on   -- the flag's own effect (communication-reduction path), isolated
#
# Usage:
#   FAMILY=eagle1 MODEL=meta-llama/Llama-3.1-8B-Instruct \
#   SPEC_CONFIG_BASE='{"method":"eagle","model":"yuhuili/EAGLE-LLaMA3.1-Instruct-8B","num_speculative_tokens":3}' \
#   VOCAB_FILE=files/draft_vocab_ko_llama31_65k.txt \
#   ./scripts/run_4arm.sh
#
#   FAMILY=exaone45 MODEL=LGAI-EXAONE/EXAONE-4.5-33B-FP8 \
#   SPEC_CONFIG_BASE='{"method":"exaone4_5_mtp","num_speculative_tokens":3}' \
#   VOCAB_FILE=files/draft_vocab_exaone45_ko_65k.txt \
#   ./scripts/run_4arm.sh
#
# Requires: ~/vllm-env/bin (the editable veneta-patched vllm install), a free
# GPU, and the repo root as cwd. Each arm gets its own server boot (the env
# var and the flag are both read at boot, never hot-swappable) and its own
# results/runs/<date>-<family>-<arm>.jsonl via scripts/measure.py.

set -euo pipefail

: "${FAMILY:?set FAMILY (e.g. eagle1, exaone45)}"
: "${MODEL:?set MODEL (HF repo id)}"
: "${SPEC_CONFIG_BASE:?set SPEC_CONFIG_BASE (JSON, no use_local_argmax_reduction key)}"
: "${VOCAB_FILE:?set VOCAB_FILE (path relative to repo root)}"

VLLM_BIN="${VLLM_BIN:-$HOME/vllm-env/bin}"
PORT="${PORT:-8000}"
GPU_UTIL="${GPU_UTIL:-0.6}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-16384}"
BASE_URL="http://127.0.0.1:${PORT}/v1"
DATE="$(date +%Y-%m-%d)"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_LOG_DIR="$REPO_ROOT/results/runs"
mkdir -p "$RUN_LOG_DIR"

# The compile caches these libraries write to default into $HOME, where earlier
# root-in-docker runs left root-owned directories: a non-writable cache dir is a
# hard engine-init failure, not a degraded start. Keep every cache under one base
# this user owns.
# The server is started as $VLLM_BIN/python3 rather than through an activated
# venv, so the venv's bin (ninja) and the CUDA toolkit are not on PATH. A cold
# kernel cache then needs both to build, and Triton reports only "No such file
# or directory: 'ninja'".
export PATH="$VLLM_BIN:/usr/local/cuda/bin:$PATH"
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"
command -v ninja >/dev/null || { echo "ninja not on PATH (looked in $VLLM_BIN)"; exit 1; }
command -v nvcc >/dev/null || echo "WARNING: nvcc not on PATH; JIT kernel builds may fail"

# Every checkpoint in this protocol is already in the local HF cache, and the
# engine otherwise contacts the hub to list repo files at startup — on a box
# that loses its uplink (this one drops nightly) that turns into a name
# resolution error and a dead arm mid-run. Offline is both correct and immune.
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"

# Recorded in every measured row, so it is read off the installed package
# rather than defaulted to whichever build the script was first written for.
# importlib.metadata reads the dist-info, it does not import vllm.
if [ -z "${ENGINE:-}" ]; then
  _vllm_version="$("$VLLM_BIN/python3" -c 'import importlib.metadata as m; print(m.version("vllm"))' 2>/dev/null || echo "")"
  [ -n "$_vllm_version" ] || { echo "cannot read the installed vllm version; set ENGINE explicitly"; exit 1; }
  ENGINE="vLLM $_vllm_version"
fi

CACHE_BASE="${CACHE_BASE:-$HOME/.cache/veneta-4arm}"
export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$CACHE_BASE/vllm}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-$CACHE_BASE/triton}"
export TILELANG_CACHE_DIR="${TILELANG_CACHE_DIR:-$CACHE_BASE/tilelang}"
mkdir -p "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR" "$TILELANG_CACHE_DIR"
for d in "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR" "$TILELANG_CACHE_DIR"; do
  [ -w "$d" ] || { echo "cache dir not writable: $d"; exit 1; }
done

log() { echo "[$(date +%H:%M:%S)] $*"; }

# Shard load, FlashInfer autotune and CUDA-graph capture all happen before the
# health endpoint answers, so this scales with checkpoint size, not with the
# engine being stuck: a 38 GiB FP8 checkpoint needs well past ten minutes on a
# cold compile cache. Raise it rather than reading a slow boot as a failure.
BOOT_TIMEOUT_S="${BOOT_TIMEOUT_S:-2400}"

wait_for_health() {
  local waited=0
  until curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; do
    if ! kill -0 "$1" 2>/dev/null; then
      log "server process $1 exited before becoming healthy"
      return 1
    fi
    waited=$((waited + 2))
    if [ "$waited" -ge "$BOOT_TIMEOUT_S" ]; then
      log "server did not become healthy within ${BOOT_TIMEOUT_S}s"
      return 1
    fi
    sleep 2
  done
  log "server healthy after ${waited}s"
}

# vLLM's EngineCore is a child that survives its parent, so killing the
# launcher alone orphans a process holding the GPU. Each server gets its own
# process group (setsid) and the whole group is signalled.
stop_server_group() {
  local pgid="$1"
  [ -n "$pgid" ] || return 0
  kill -TERM "-$pgid" 2>/dev/null || true
  for _ in $(seq 1 15); do
    kill -0 "-$pgid" 2>/dev/null || return 0
    sleep 2
  done
  kill -KILL "-$pgid" 2>/dev/null || true
}

run_arm() {
  local arm="$1" env_on="$2" flag_on="$3"
  local boot_log="/tmp/vllm-4arm-${FAMILY}-${arm}.boot.log"
  local spec_config

  spec_config="$(python3 -c "
import json, sys
cfg = json.loads('$SPEC_CONFIG_BASE')
cfg['use_local_argmax_reduction'] = $([ "$flag_on" = "1" ] && echo True || echo False)
print(json.dumps(cfg))
")"

  log "=== arm $arm: env=$env_on flag=$flag_on ==="
  log "speculative-config: $spec_config"

  local env_args=()
  if [ "$env_on" = "1" ]; then
    env_args=(env "VLLM_SPEC_DRAFT_VOCAB=$REPO_ROOT/$VOCAB_FILE")
  else
    env_args=(env)
  fi

  setsid "${env_args[@]}" "$VLLM_BIN/python3" -m vllm.entrypoints.cli.main serve \
    --model "$MODEL" \
    --port "$PORT" \
    --gpu-memory-utilization "$GPU_UTIL" \
    --max-model-len "$MAX_MODEL_LEN" \
    --speculative-config "$spec_config" \
    > "$boot_log" 2>&1 &
  local server_pid=$!
  local server_pgid
  server_pgid="$(ps -o pgid= -p "$server_pid" 2>/dev/null | tr -d ' ')"

  log "server pid $server_pid (pgid $server_pgid), boot log $boot_log"
  if ! wait_for_health "$server_pid"; then
    log "arm $arm FAILED to boot -- tail of boot log:"
    tail -40 "$boot_log"
    stop_server_group "$server_pgid"
    return 1
  fi

  log "server healthy, checking boot log for the expected signal line"
  if [ "$env_on" = "1" ]; then
    grep "VLLM_SPEC_DRAFT_VOCAB" "$boot_log" | tail -5 || log "WARNING: no VLLM_SPEC_DRAFT_VOCAB line found in boot log"
  fi
  if [ "$flag_on" = "1" ] && [ "$env_on" = "0" ]; then
    grep -i "use_local_argmax_reduction" "$boot_log" | tail -5 || true
  fi

  local out_file="$RUN_LOG_DIR/${DATE}-${FAMILY}-${arm}.jsonl"
  "$VLLM_BIN/python3" "$REPO_ROOT/scripts/measure.py" \
    --base-url "$BASE_URL" \
    --model "$MODEL" \
    --vocab "arm-${arm} (env=${env_on} flag=${flag_on})" \
    --engine "$ENGINE" \
    --checkpoint "$MODEL" \
    --k 3 \
    --prompts "$REPO_ROOT/results/prompts/ko-general-10.jsonl" "$REPO_ROOT/results/prompts/ko-domain-10.jsonl" \
    --repeats 3 --max-tokens 400 \
    --out "$out_file"

  log "arm $arm done, shutting server down"
  stop_server_group "$server_pgid"
  wait "$server_pid" 2>/dev/null || true
  cp "$boot_log" "${out_file%.jsonl}.boot.log"
}

log "family=$FAMILY model=$MODEL vocab=$VOCAB_FILE"
run_arm a 0 0
run_arm b 1 0
run_arm c 1 1
run_arm d 0 1
log "all 4 arms done for $FAMILY -- see $RUN_LOG_DIR/${DATE}-${FAMILY}-*.jsonl"
