# Troubleshooting guide

Use this guide to diagnose and resolve known issues with the Streamlit
Dividend Dashboard.

## Sliders and selection windows show the wrong primary color

**Symptom**: The primary color appears red throughout the app instead of
purple.

**Cause**: A stale browser cache overrides the configured Streamlit theme.

**Resolution**: Open the app in a different browser (for example, Firefox).
If the correct purple color appears, clear the cache in your original browser
and reload.

**Additional notes**:

- We recommend testing the app in more than one browser during development.
- Verify that the `primaryColor` in `.streamlit/config.toml` matches the
  `COLOR_THEME["primary"]` value (`#8A2BE2`) in `app/app_config.py` to
  prevent styling conflicts.
