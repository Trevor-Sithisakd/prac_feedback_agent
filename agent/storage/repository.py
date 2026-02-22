"""Persistence helpers for saving pipeline runs and finalized outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List


@dataclass
class FileRepository:
    base_dir: Path = Path("runs")

    def save_run(self, state: Dict) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        path = self.base_dir / f"run_{stamp}.json"
        path.write_text(json.dumps(state, indent=2))
        return path

    def save_final(self, final_output: Dict) -> Path:
        final_dir = self.base_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        path = final_dir / f"final_{stamp}.json"
        path.write_text(json.dumps(final_output, indent=2))
        return path

    def list_runs(self) -> List[Path]:
        if not self.base_dir.exists():
            return []
        return sorted(self.base_dir.glob("run_*.json"))
