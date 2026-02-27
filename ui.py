"""
UI utility functions for InVesta application.
Provides reusable UI components and helpers.
"""

from typing import Dict
import streamlit as st


def display_metric_cards(metrics: Dict[str, float]) -> None:
    """Display key metrics as cards."""
    col1, col2, col3, col4 = st.columns(4)
    metric_cols = [col1, col2, col3, col4]

    for idx, (metric_name, metric_value) in enumerate(metrics.items()):
        if idx < len(metric_cols):
            with metric_cols[idx]:
                st.metric(metric_name, f"${metric_value:,.2f}")


def display_empty_state(message: str) -> None:
    """Display an empty state message."""
    st.info(message)


def display_confirmation_message(message: str, message_type: str = "success") -> None:
    """Display a confirmation or status message."""
    if message_type == "success":
        st.success(message)
    elif message_type == "warning":
        st.warning(message)
    elif message_type == "error":
        st.error(message)
