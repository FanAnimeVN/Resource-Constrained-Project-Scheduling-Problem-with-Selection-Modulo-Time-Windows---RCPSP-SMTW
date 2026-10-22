import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from curriculum_planner.data.loader import load_dataset  # noqa: E402


@pytest.fixture(scope="session")
def ds():
    return load_dataset("hcmus_cntt_k2020")
