from pathlib import Path

from mechpro.app import _application_data_dir


def test_new_installation_uses_mechprox_data_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("MECHPROX_DATA_DIR", raising=False)
    monkeypatch.delenv("MECHPRO_DATA_DIR", raising=False)

    assert _application_data_dir() == tmp_path / ".mechprox"


def test_existing_mechpro_data_directory_is_reused_without_deletion(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("MECHPROX_DATA_DIR", raising=False)
    monkeypatch.delenv("MECHPRO_DATA_DIR", raising=False)
    legacy = tmp_path / ".mechpro"
    legacy.mkdir()
    database = legacy / "mechpro.db"
    database.write_bytes(b"existing-project-data")

    assert _application_data_dir() == legacy
    assert database.read_bytes() == b"existing-project-data"


def test_mechprox_data_directory_takes_precedence_over_legacy_folder(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("MECHPROX_DATA_DIR", raising=False)
    monkeypatch.delenv("MECHPRO_DATA_DIR", raising=False)
    (tmp_path / ".mechpro").mkdir()
    current = tmp_path / ".mechprox"
    current.mkdir()

    assert _application_data_dir() == current


def test_mechprox_environment_override_takes_precedence(tmp_path, monkeypatch) -> None:
    target = tmp_path / "custom-workspace"
    monkeypatch.setenv("MECHPROX_DATA_DIR", str(target))
    monkeypatch.setenv("MECHPRO_DATA_DIR", str(tmp_path / "legacy-override"))

    assert _application_data_dir() == target


def test_existing_mechpro_database_file_is_reused(tmp_path) -> None:
    from mechpro.app import _database_file

    legacy_database = tmp_path / "mechpro.db"
    legacy_database.write_bytes(b"existing-database")

    assert _database_file(tmp_path) == legacy_database
    assert legacy_database.read_bytes() == b"existing-database"


def test_new_mechprox_database_name_is_used_without_legacy_database(tmp_path) -> None:
    from mechpro.app import _database_file

    assert _database_file(tmp_path) == tmp_path / "mechprox.db"


def test_existing_mechprox_database_takes_precedence(tmp_path) -> None:
    from mechpro.app import _database_file

    current_database = tmp_path / "mechprox.db"
    current_database.write_bytes(b"current-database")
    (tmp_path / "mechpro.db").write_bytes(b"legacy-database")

    assert _database_file(tmp_path) == current_database
