# GitHub Copilot — Project Instructions

> Automatically injected into every Copilot Chat session and all custom agents.
> Agent-specific behavioral rules live in `.github/agents/*.agent.md` — do NOT duplicate them here.
> Always use English in all code, comments, docstrings, commit messages, and documentation.

---

## Project Overview

**Streamlit Dividend Dashboard** is a single-page personal finance web application for dividend portfolio analysis.

The app allows a user to:
- View a portfolio overview as gradient HTML tiles (one tile per ticker)
- Explore dividend distribution via an interactive Nivo.js donut chart
- Project future dividend income using compound annual growth rate (CAGR)
- Simulate a DRIP (Dividend Reinvestment Plan) with full year-by-year compound simulation

The data source is a local TSV file (`data/dividend_data.csv`) representing a personal portfolio. The app is not connected to any external API.

---

## Tech Stack

| Layer | Technology | Version constraint |
|---|---|---|
| Language | Python | `>=3.12` |
| Web framework | Streamlit | `>=1.51.0,<2` |
| Data processing | pandas | `>=2.2.3,<3` |
| Charts | Plotly (express + graph_objects) | `>=5.24.1,<6` |
| Interactive chart | streamlit-elements (Nivo.js + MUI) | `>=0.1.0,<0.2.0` |
| Settings / env | pydantic-settings | `>=2.0.0,<3` |
| Dependency manager | Poetry + pyproject.toml | poetry-core `>=2.0.0` |

**Dev dependencies (in `[dependency-groups].dev`):** `pytest`, `pytest-cov`, `pytest-mock`, `pytest-asyncio`, `pytest-xdist`, `hypothesis`, `freezegun`, `pytest-benchmark`, `mypy`, `ruff`.

**Python version notes:**
- Python 3.12+ is required. Use built-in generic annotations (`list[str]`, `dict[str, int]`, `str | None`) — never `from __future__ import annotations` or `typing.List`, `typing.Dict`, `typing.Optional`.
- `streamlit-elements` is the **only** dependency for Nivo.js; it is used exclusively in `app/components/nivo_pie_chart.py`.

---

## Project Layout

All application source code lives inside the `app/` package. `main.py` orchestrates the app from the project root.

```
Streamlit-Dividend-Dashboard/
├── main.py                          # Entry point; owns DividendApp
├── pyproject.toml
├── data/dividend_data.csv
├── tests/
│   ├── conftest.py
│   └── unit/
│       ├── test_app_config.py
│       ├── test_color_manager.py
│       ├── test_data_processor.py
│       └── test_dividend_calculator.py
└── app/
    ├── app_config.py                # Constants imported by main.py
    ├── data_processor.py            # DividendDataProcessor (primary)
    ├── config/
    │   ├── app_config.py            # Mirror of app/app_config.py
    │   └── settings.py              # Pydantic-settings Settings class
    ├── components/
    │   ├── drip_calculator.py
    │   └── nivo_pie_chart.py
    ├── styles/
    │   └── colors_and_styles.py
    └── utils/
        ├── color_manager.py
        ├── data_processor.py        # Mirror of app/data_processor.py
        └── dividend_calculator.py
```

## File Responsibilities

| File | Role |
|---|---|
| `main.py` | Orchestrates every UI section; owns `DividendApp`; calls all components |
| `app/app_config.py` | Single source of truth for every constant, default, and theme color (imported by `main.py`) |
| `app/config/app_config.py` | Mirror of `app/app_config.py`; used by `app/config/settings.py` |
| `app/config/settings.py` | `Settings` (pydantic-settings `BaseSettings`): loads env vars / `.env` file; exposes `settings` singleton |
| `app/data_processor.py` | Reads and sanitises the TSV; exposes `filter_data(selected_tickers)` |
| `app/utils/data_processor.py` | Mirror of `app/data_processor.py` (kept for internal package imports) |
| `app/components/drip_calculator.py` | Encapsulated DRIP UI: inputs → simulation → metric cards → subplot chart |
| `app/components/nivo_pie_chart.py` | Encapsulated Nivo.js donut: receives data + colors, renders via streamlit-elements |
| `app/utils/color_manager.py` | Module-level color utilities + `ColorManager` class: Pastel palette assignment, WCAG contrast, gradient generation, tile HTML |
| `app/utils/dividend_calculator.py` | Pure calculation: CAGR projections, growth info, currency symbol inference |
| `app/styles/colors_and_styles.py` | `BASE_COLORS` palette list + `CSS_STYLES` multi-line HTML `<style>` block |
| `data/dividend_data.csv` | Tab-separated portfolio data; values include `" USD"` and `"%"` suffixes |

---

## Ticker Format

Tickers follow the `SYMBOL.COUNTRY` convention:

| Suffix | Currency |
|---|---|
| `.US` | `$` (USD) |
| `.PL` | `PLN` |
| `.EU` | `€` (EUR) |
| *(no dot)* | `$` (USD) |

Currency is **always** inferred from the ticker suffix via `DividendCalculator.get_currency_symbol(ticker)`. Never hardcode a currency symbol.

---

## Coding Conventions

### Constants and configuration
- All magic numbers, default values, colors, and file paths belong in `app/app_config.py`.
- Never define constants inline in `main.py` or any component file.
- `COLOR_THEME["primary"]` is `#8A2BE2` (purple) — used for milestones and accents.
- Environment-specific overrides (file path, debug flag, environment name) go in `app/config/settings.py` via the `Settings` class and `.env` file — never as hardcoded constants.

### CSS and styling
- All CSS lives exclusively in `app/styles/colors_and_styles.py` inside the `CSS_STYLES` string.
- Inject CSS once per app run via `st.markdown(CSS_STYLES, unsafe_allow_html=True)`.
- Never write `<style>` blocks inside component files.
- CSS uses `clamp()`-based fluid typography and CSS custom properties.
- All interactive elements must meet WCAG AAA minimum 44×44 px touch targets.
- Always include `@media (prefers-reduced-motion: reduce)` blocks for animated elements.

### Color management
- Always go through `ColorManager` — never import `px.colors` directly in components.
- `ColorManager.generate_colors_for_tickers()` assigns Plotly Pastel colors in sorted ticker order. Call it once after filtering.
- `ColorManager.create_tile_html(ticker, shares)` builds the gradient HTML tile for the portfolio overview.
- Module-level helpers in `app/utils/color_manager.py` (import directly when needed):
  - `hex_to_rgba(hex, alpha)` — Plotly fill transparency.
  - `rgb_to_hex(rgb)` — convert rgb string to hex for Nivo.js.
  - `adjust_gradient(color)` — lightens a color for gradient endpoints.
  - `apply_wcag_ui_standards(color) -> bool` — returns `True` if the color is perceived as **light** (luminance > 0.5).
  - `determine_text_color_for_dropdown(bg_color) -> str` — returns `"#000000"` or `"#FFFFFF"` based on background luminance; use this (not `apply_wcag_ui_standards`) when you need a ready-to-use text color string.

### Calculation logic
- `DividendCalculator` is a pure utility class — all methods are `@staticmethod`, no `st.*` calls allowed.

### Components
- Components receive only `ticker_colors: dict[str, str]` — they are fully self-contained.
- Component files must not import from `main.py`.
- Each component exposes a single `.render()` method as its public API.

### Data processing
- Input file is always TSV (`sep="\t"`). Do not change the separator.
- `Net Dividend` values in the CSV include a `" USD"` suffix — stripped by `_clean_dataframe()`.
- `Tax Collected` values include a `"%"` suffix — also stripped by `_clean_dataframe()`.
- Required columns: `['Ticker', 'Net Dividend', 'Tax Collected', 'Shares']`. Raise `ValueError` if any are missing.

### Error handling
- Data loading errors: `st.error(message)` followed by `st.stop()`.
- Numeric conversion: always use `pd.to_numeric(errors="coerce")` — never `float()` directly on raw strings.

---

## Anti-patterns — Never Do These

| Anti-pattern | Correct approach |
|---|---|
| Inline CSS inside component files | Extend `CSS_STYLES` in `app/styles/colors_and_styles.py` |
| Constants defined in `main.py` | Add to `app/app_config.py` |
| `st.*` calls inside `DividendCalculator` | Pure logic only; call Streamlit in `main.py` or components |
| `px.colors` imported directly in a component | Use `ColorManager.generate_colors_for_tickers()` |
| Hardcoded currency symbols like `"$"` | Use `DividendCalculator.get_currency_symbol(ticker)` |
| Using `apply_wcag_ui_standards()` as a text color string | It returns `bool`; use `determine_text_color_for_dropdown()` for a CSS color string |
| Environment-specific values hardcoded in source | Use `app/config/settings.py` + `.env` file |
| `typing.List`, `typing.Optional`, `typing.Dict` | Use `list[str]`, `str | None`, `dict[str, int]` (Python 3.12+) |
| `from __future__ import annotations` | Not needed on Python 3.12+ |
| Adding logic directly to `utils/__init__.py` | Keep it as a package marker only |

---

## Extension Patterns

| Task | Where to act |
|---|---|
| New constant or default | `app/app_config.py` only |
| New env-overridable setting | Add field to `Settings` in `app/config/settings.py`; back it with a constant from `app/config/app_config.py` |
| New chart section | Add `_render_<section>(self)` to `DividendApp` in `main.py`; call from `run()` |
| New component | `app/components/<name>.py`; constructor takes `ticker_colors: dict[str, str]`; exposes `.render()` |
| New CSS | Extend `CSS_STYLES` in `app/styles/colors_and_styles.py` |
| New CSV column | Add to `REQUIRED_COLUMNS`; add strip logic in `_clean_dataframe()`; include in `filter_data()` |
| New ticker country | Add suffix → currency entry in `DividendCalculator.get_currency_symbol()` |
