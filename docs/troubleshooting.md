# Troubleshooting Guide

This document contains common errors encountered during development and their solutions.

## Error 1: Incorrect color of sliders and selection windows

**Problem**: The primary color was displayed incorrectly throughout the entire application - it was supposed to be purple but appeared red.

**Cause**: Error in local Streamlit configuration.

**Solution**: Opening the Streamlit application in a different browser (e.g., Mozilla Firefox) resolved the color issue.

**Additional notes**: 
- The problem may be related to browser cache
- It's recommended to test the application in different browsers during development
- You can also try clearing the browser cache before switching browsers
- Make sure that `.streamlit/config.toml` color settings are consistent with `app_config.py` configuration to avoid styling conflicts

---

*This document will be updated with additional encountered errors and their solutions.*
