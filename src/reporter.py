"""Reporter module for RepoSignal.

Takes analyzer results and renders a Markdown report using Jinja2.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def generate_report(results: dict[str, Any], *, date: str | None = None) -> Path:
    """Render analysis results into a Markdown report.

    Args:
        results: Dict returned by analyzer.analyze().
        date: Override date string (YYYY-MM-DD). Defaults to today.

    Returns:
        Path to the generated report file.
    """
    now = datetime.now(timezone.utc)
    if date is None:
        date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%H%M%S")

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate English report
    template_en = env.get_template("report.md.j2")
    rendered_en = template_en.render(date=date, results=results)
    output_path = REPORTS_DIR / f"patterns-{date}-{timestamp}.md"
    output_path.write_text(rendered_en)
    logger.info("Report written to %s", output_path)

    # Generate Traditional Chinese report
    template_zh = env.get_template("report-zh-tw.md.j2")
    rendered_zh = template_zh.render(date=date, results=results)
    output_path_zh = REPORTS_DIR / f"patterns-{date}-{timestamp}-zh-tw.md"
    output_path_zh.write_text(rendered_zh)
    logger.info("Report written to %s", output_path_zh)

    return output_path
