# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

import pytest

from tests.utils import wait_for_gpu_memory_to_clear
from vllm.platforms import current_platform


@pytest.fixture()
def gpu_memory_cleared():
    """Wait for GPU memory to settle before a test on DPX.

    On MI355 (gfx950) with bin-packing scheduler, multiple pods run on
    the same physical node. Residual GPU memory from a prior test can
    prevent the next test from initializing (0.92 x 144 GiB barely missed).
    Only opt-in tests that need this should request this fixture.
    """
    if current_platform.is_rocm():
        wait_for_gpu_memory_to_clear(
            devices=[0],
            threshold_ratio=0.08,  # <8% = <11.5 GiB — matches observed residual
            timeout_s=30,
            stable_duration_s=1,
        )
    yield
