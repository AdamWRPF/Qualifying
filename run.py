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
    for key in ["gender", "ages", "wcs_male", "wcs_female", "equipment", "tested_state"]:
        if key in st.session_state:
            del st.session_state[key]


def filter_with_controls(df: pd.DataFrame) -> pd.DataFrame:
    """Apply horizontal filter bar controls (no search override)."""
    gender = st.session_state.get("gender") or []
    ages = st.session_state.get("ages") or []
    wcs_male = st.session_state.get("wcs_male") or []
    wcs_female = st.session_state.get("wcs_female") or []
    equipment = st.session_state.get("equipment") or []
    tested_state = st.session_state.get("tested_state", "All")

    out = df.copy()

    # Sex filter first
    if gender:
        out = out[out["Sex"].isin(gender)]

    # Age filter
    if ages:
        out = out[out["Age Category"].isin(ages)]

    # Weight class logic (separate by sex)
    if gender == ["Female"]:
        if wcs_female:
            out = out[out["WeightClassKg"].isin(wcs_female)]
    elif gender == ["Male"]:
        if wcs_male:
            out = out[out["WeightClassKg"].isin(wcs_male)]
    else:
        # both or none selected → allow union of both selections if any chosen
        combined = list(set(wcs_male) | set(wcs_female))
        if combined:
            out = out[out["WeightClassKg"].isin(combined)]

    # Equipment
    if equipment:
        out = out[out["Equipment"].isin(equipment)]

    # Tested/Untested
    if tested_state == "Tested":
        out = out[out["Tested"].str.lower() == "tested"]
    elif tested_state == "Untested":
        out = out[out["Tested"].str.lower() == "untested"]

    return out


def show_table(df: pd.DataFrame, title: str):
    st.markdown(f"### {title}")
    # Polished table look via light CSS (no theme forcing)
    st.markdown("""
    <style>
    /* make dataframe headers sticky and add subtle borders/striping */
    .stDataFrame [data-testid="stHeader"] { position: sticky; top: 0; z-index: 1; }
    .stDataFrame [role="gridcell"] { border-bottom: 1px solid rgba(0,0,0,0.05); }
    .stDataFrame tbody tr:nth-child(even) [role="gridcell"] { background: rgba(0,0,0,0.02); }
    .stDataFrame th div p { font-weight: 700; letter-spacing: .2px; }
    </style>
    """, unsafe_allow_html=True)

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


# -------------------- Header + Top Links --------------------
st.title("WRPF UK — Qualifying Totals")

# Link buttons row
st.markdown("""
<style>
.linkbar { display:flex; gap:.5rem; flex-wrap:wrap; margin: .25rem 0 1rem; }
.linkbar a {
  text-decoration:none; padding:.6rem .9rem; border-radius:.6rem; border:1px solid rgba(0,0,0,.12);
  font-weight:600; display:inline-block;
}
.link-primary  { background:#e0232e; color:#fff; border-color:#e0232e; }
.link-neutral  { background:#f6f7f9; color:#111; }
.link-neutral:hover { background:#eef0f4; }
.link-primary:hover { filter:brightness(1.05); }
</style>
<div class="linkbar">
  <a class="link-primary" href="https://www.wrpf.uk/memberships" target="_blank" rel="noopener">Sign Up!</a>
  <a class="link-neutral" href="https://www.records.wrpf.uk" target="_blank" rel="noopener">Records</a>
  <a class="link-neutral" href="https://www.wrpf.uk/events" target="_blank" rel="noopener">Events</a>
  <a class="link-neutral" href="https://www.wrpf.uk/live" target="_blank" rel="noopener">Live Streams</a>
</div>
""", unsafe_allow_html=True)

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

male_wcs = sorted(
    data.loc[data["Sex"] == "Male", "WeightClassKg"].dropna().unique().tolist(),
    key=numeric_sort_key_wc
)
female_wcs = sorted(
    data.loc[data["Sex"] == "Female", "WeightClassKg"].dropna().unique().tolist(),
    key=numeric_sort_key_wc
)

eqs = sorted(data["Equipment"].dropna().unique().tolist())

if "tested_state" not in st.session_state:
    st.session_state["tested_state"] = "All"

# -------------------- Horizontal Filter Bar (no search override) --------------------
cols = st.columns([1.2, 1.8, 1.8, 1.8, 1.6, 1.2, 0.9])
c_gender, c_age, c_wc_f, c_wc_m, c_eq, c_tested, c_reset = cols

with c_gender:
    st.multiselect("Gender", options=["Male", "Female"], key="gender")

with c_age:
    st.multiselect("Age Category", options=ages, key="ages")

selected_gender = st.session_state.get("gender") or []
show_female_wc = (selected_gender == ["Female"]) or (not selected_gender) or (set(selected_gender) == {"Male", "Female"})
show_male_wc = (selected_gender == ["Male"]) or (not selected_gender) or (set(selected_gender) == {"Male", "Female"})

with c_wc_f:
    if show_female_wc:
        st.multiselect("Female Weight Class (Kg)", options=female_wcs, key="wcs_female")
    else:
        st.empty()

with c_wc_m:
    if show_male_wc:
        st.multiselect("Male Weight Class (Kg)", options=male_wcs, key="wcs_male")
    else:
        st.empty()

with c_eq:
    st.multiselect("Equipment", options=eqs, key="equipment")

with c_tested:
    st.selectbox("Tested", options=["All", "Tested", "Untested"], key="tested_state")

with c_reset:
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
