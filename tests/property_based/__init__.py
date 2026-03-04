"""Hypothesis property-based tests for the Streamlit Dividend Dashboard.

Covers DividendCalculator, color utilities, ColorManager, and a stateful
RuleBasedStateMachine for the color-cycling mechanism.

Note:
    Tests here require an explicit ``@pytest.mark.property`` decorator —
    unlike ``unit/`` and ``integration/``, this package is not auto-marked
    by ``conftest.pytest_collection_modifyitems``.

Example:
    Run all property tests::

        poetry run pytest tests/property_based/ -v -m property
"""
