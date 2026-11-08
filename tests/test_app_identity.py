from pathlib import Path

from mechprox.app import _application_data_dir


def test_default_application_data_directory_uses_mechprox(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("MECHPROX_DATA_DIR", raising=False)

    assert _application_data_dir() == tmp_path / ".mechprox"


def test_mechprox_environment_override_takes_precedence(tmp_path, monkeypatch) -> None:
    target = tmp_path / "custom-workspace"
    monkeypatch.setenv("MECHPROX_DATA_DIR", str(target))

    assert _application_data_dir() == target
