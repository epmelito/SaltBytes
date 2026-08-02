from pathlib import Path
from typing import Any

import pytest

from saltbytes.cli import main


def test_main_exports_dashboard_data_without_running_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config: dict[str, Any] = {"logging": {"level": "INFO"}}
    output_path = tmp_path / "dashboard-data"
    calls: list[tuple[dict[str, Any], Path]] = []

    monkeypatch.setattr("saltbytes.cli.load_config", lambda: config)
    monkeypatch.setattr("saltbytes.cli.configure_logging", lambda _: None)
    monkeypatch.setattr(
        "saltbytes.cli.export_dashboard_data",
        lambda selected_config, selected_output: calls.append(
            (selected_config, selected_output)
        ),
    )
    monkeypatch.setattr(
        "saltbytes.cli.run_pipeline",
        lambda _: pytest.fail("pipeline must not run while exporting dashboard data"),
    )

    main(["dashboard", "export", "--output", str(output_path)])

    assert calls == [(config, output_path)]
