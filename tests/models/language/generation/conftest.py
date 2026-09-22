# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

import pytest

from tests.utils import wait_for_gpu_memory_to_clear
from vllm.platforms import current_platform


@pytest.fixture(autouse=True)
def wait_for_gpu_memory_before_test():
    """Wait for GPU memory to settle before each test.

    On DPX (MI355/gfx950) with bin-packing scheduler, multiple pods run on
    the same physical node simultaneously. Residual GPU memory from a prior
    test can prevent the next test from initializing (threshold barely missed).
    """
    if current_platform.is_rocm():
        wait_for_gpu_memory_to_clear(
            devices=[0],
            threshold_ratio=0.05,  # wait until <5% of partition is used
            timeout_s=60,
            stable_duration_s=2,
        )
    yield
