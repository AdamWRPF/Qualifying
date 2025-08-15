# app.py
import os
import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="WRPF UK — Qualifying Totals", layout="wide")

# -------------------- Helpers --------------------
def load_qualifying_table(file_path_or_obj) -> pd.DataFrame:
    """
    Accepts:
      - Excel with 'Men' and 'Women' sheets (like FP.xlsx), or
      - CSV with header style: Age Category, Sex, Event, Tested, Equipment, then weight classes as columns.
    Returns tidy DataFrame:
      ['Age Category','Sex','Event','Tested','Equipment','WeightClassKg','QualifyingTotalKg']
    """
    name = ""
    if isinstance(file_path_or_obj, (io.BytesIO, io.StringIO)) or hasattr(file_path_or_obj, "read"):
        name = getattr(file_path_or_obj, "name", "").lower()
    else:
        name = str(file_path_or_obj).lower()

    if name.endswith((".xlsx", ".xls")) or (isinstance(file_path_or_obj, str) and os.path.exists(file_path_or_obj)):
        xls = pd.ExcelFile(file_path_or_obj)
        frames = [pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names]
        wide = pd.concat(frames, ignore_index=True)
    elif name.endswith(".csv"):
        wide = pd.read_csv(file_path_or_obj)
    else:
        raise ValueError("Unsupported file type or file not found.")

    base_cols = {"Age Category", "Sex", "Event", "Tested", "Equipment"}
    weight_cols = [c for c in wide.columns if c not in base_cols]

    long_df = wide.melt(
        id_vars=["Age Category", "Sex", "Event", "Tested", "Equipment"],
        value_vars=weight_cols,
        var_name="WeightClassKg",
        value_name="QualifyingTotalKg",
    )

    # Cleanup
    for c in ["Age Category", "Sex", "Event", "Tested", "Equipment", "WeightClassKg"]:
        long_df[c] = long_df[c].astype(str).str.strip()
    long_df = long_df[~long_df["QualifyingTotalKg"].isna()]

    # Normalise Tested column variants
    tested_map = {
        "yes": "Tested", "true": "Tested", "tested": "Tested",
        "no": "Untested", "false": "Untested", "untested": "Untested",
    }
    long_df["Tested"] = long_df["Tested"].str.lower().map(tested_map).fillna(long_df["Tested"])

    return long_df


def numeric_sort_key_wc(x: str):
    s = str(x)
    try:
        return (float(s.replace("+", "")), s)
    except ValueError:
        return (float("inf"), s)


def reset_filters():
    # DO NOT call st.rerun() here; Streamlit will rerun automatically after button click.
    for key in ["search", "gender", "ages", "wcs", "equipment", "tested_state"]:
        if key in st.session_state:
            del st.session_state[key]


def filter_with_controls(df: pd.DataFrame) -> pd.DataFrame:
    """Apply horizontal filter bar controls unless search is present (search overrides all filters)."""
    search = st.session_state.get("search", "").strip()
    if search:
        s = search.lower()
        mask = (
            df["Sex"].str.lower().str.contains(s)
            | df["Age Category"].str.lower().str.contains(s)
            | df["Event"].str.lower().str.contains(s)
            | df["Tested"].str.lower().str.contains(s)
            | df["Equipment"].str.lower().str.contains(s)
            | df["WeightClassKg"].str.lower().str.contains(s)
        )
        return df[mask]

    gender = st.session_state.get("gender") or []
    ages = st.session_state.get("ages") or []
    wcs = st.session_state.get("wcs") or []
    equipment = st.session_state.get("equipment") or []
    tested_state = st.session_state.get("tested_state", "All")

    out = df.copy()
    if gender:
        out = out[out["Sex"].isin(gender)]
    if ages:
        out = out[out["Age Category"].isin(ages)]
    if wcs:
        out = out[out["WeightClassKg"].isin(wcs)]
    if equipment:
        out = out[out["Equipment"].isin(equipment)]
    if tested_state == "Tested":
        out = out[out["Tested"].str.lower() == "tested"]
    elif tested_state == "Untested":
        out = out[out["Tested"].str.lower() == "untested"]
    return out


def show_table(df: pd.DataFrame, title: str):
    st.markdown(f"### {title}")
    display_cols = [
        "Sex", "Age Category", "Event", "Tested", "Equipment", "WeightClassKg", "QualifyingTotalKg",
    ]
    view_to_show = (
        df[display_cols]
        .sort_values(by=["Sex","Age Category","Event","Tested","Equipment","WeightClassKg"], kind="mergesort")
    )

    st.dataframe(view_to_show, use_container_width=True, hide_index=True)

    csv_bytes = view_to_show.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Download {title} (CSV)",
        data=csv_bytes,
        file_name=f"qualifying_totals_{title.replace(' ', '_').lower()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Rows", len(view_to_show))
    with c2:
        st.metric("Weight classes", view_to_show["WeightClassKg"].nunique())
    with c3:
        st.metric("Age groups", view_to_show["Age Category"].nunique())


# -------------------- Header --------------------
st.title("WRPF UK — Qualifying Totals")
st.caption("This dashboard reads FP.xlsx from the working directory. Search overrides all filters. Reset clears everything.")

# -------------------- Data Load --------------------
DEFAULT_FILE = "FP.xlsx"
if not os.path.exists(DEFAULT_FILE):
    st.error(
        "Missing **FP.xlsx** in the current folder. "
        "Place your qualifying totals workbook (with ‘Men’ and ‘Women’ sheets) next to `app.py` and reload."
    )
    st.stop()

try:
    data = load_qualifying_table(DEFAULT_FILE)
except Exception as e:
    st.error(f"Could not read FP.xlsx. Please check the format. Details: {e}")
    st.stop()

# -------------------- Build filter choices --------------------
ages = sorted(data["Age Category"].dropna().unique().tolist())
wcs = sorted(data["WeightClassKg"].dropna().unique().tolist(), key=numeric_sort_key_wc)
eqs = sorted(data["Equipment"].dropna().unique().tolist())

if "tested_state" not in st.session_state:
    st.session_state["tested_state"] = "All"

# -------------------- Horizontal Filter Bar --------------------
# Layout across the page in a single row
f1, f2, f3, f4, f5, f6, f7 = st.columns([2.4, 1.2, 1.8, 2.0, 1.8, 1.4, 1.0])

with f1:
    st.text_input("Search (overrides filters)", key="search", placeholder="e.g., 24-39, SBD, Tested, 90, Female")

with f2:
    st.multiselect("Gender", options=["Male", "Female"], key="gender")

with f3:
    st.multiselect("Age Category", options=ages, key="ages")

with f4:
    st.multiselect("Weight Class (Kg)", options=wcs, key="wcs")

with f5:
    st.multiselect("Equipment", options=eqs, key="equipment")

with f6:
    st.selectbox("Tested", options=["All", "Tested", "Untested"], key="tested_state")

with f7:
    st.button("Reset", on_click=reset_filters)

st.markdown("---")

# -------------------- Tabs --------------------
tab_sbd, tab_singles = st.tabs(["Full Power (SBD)", "Single Lifts (B & D)"])

with tab_sbd:
    sbd_df = data[data["Event"] == "SBD"]
    sbd_view = filter_with_controls(sbd_df)
    show_table(sbd_view, "Full Power (SBD)")

with tab_singles:
    singles_df = data[data["Event"].isin(["B", "D"])]
    singles_view = filter_with_controls(singles_df)
    show_table(singles_view, "Single Lifts (B & D)")
