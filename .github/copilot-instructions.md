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
| Dependency manager | Poetry + pyproject.toml | poetry-core `>=2.0.0` |

**Python version notes:**
- Python 3.12+ is required. Use built-in generic annotations (`list[str]`, `dict[str, int]`, `str | None`) — never `from __future__ import annotations` or `typing.List`, `typing.Dict`, `typing.Optional`.
- `streamlit-elements` is the **only** dependency for Nivo.js; it is used exclusively in `components/nivo_pie_chart.py`.

---

## File Responsibilities

| File | Role |
|---|---|
| `main.py` | Orchestrates every UI section; owns `DividendApp`; calls all components |
| `app_config.py` | Single source of truth for every constant, default, and theme color |
| `data_processor.py` | Reads and sanitises the TSV; exposes `filter_data(selected_tickers)` |
| `components/drip_calculator.py` | Encapsulated DRIP UI: inputs → simulation → metric cards → subplot chart |
| `components/nivo_pie_chart.py` | Encapsulated Nivo.js donut: receives data + colors, renders via streamlit-elements |
| `utils/color_manager.py` | All color math: Pastel palette assignment, WCAG contrast, gradient generation |
| `utils/dividend_calculator.py` | Pure calculation: CAGR projections, growth info, currency symbol inference |
| `styles/colors_and_styles.py` | `BASE_COLORS` palette list + `CSS_STYLES` multi-line HTML `<style>` block |
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
- All magic numbers, default values, colors, and file paths belong in `app_config.py`.
- Never define constants inline in `main.py` or any component file.
- `COLOR_THEME["primary"]` is `#8A2BE2` (purple) — used for milestones and accents.

### CSS and styling
- All CSS lives exclusively in `styles/colors_and_styles.py` inside the `CSS_STYLES` string.
- Inject CSS once per app run via `st.markdown(CSS_STYLES, unsafe_allow_html=True)`.
- Never write `<style>` blocks inside component files.
- CSS uses `clamp()`-based fluid typography and CSS custom properties.
- All interactive elements must meet WCAG AAA minimum 44×44 px touch targets.
- Always include `@media (prefers-reduced-motion: reduce)` blocks for animated elements.

### Color management
- Always go through `ColorManager` — never import `px.colors` directly in components.
- `ColorManager.generate_colors_for_tickers()` assigns Plotly Pastel colors in sorted ticker order. Call it once after filtering.
- Use `hex_to_rgba(hex, alpha)` for Plotly fill transparency; use `rgb_to_hex(rgb)` when Nivo.js requires hex.
- Use `apply_wcag_ui_standards(color)` to choose `#000000` vs `#FFFFFF` text on dynamic backgrounds.

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
| Inline CSS inside component files | Extend `CSS_STYLES` in `styles/colors_and_styles.py` |
| Constants defined in `main.py` | Add to `app_config.py` |
| `st.*` calls inside `DividendCalculator` | Pure logic only; call Streamlit in `main.py` or components |
| `px.colors` imported directly in a component | Use `ColorManager.generate_colors_for_tickers()` |
| Hardcoded currency symbols like `"$"` | Use `DividendCalculator.get_currency_symbol(ticker)` |
| `typing.List`, `typing.Optional`, `typing.Dict` | Use `list[str]`, `str | None`, `dict[str, int]` (Python 3.12+) |
| `from __future__ import annotations` | Not needed on Python 3.12+ |
| Adding logic directly to `utils/__init__.py` | Keep it as a package marker only |

---

## Extension Patterns

| Task | Where to act |
|---|---|
| New constant or default | `app_config.py` only |
| New chart section | Add `_render_<section>(self)` to `DividendApp` in `main.py`; call from `run()` |
| New component | `components/<name>.py`; constructor takes `ticker_colors: dict[str, str]`; exposes `.render()` |
| New CSS | Extend `CSS_STYLES` in `styles/colors_and_styles.py` |
| New CSV column | Add to `REQUIRED_COLUMNS`; add strip logic in `_clean_dataframe()`; include in `filter_data()` |
| New ticker country | Add suffix → currency entry in `DividendCalculator.get_currency_symbol()` |
