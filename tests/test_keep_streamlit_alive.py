import importlib.util
from pathlib import Path


def _load_keep_alive_module():
    module_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "keep_streamlit_alive.py"
    )
    spec = importlib.util.spec_from_file_location("keep_streamlit_alive", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_app_ready_selector_covers_legacy_and_new_streamlit_shells():
    module = _load_keep_alive_module()

    assert "[data-testid='stApp']" in module.APP_READY_SELECTOR
    assert "[data-testid='stAppViewContainer']" in module.APP_READY_SELECTOR
    assert "section.main" in module.APP_READY_SELECTOR
