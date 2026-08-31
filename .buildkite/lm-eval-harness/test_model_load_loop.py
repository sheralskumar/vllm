# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
Load-only loop test for ROCm large models.

Repeatedly initializes and tears down vLLM to measure model load time
without running lm-eval inference.

pytest -s -v test_model_load_loop.py \
    --config-list-file=configs/models-large-rocm.txt \
    --tp-size=8 \
    --load-iterations=20
"""

import contextlib
import gc
import time

import pytest
import yaml

from vllm import LLM
from vllm.platforms import current_platform

from test_lm_eval_correctness import _check_rocm_gpu_arch_requirement, scoped_env_vars


def _parse_bool(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def _build_llm_kwargs(eval_config, tp_size):
    kwargs = {
        "model": eval_config["model_name"],
        "tensor_parallel_size": tp_size,
        "enforce_eager": _parse_bool(eval_config.get("enforce_eager"), True),
        "kv_cache_dtype": eval_config.get("kv_cache_dtype", "auto"),
        "trust_remote_code": eval_config.get("trust_remote_code", False),
        "max_model_len": eval_config.get("max_model_len", 4096),
        "seed": eval_config.get("seed", 1234),
    }

    moe_backend = eval_config.get("moe_backend")
    if moe_backend is not None:
        kwargs["moe_backend"] = moe_backend

    if current_platform.is_rocm():
        rocm_load_strategy = eval_config.get("rocm_safetensors_load_strategy")
        if rocm_load_strategy is not None:
            kwargs["safetensors_load_strategy"] = rocm_load_strategy

    tokenizer_mode = eval_config.get("tokenizer_mode")
    if tokenizer_mode is not None:
        kwargs["tokenizer_mode"] = tokenizer_mode

    return kwargs


def test_model_load_loop(config_filename, tp_size, load_iterations):
    eval_config = yaml.safe_load(config_filename.read_text(encoding="utf-8"))

    _check_rocm_gpu_arch_requirement(eval_config)

    llm_kwargs = _build_llm_kwargs(eval_config, tp_size)
    env_vars = eval_config.get("env_vars") or {}

    load_times = []
    with scoped_env_vars(env_vars):
        for iteration in range(1, load_iterations + 1):
            print(f"\n{'=' * 80}")
            print(f"Load iteration {iteration}/{load_iterations}")
            print(f"{'=' * 80}\n")

            start = time.perf_counter()
            llm = LLM(**llm_kwargs)
            load_time = time.perf_counter() - start
            load_times.append(load_time)

            print(f"Load iteration {iteration} completed in {load_time:.2f}s")

            with contextlib.suppress(Exception):
                llm.llm_engine.shutdown()
            del llm
            gc.collect()

    print(f"\nLoad time summary ({load_iterations} iterations):")
    for i, load_time in enumerate(load_times, 1):
        print(f"  iteration {i}: {load_time:.2f}s")
    print(f"  min: {min(load_times):.2f}s")
    print(f"  max: {max(load_times):.2f}s")
    print(f"  avg: {sum(load_times) / len(load_times):.2f}s")

    assert load_times
