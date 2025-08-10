from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ThemeTokens:
    # Light
    bg_light: str = "#FFFFFF"
    surface_light: str = "#F7F7F9"
    text_primary_light: str = "#111114"
    text_secondary_light: str = "rgba(17,17,20,0.70)"
    text_tertiary_light: str = "rgba(17,17,20,0.50)"
    divider_light: str = "rgba(60,60,67,0.29)"
    accent_light: str = "#007AFF"
    error_light: str = "#FF3B30"

    # Dark
    bg_dark: str = "#0B0B0C"
    surface_dark: str = "#151517"
    text_primary_dark: str = "#F5F6F7"
    text_secondary_dark: str = "rgba(245,246,247,0.70)"
    text_tertiary_dark: str = "rgba(245,246,247,0.50)"
    divider_dark: str = "rgba(84,84,88,0.60)"
    accent_dark: str = "#0A84FF"
    error_dark: str = "#FF453A"


def build_stylesheet(dark: bool, tokens: ThemeTokens = ThemeTokens()) -> str:
    """
    Build a CSS stylesheet string for the application based on the theme tokens.
    """
    if not dark:
        bg = tokens.bg_light
        surface = tokens.surface_light
        text = tokens.text_primary_light
        text2 = tokens.text_secondary_light
        text3 = tokens.text_tertiary_light
        divider = tokens.divider_light
        accent = tokens.accent_light
        error = tokens.error_light
    else:
        bg = tokens.bg_dark
        surface = tokens.surface_dark
        text = tokens.text_primary_dark
        text2 = tokens.text_secondary_dark
        text3 = tokens.text_tertiary_dark
        divider = tokens.divider_dark
        accent = tokens.accent_dark
        error = tokens.error_dark
    return f"""
    QWidget {{
        background: {bg};
        color: {text};
        font-family: "SF Pro Text", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 17px;
    }}
    QLabel#page-title {{
        font-family: "SF Pro Display", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 34px;
        font-weight: 600;
        padding: 8px 0 16px 0;
    }}
    QFrame, .Card {{
        background: {surface};
        border: 1px solid {divider};
        border-radius: 12px;
    }}
    QPushButton {{
        background: transparent;
        border: 1px solid {divider};
        border-radius: 10px;
        padding: 10px 14px;
        min-height: 44px;
        color: {text};
    }}
    QPushButton:hover {{
        background: {surface};
    }}
    QPushButton:pressed {{
        transform: scale(0.95);
    }}
    QCheckBox {{
        padding: 8px;
        color: {text};
    }}
    QLineEdit, QTextEdit {{
        background: {surface};
        border: 1px solid {divider};
        border-radius: 10px;
        padding: 10px;
        color: {text};
    }}
    .text-secondary {{ color: {text2}; }}
    .text-tertiary {{ color: {text3}; }}
    .accent {{ color: {accent}; }}
    .error {{ color: {error}; }}
    """