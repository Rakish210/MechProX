import tempfile
from pathlib import Path

from mechprox.core.config import ConfigManager


def test_config_roundtrip():
    d = Path(tempfile.mkdtemp())
    p = d / "config.json"
    c = ConfigManager(p)
    c.set("a", 1)
    c2 = ConfigManager(p)
    assert c2.get("a") == 1
