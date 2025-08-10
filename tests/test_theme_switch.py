from __future__ import annotations
from ui.theme_manager import build_stylesheet


def test_stylesheet_light_contains_core_tokens():
    css = build_stylesheet(False)
    assert "background: #FFFFFF" in css
    assert "min-height: 44px" in css


def test_stylesheet_dark_contains_core_tokens():
    css = build_stylesheet(True)
    assert "background: #0B0B0C" in css
    assert "min-height: 44px" in css