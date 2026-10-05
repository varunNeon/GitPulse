import importlib.util
from pathlib import Path


def _load_keep_alive_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "keep_streamlit_alive.py"
    spec = importlib.util.spec_from_file_location("keep_streamlit_alive", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_app_selectors_cover_streamlit_shell_variants():
    module = _load_keep_alive_module()

    assert "[data-testid='stApp']" in module.APP_SELECTORS
    assert "[data-testid='stAppViewContainer']" in module.APP_SELECTORS
    assert "section.main" in module.APP_SELECTORS


def test_app_urls_accepts_comma_and_newline_separated_urls(monkeypatch):
    module = _load_keep_alive_module()

    monkeypatch.setenv("STREAMLIT_APP_URLS", "https://one.example,\nhttps://two.example")

    assert module.app_urls() == ["https://one.example", "https://two.example"]
