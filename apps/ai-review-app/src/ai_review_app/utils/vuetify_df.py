"""DataFrame Vuetify uitilities for AI Review Dashboard."""

import pandas as pd


def df_headers(df: pd.DataFrame):
    """Return headers for rv.DataTable from pd.DataFrame."""
    headers_ = [
        {"text": col, "value": col, "align": "left"} for col in df.columns.to_list()
    ]
    return headers_


def df_items(df: pd.DataFrame):
    """Return items for rv.DataTable from pd.DataFrame."""
    items_ = df.to_dict("records")
    return items_
