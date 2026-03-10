# GitHub Copilot — Project Instructions

> Injected into every Copilot Chat session and all custom agents.
> Agent rules live in `.github/agents/*.agent.md` — do NOT duplicate them here.
> Always use English in all code, comments, docstrings, commit messages, and documentation.

---

## Project Overview

**Streamlit Dividend Dashboard** is a single-page personal finance web app for dividend portfolio analysis. It displays gradient portfolio tiles, an interactive Nivo.js donut chart, CAGR income projections, and a full DRIP simulation. Data source: `data/dividend_data.csv` (local TSV, no external API).

---

## Tech Stack

> **Versions:** `pyproject.toml` is the single source of truth — never duplicate version constraints here.

| Layer | Technology |
|---|---|
| Language | Python — code style targets **3.12+** (Ruff `target-version = "py312"`) |
| Web framework | Streamlit |
| Data processing | pandas |
| Charts | Plotly (express + graph_objects) |
| Interactive chart | streamlit-elements (Nivo.js + MUI) — used **only** in `app/components/nivo_pie_chart.py` |
| Settings / env | pydantic-settings |
| Dependency manager | Poetry + `pyproject.toml` |

Dev deps: `pytest`, `pytest-cov`, `pytest-mock`, `pytest-asyncio`, `pytest-xdist`, `hypothesis`, `freezegun`, `pytest-benchmark`, `mypy`, `ruff`.

---

## Project Layout

`main.py` at the root orchestrates the app; all source lives in `app/`.

| File | Role |
|---|---|
| `main.py` | Entry point; owns `DividendApp`; calls all components |
| `app/app_config.py` | Single source of truth for every constant, default, and theme color |
| `app/config/settings.py` | `Settings` (pydantic-settings): loads env vars / `.env`; exposes `settings` singleton |
| `app/data_processor.py` | Reads and sanitises the TSV; exposes `filter_data(selected_tickers)` |
| `app/components/drip_calculator.py` | DRIP UI: inputs → simulation → metric cards → subplot chart |
| `app/components/nivo_pie_chart.py` | Nivo.js donut chart via streamlit-elements |
| `app/utils/color_manager.py` | `ColorManager` class + module helpers: Pastel palette, WCAG contrast, gradient, tile HTML |
| `app/utils/dividend_calculator.py` | Pure CAGR / growth / currency calculations; no `st.*` calls |
| `app/styles/colors_and_styles.py` | `BASE_COLORS` palette + `CSS_STYLES` `<style>` block |

---

## Coding Conventions

### Constants and configuration
- All magic numbers, defaults, colors, and file paths → `app/app_config.py` only.
- `COLOR_THEME["primary"]` is `#8A2BE2` (purple) — milestones and accents.
- Env-specific overrides (file path, debug, environment) → `app/config/settings.py` + `.env` file.

### Python style (3.12+)
- Built-in generics: `list[str]`, `dict[str, int]`, `str | None`. Never `typing.List`, `typing.Optional`, `typing.Dict`, or `from __future__ import annotations`.

### CSS and styling
- All CSS → `app/styles/colors_and_styles.py` (`CSS_STYLES`). Never `<style>` blocks in component files.
- Inject once: `st.markdown(CSS_STYLES, unsafe_allow_html=True)`.
- `clamp()`-based fluid typography, CSS custom properties, WCAG AAA 44×44 px touch targets.
- Always include `@media (prefers-reduced-motion: reduce)` for animated elements.

### Color management
- Always use `ColorManager` — never `px.colors` directly. Call `generate_colors_for_tickers()` once after filtering.
- `ColorManager.create_tile_html(ticker, shares)` builds the gradient HTML tile.
- Module helpers (`app/utils/color_manager.py`): `hex_to_rgba`, `rgb_to_hex`, `adjust_gradient`, `apply_wcag_ui_standards(color) -> bool` (luminance > 0.5 = light), `determine_text_color_for_dropdown(bg_color) -> str` (returns `"#000000"` or `"#FFFFFF"` — use this for CSS color strings, not `apply_wcag_ui_standards`).

### Ticker format & currency
- `SYMBOL.COUNTRY` convention: `.US` → `$`, `.PL` → `PLN`, `.EU` → `€`, no dot → `$`.
- Always infer currency via `DividendCalculator.get_currency_symbol(ticker)`. Never hardcode.

### Data processing
- TSV only (`sep="\t"`). Required columns: `['Ticker', 'Net Dividend', 'Tax Collected', 'Shares']`; raise `ValueError` if missing.
- `Net Dividend` has `" USD"` suffix; `Tax Collected` has `"%"` suffix — both stripped in `_clean_dataframe()`.
- Numeric conversion: `pd.to_numeric(errors="coerce")` — never `float()` on raw strings.
- Data errors: `st.error(message)` then `st.stop()`.

### Components
- Constructor: `ticker_colors: dict[str, str]`. Public API: single `.render()` method.
- Must not import from `main.py`. `DividendCalculator` must not call `st.*`.

---

## Anti-patterns

| Anti-pattern | Correct approach |
|---|---|
| Inline CSS in component files | Extend `CSS_STYLES` in `app/styles/colors_and_styles.py` |
| Constants in `main.py` | Add to `app/app_config.py` |
| `st.*` calls in `DividendCalculator` | Pure logic only |
| `px.colors` directly in a component | Use `ColorManager.generate_colors_for_tickers()` |
| Hardcoded `"$"` or any currency string | Use `DividendCalculator.get_currency_symbol(ticker)` |
| `apply_wcag_ui_standards()` used as a CSS color | It returns `bool`; use `determine_text_color_for_dropdown()` |
| Env-specific values hardcoded in source | Use `app/config/settings.py` + `.env` file |
| Version constraints written in instructions | `pyproject.toml` (Poetry) is the single source of truth for all versions |
| `typing.List` / `typing.Optional` / `from __future__ import annotations` | Use built-in generics: `list[str]`, `str | None` (Python 3.12+) |
| Logic added directly to `utils/__init__.py` | Keep it as a package marker only |

---

## Extension Patterns

| Task | Where to act |
|---|---|
| New constant or default | `app/app_config.py` only |
| New env-overridable setting | `Settings` in `app/config/settings.py`; backed by `app/config/app_config.py` constant |
| New chart section | `_render_<section>(self)` in `DividendApp`; call from `run()` |
| New component | `app/components/<name>.py`; takes `ticker_colors: dict[str, str]`; exposes `.render()` |
| New CSS | Extend `CSS_STYLES` in `app/styles/colors_and_styles.py` |
| New CSV column | Add to `REQUIRED_COLUMNS`; strip in `_clean_dataframe()`; include in `filter_data()` |
| New ticker country | Add suffix → currency in `DividendCalculator.get_currency_symbol()` |
