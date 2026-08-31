# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--config-list-file",
        action="store",
        help="Path to the file listing model config YAMLs (one per line)",
    )
    parser.addoption(
        "--tp-size",
        action="store",
        default="1",
        help="Tensor parallel size to use for evaluation",
    )
    parser.addoption(
        "--load-iterations",
        action="store",
        default="20",
        help="Number of model load iterations for load-only tests",
    )


@pytest.fixture(scope="session")
def config_list_file(pytestconfig, config_dir):
    rel_path = pytestconfig.getoption("--config-list-file")
    return config_dir / rel_path


@pytest.fixture(scope="session")
def tp_size(pytestconfig):
    return pytestconfig.getoption("--tp-size")


@pytest.fixture(scope="session")
def load_iterations(pytestconfig):
    return int(pytestconfig.getoption("--load-iterations"))


def pytest_generate_tests(metafunc):
    if "config_filename" in metafunc.fixturenames:
        rel_path = metafunc.config.getoption("--config-list-file")
        config_list_file = Path(rel_path).resolve()
        config_dir = config_list_file.parent
        with open(config_list_file, encoding="utf-8") as f:
            configs = [
                config_dir / line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            ]
        metafunc.parametrize("config_filename", configs)
