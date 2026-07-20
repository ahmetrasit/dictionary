#!/usr/bin/env python3
"""Render the Turkish per-root water reports to PDF."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = (
    REPO_ROOT / "data" / "output" / "water_secondary_resonance" / "root_reports"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def require_command(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise SystemExit(f"Required command not found: {name}")
    return path


def main() -> int:
    args = parse_args()
    report_dir = args.report_dir.resolve()
    output_dir = (args.output_dir or report_dir / "pdf").resolve()
    css_path = report_dir / "report.css"

    pandoc = require_command("pandoc")
    weasyprint = require_command("weasyprint")
    sources = sorted(report_dir.glob("root_*.md"))
    if len(sources) != 20:
        raise SystemExit(f"Expected 20 root reports, found {len(sources)}")
    if not css_path.is_file():
        raise SystemExit(f"Missing stylesheet: {css_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    expected_outputs = {f"{source.stem}.pdf" for source in sources}
    for stale in output_dir.glob("root_*.pdf"):
        if stale.name not in expected_outputs:
            stale.unlink()

    with tempfile.TemporaryDirectory(prefix="water-root-reports-") as temp_dir:
        temp_path = Path(temp_dir)
        cache_path = temp_path / "cache"
        cache_path.mkdir()
        render_env = os.environ.copy()
        render_env["XDG_CACHE_HOME"] = str(cache_path)
        for source in sources:
            html_path = temp_path / f"{source.stem}.html"
            output_path = output_dir / f"{source.stem}.pdf"
            subprocess.run(
                [
                    pandoc,
                    "--from=gfm",
                    "--to=html5",
                    "--standalone",
                    "--metadata=lang:tr",
                    f"--css={css_path}",
                    f"--output={html_path}",
                    str(source),
                ],
                check=True,
                env=render_env,
            )
            subprocess.run(
                [weasyprint, "--quiet", str(html_path), str(output_path)],
                check=True,
                env=render_env,
            )

    outputs = sorted(output_dir.glob("root_*.pdf"))
    if len(outputs) != len(sources):
        raise SystemExit(
            f"Expected {len(sources)} PDFs after rendering, found {len(outputs)}"
        )
    print(f"Rendered {len(outputs)} PDFs in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
