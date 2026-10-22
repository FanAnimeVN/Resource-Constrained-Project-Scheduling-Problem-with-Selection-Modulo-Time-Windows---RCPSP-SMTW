"""Điểm vào hàm serverless Python trên Vercel: phục vụ FastAPI app tại /api/*."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))
os.environ.setdefault("CPLAN_DATA_DIR", str(ROOT / "data"))
# Giao diện tĩnh do Vercel phục vụ; hàm chỉ xử lý API.
os.environ.setdefault("CPLAN_WEB_DIST", str(ROOT / "__no_dist__"))

from curriculum_planner.api.app import app  # noqa: E402,F401
