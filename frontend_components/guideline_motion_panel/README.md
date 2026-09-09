# guideline_motion_panel

A React + TypeScript + Framer Motion custom Streamlit component used by the GuidelineCheck
frontend to add subtle, accessible animations on top of the answer/citation display:

- Animated Current / Superseded / Historical / Draft status badges
- Expand/collapse transitions on source cards
- Soft fade-and-slide entrance for the answer and guidance-status banner
- An animated confidence indicator bar
- Respects `prefers-reduced-motion` (disables motion, not content)

## A prebuilt `dist/` is included

The repository ships with `dist/` already built, so the Streamlit app can use the enhanced
motion UI immediately without requiring Node/npm. You only need to rebuild if you modify the
component source.

## Rebuilding

```bash
cd frontend_components/guideline_motion_panel
npm install
npm run build
```

This regenerates `dist/`, which `frontend/motion_panel.py` loads automatically the next time
Streamlit starts.

## Development mode

```bash
npm run dev
```

Runs a Vite dev server for iterating on the component in isolation (outside of Streamlit).

## Graceful fallback

If `dist/index.html` is missing or fails to load for any reason, `frontend/motion_panel.py`
sets `MOTION_PANEL_AVAILABLE = False` and the main Streamlit app (`frontend/app.py`) falls back
to plain static Streamlit rendering (`frontend/styles.py`) for status badges, source cards, and
the guidance banner — no functionality is lost, only the animation polish.
