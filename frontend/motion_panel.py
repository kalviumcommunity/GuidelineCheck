"""Safe loader for the guideline_motion_panel custom Streamlit component.

If the component cannot be loaded or built (e.g. Node/npm dependencies were
never installed), the rest of the app must still work using plain static
Streamlit rendering. Callers should check `MOTION_PANEL_AVAILABLE` and fall
back to `styles.py` helpers when False.
"""
from __future__ import annotations

import os
from pathlib import Path

MOTION_PANEL_AVAILABLE = False
_component_func = None

_COMPONENT_DIR = Path(__file__).resolve().parents[1] / "frontend_components" / "guideline_motion_panel"
_BUILD_DIR = _COMPONENT_DIR / "dist"

try:
    import streamlit.components.v1 as components

    if _BUILD_DIR.exists() and (_BUILD_DIR / "index.html").exists():
        _component_func = components.declare_component(
            "guideline_motion_panel", path=str(_BUILD_DIR)
        )
        MOTION_PANEL_AVAILABLE = True
except Exception:  # noqa: BLE001 - any failure here must not crash the app
    MOTION_PANEL_AVAILABLE = False
    _component_func = None


def render_motion_panel(payload: dict, key: str | None = None, height: int = 400):
    """Render the Framer Motion panel if available; caller must have already
    checked MOTION_PANEL_AVAILABLE and provide a static fallback otherwise."""
    if not MOTION_PANEL_AVAILABLE or _component_func is None:
        raise RuntimeError("guideline_motion_panel component is not available")
    return _component_func(payload=payload, key=key, height=height, default=None)
