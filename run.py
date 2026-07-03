import os
import io
import html
import pandas as pd
import streamlit as st

st.set_page_config(page_title="WRPF UK — Qualifying Totals", layout="wide")


WRPF_RED = "#ff3131"
WRPF_DARK = "#111827"
WRPF_MUTED = "#6b7280"


def inject_app_style():
    st.markdown("""
    <style>
    :root{
      --wrpf-red: #ff3131;
      --wrpf-red-dark: #c92020;
      --wrpf-dark: #111827;
      --wrpf-slate: #1f2937;
      --wrpf-muted: #6b7280;
      --wrpf-border: rgba(17,24,39,.10);
      --wrpf-soft: #f7f8fb;
      --wrpf-good: #059669;
      --wrpf-good-bg: #ecfdf5;
      --wrpf-good-border: #a7f3d0;
    }

    .main .block-container{
      max-width: 1280px;
      padding-top: 1.7rem;
      padding-bottom: 3rem;
    }

    h1, h2, h3{
      letter-spacing: -.02em;
    }

    div[data-testid="stHorizontalBlock"]{
      gap: .75rem;
    }

    .wrpf-page-hero{
      position: relative;
      overflow: hidden;
      border-radius: 18px;
      padding: 1.45rem 1.6rem;
      margin: .25rem 0 1.1rem;
      background:
        radial-gradient(circle at top right, rgba(255,49,49,.32), transparent 34%),
        linear-gradient(135deg, #101827 0%, #151515 58%, #2a1010 100%);
      border: 1px solid rgba(255,255,255,.10);
      box-shadow: 0 18px 45px rgba(17,24,39,.16);
      color: #ffffff;
    }
    .wrpf-page-kicker{
      color: rgba(255,255,255,.72);
      font-size: .82rem;
      font-weight: 800;
      letter-spacing: .16em;
      text-transform: uppercase;
      margin-bottom: .35rem;
    }
    .wrpf-page-title{
      font-size: clamp(1.85rem, 4vw, 3.05rem);
      font-weight: 900;
      line-height: 1.02;
      margin: 0;
    }
    .wrpf-page-subtitle{
      color: rgba(255,255,255,.76);
      font-size: 1rem;
      line-height: 1.5;
      max-width: 860px;
      margin-top: .72rem;
    }

    .linkgrid{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: .85rem;
      margin: .4rem 0 1.2rem;
    }
    @media (max-width: 1100px){
      .linkgrid{ grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 640px){
      .linkgrid{ grid-template-columns: 1fr; }
    }
    .linkbtn{
      display:flex;
      align-items:center;
      justify-content:space-between;
      min-height: 52px;
      padding: 0 1rem;
      background: #ffffff;
      color: var(--wrpf-dark) !important;
      border-radius: 14px;
      font-weight: 850;
      text-decoration: none !important;
      border: 1px solid var(--wrpf-border);
      box-shadow: 0 8px 22px rgba(17,24,39,.055);
      transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }
    .linkbtn:after{
      content: "→";
      color: var(--wrpf-red);
      font-weight: 900;
      transition: transform .16s ease;
    }
    .linkbtn:hover{
      transform: translateY(-2px);
      border-color: rgba(255,49,49,.35);
      box-shadow: 0 12px 28px rgba(17,24,39,.10);
    }
    .linkbtn:hover:after{ transform: translateX(3px); }

    /* Streamlit tab polish */
    .stTabs [data-baseweb="tab-list"]{
      gap: .4rem;
      border-bottom: 1px solid rgba(17,24,39,.10);
    }
    .stTabs [data-baseweb="tab"]{
      height: 46px;
      padding: 0 .95rem;
      border-radius: 10px 10px 0 0;
      font-weight: 800;
    }
    .stTabs [aria-selected="true"]{
      color: var(--wrpf-red) !important;
      background: rgba(255,49,49,.07);
    }

    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button{
      border-radius: 10px;
      font-weight: 800;
    }
    div[data-testid="stDownloadButton"] button{
      border-color: rgba(255,49,49,.30);
    }

    div[data-testid="stTextInput"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stSelectbox"] label{
      font-weight: 800;
      color: #1f2937;
    }
    div[data-testid="stTextInput"] input{
      min-height: 48px;
      border-radius: 12px;
      border: 1px solid rgba(17,24,39,.14);
      font-size: 1rem;
      box-shadow: 0 1px 2px rgba(17,24,39,.04);
    }
    div[data-testid="stTextInput"] input:focus{
      border-color: rgba(255,49,49,.60);
      box-shadow: 0 0 0 3px rgba(255,49,49,.12);
    }

    .qualified-hero{
      border-radius: 18px;
      padding: 1.35rem 1.45rem;
      margin: .25rem 0 1rem;
      background:
        linear-gradient(135deg, rgba(255,49,49,.12), rgba(255,255,255,.95) 46%),
        #ffffff;
      border: 1px solid rgba(255,49,49,.18);
      box-shadow: 0 14px 36px rgba(17,24,39,.08);
    }
    .qualified-kicker{
      font-size: .78rem;
      font-weight: 900;
      letter-spacing: .16em;
      text-transform: uppercase;
      color: var(--wrpf-red);
      margin-bottom: .35rem;
    }
    .qualified-title{
      color: var(--wrpf-dark);
      font-size: clamp(1.45rem, 3vw, 2.25rem);
      line-height: 1.08;
      font-weight: 950;
      letter-spacing: -.03em;
      margin: 0;
    }
    .qualified-copy{
      color: #4b5563;
      line-height: 1.55;
      margin-top: .55rem;
      max-width: 850px;
    }

    .qualified-stats{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: .85rem;
      margin: .7rem 0 1rem;
    }
    @media (max-width: 900px){
      .qualified-stats{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 520px){
      .qualified-stats{ grid-template-columns: 1fr; }
    }
    .qualified-stat{
      background: #ffffff;
      border: 1px solid var(--wrpf-border);
      border-radius: 16px;
      padding: .9rem 1rem;
      box-shadow: 0 8px 22px rgba(17,24,39,.055);
    }
    .qualified-stat-value{
      color: var(--wrpf-dark);
      font-size: 1.65rem;
      line-height: 1;
      font-weight: 950;
      letter-spacing: -.03em;
    }
    .qualified-stat-label{
      color: var(--wrpf-muted);
      font-size: .82rem;
      font-weight: 750;
      margin-top: .35rem;
    }

    .qualified-search-panel{
      background: #ffffff;
      border: 1px solid var(--wrpf-border);
      border-radius: 18px;
      padding: 1rem 1rem .8rem;
      margin-top: .8rem;
      box-shadow: 0 12px 30px rgba(17,24,39,.07);
    }
    .qualified-note{
      color: #6b7280;
      font-size: .9rem;
      margin-top: .25rem;
    }

    .qualified-results{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: .85rem;
      margin-top: 1rem;
    }
    @media (max-width: 1100px){
      .qualified-results{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 720px){
      .qualified-results{ grid-template-columns: 1fr; }
    }
    .qualified-card{
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(17,24,39,.10);
      border-radius: 18px;
      padding: 1rem;
      background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
      box-shadow: 0 10px 28px rgba(17,24,39,.07);
    }
    .qualified-card:before{
      content: "";
      position:absolute;
      left:0;
      top:0;
      width: 5px;
      height:100%;
      background: var(--wrpf-red);
    }
    .qualified-name{
      font-weight: 950;
      font-size: 1.08rem;
      line-height: 1.22;
      color: #111827;
      margin: 0 0 .75rem .15rem;
      padding-right: .25rem;
    }
    .qualified-row{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: .7rem;
      padding: .48rem .15rem;
      border-top: 1px solid rgba(17,24,39,.07);
    }
    .qualified-label{
      color: #374151;
      font-weight: 800;
      font-size: .92rem;
    }
    .qualified-pill{
      border-radius: 999px;
      padding: .28rem .66rem;
      font-size: .78rem;
      font-weight: 950;
      white-space: nowrap;
      letter-spacing: .01em;
    }
    .qualified-pill.yes{
      color: #047857;
      background: #d1fae5;
      border: 1px solid #a7f3d0;
    }
    .qualified-pill.no{
      color: #6b7280;
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
    }
    .qualified-empty{
      border-radius: 16px;
      border: 1px dashed rgba(17,24,39,.20);
      background: #ffffff;
      padding: 1.1rem;
      color: #4b5563;
      font-weight: 700;
      margin-top: 1rem;
    }
    .qualified-alert{
      border-radius: 16px;
      padding: .95rem 1rem;
      margin-top: 1rem;
      font-weight: 750;
      border: 1px solid rgba(255,49,49,.22);
      background: rgba(255,49,49,.06);
      color: #7f1d1d;
    }
    .qualified-success{
      border-radius: 16px;
      padding: .85rem 1rem;
      margin-top: 1rem;
      font-weight: 850;
      border: 1px solid var(--wrpf-good-border);
      background: var(--wrpf-good-bg);
      color: #065f46;
    }
    </style>
    """, unsafe_allow_html=True)


def render_page_hero():
    st.markdown("""
    <div class="wrpf-page-hero">
      <div class="wrpf-page-kicker">WRPF UK</div>
      <div class="wrpf-page-title">Qualifying Totals</div>
      <div class="wrpf-page-subtitle">
        View current qualifying totals, compare previous-year standards, and check whether an athlete has already qualified for Nationals.
      </div>
    </div>
    """, unsafe_allow_html=True)

def load_qualifying_table(file_path_or_obj) -> pd.DataFrame:
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

    for c in ["Age Category", "Sex", "Event", "Tested", "Equipment", "WeightClassKg"]:
        long_df[c] = long_df[c].astype(str).str.strip()
    long_df = long_df[~long_df["QualifyingTotalKg"].isna()]

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
    gender = st.session_state.get("gender") or []
    ages = st.session_state.get("ages") or []
    wcs_male = st.session_state.get("wcs_male") or []
    wcs_female = st.session_state.get("wcs_female") or []
    equipment = st.session_state.get("equipment") or []
    tested_state = st.session_state.get("tested_state", "All")

    out = df.copy()

    if gender:
        out = out[out["Sex"].isin(gender)]

    if ages:
        out = out[out["Age Category"].isin(ages)]

    if gender == ["Female"]:
        if wcs_female:
            out = out[out["WeightClassKg"].isin(wcs_female)]
    elif gender == ["Male"]:
        if wcs_male:
            out = out[out["WeightClassKg"].isin(wcs_male)]
    else:
        combined = list(set(wcs_male) | set(wcs_female))
        if combined:
            out = out[out["WeightClassKg"].isin(combined)]

    if equipment:
        out = out[out["Equipment"].isin(equipment)]

    if tested_state == "Tested":
        out = out[out["Tested"].str.lower() == "tested"]
    elif tested_state == "Untested":
        out = out[out["Tested"].str.lower() == "untested"]

    return out


def show_table(df: pd.DataFrame, title: str):
    st.markdown(f"### {title}")
    st.markdown("""
    <style>
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
        .sort_values(by=["Sex", "Age Category", "Event", "Tested", "Equipment", "WeightClassKg"], kind="mergesort")
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

QUALIFIED_FILE = "Qualified.csv"


def normalise_yes(value) -> str:
    value = "" if pd.isna(value) else str(value).strip()
    if value.lower() in {"yes", "y", "true", "1", "qualified"}:
        return "Yes"
    return ""


def load_qualified_athletes(file_path: str) -> pd.DataFrame:
    qualified = pd.read_csv(file_path, encoding="utf-8-sig")
    qualified.columns = [str(c).strip() for c in qualified.columns]

    required_cols = ["Name", "Open Nationals", "Masters Nationals"]
    missing = [c for c in required_cols if c not in qualified.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    qualified = qualified[required_cols].copy()
    for col in required_cols:
        qualified[col] = qualified[col].fillna("").astype(str).str.strip()

    qualified = qualified[qualified["Name"] != ""].copy()
    qualified["Open Nationals"] = qualified["Open Nationals"].apply(normalise_yes)
    qualified["Masters Nationals"] = qualified["Masters Nationals"].apply(normalise_yes)

    # If the CSV is appended to over time and a lifter appears more than once,
    # combine the rows so the public search only shows one clear result per lifter.
    qualified = (
        qualified
        .groupby("Name", as_index=False, sort=False)
        .agg({
            "Open Nationals": lambda s: "Yes" if any(v == "Yes" for v in s) else "",
            "Masters Nationals": lambda s: "Yes" if any(v == "Yes" for v in s) else "",
        })
    )

    return qualified.sort_values("Name", kind="mergesort").reset_index(drop=True)


def render_qualified_cards(results: pd.DataFrame):
    cards = []
    for _, row in results.iterrows():
        name = html.escape(str(row["Name"]))
        open_yes = str(row["Open Nationals"]).strip().lower() == "yes"
        masters_yes = str(row["Masters Nationals"]).strip().lower() == "yes"

        open_class = "yes" if open_yes else "no"
        masters_class = "yes" if masters_yes else "no"
        open_text = "Qualified" if open_yes else "Not listed"
        masters_text = "Qualified" if masters_yes else "Not listed"

        cards.append(f"""
        <div class="qualified-card">
          <div class="qualified-name">{name}</div>
          <div class="qualified-row">
            <span class="qualified-label">Teen, Junior &amp; Open Nationals</span>
            <span class="qualified-pill {open_class}">{open_text}</span>
          </div>
          <div class="qualified-row">
            <span class="qualified-label">Masters Nationals</span>
            <span class="qualified-pill {masters_class}">{masters_text}</span>
          </div>
        </div>
        """)

    st.markdown(f'<div class="qualified-results">{"".join(cards)}</div>', unsafe_allow_html=True)


inject_app_style()
render_page_hero()

st.markdown("""
<div class="linkgrid">
  <a class="linkbtn" href="https://www.wrpf.uk/memberships" target="_blank" rel="noopener">Sign Up</a>
  <a class="linkbtn" href="https://www.wrpf.uk/records" target="_blank" rel="noopener">Records</a>
  <a class="linkbtn" href="https://www.wrpf.uk/events" target="_blank" rel="noopener">Events</a>
  <a class="linkbtn" href="https://www.wrpf.uk/live" target="_blank" rel="noopener">Live Streams</a>
</div>
""", unsafe_allow_html=True)

DEFAULT_FILE = "FP.xlsx"
PREV_FILE = "2025_FP.xlsx"  # used in the "2025 Qualifying Totals" tab

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

# Try to load previous year's file, but don't stop if it's missing.
prev_data = None
if os.path.exists(PREV_FILE):
    try:
        prev_data = load_qualifying_table(PREV_FILE)
    except Exception as e:
        st.warning(f"Found {PREV_FILE} but could not read it. Details: {e}")
else:
    # We'll show a friendly message only inside the tab if selected
    prev_data = None

def union_series(series_list):
    out = pd.Series(dtype=object)
    for s in series_list:
        out = pd.Series(pd.unique(pd.concat([out, s.dropna().astype(str)])))
    return sorted(out.tolist())

source_series_ages = [data["Age Category"]]
source_series_eq = [data["Equipment"]]
male_wc_series = [data.loc[data["Sex"] == "Male", "WeightClassKg"]]
female_wc_series = [data.loc[data["Sex"] == "Female", "WeightClassKg"]]

if isinstance(prev_data, pd.DataFrame):
    source_series_ages.append(prev_data["Age Category"])
    source_series_eq.append(prev_data["Equipment"])
    male_wc_series.append(prev_data.loc[prev_data["Sex"] == "Male", "WeightClassKg"])
    female_wc_series.append(prev_data.loc[prev_data["Sex"] == "Female", "WeightClassKg"])

ages = union_series(source_series_ages)
eqs = union_series(source_series_eq)
male_wcs = sorted(pd.unique(pd.concat(male_wc_series).astype(str)).tolist(), key=numeric_sort_key_wc)
female_wcs = sorted(pd.unique(pd.concat(female_wc_series).astype(str)).tolist(), key=numeric_sort_key_wc)

if "tested_state" not in st.session_state:
    st.session_state["tested_state"] = "All"

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

tab_sbd, tab_singles, tab_prev, tab_qualified = st.tabs(["Full Power (SBD)", "Single Lifts (B & D)", "2025 Qualifying Totals", "Qualified Athletes"])

with tab_sbd:
    sbd_df = data[data["Event"] == "SBD"]
    sbd_view = filter_with_controls(sbd_df)
    show_table(sbd_view, "Full Power (SBD)")

with tab_singles:
    singles_df = data[data["Event"].isin(["B", "D"])]
    singles_view = filter_with_controls(singles_df)
    show_table(singles_view, "Single Lifts (B & D)")

with tab_prev:
    if prev_data is None:
        st.info(f"Add **{PREV_FILE}** next to `app.py` to view previous year’s qualifying totals here.")
    else:
        st.markdown("#### Previous Year — Based on 2025_FP.xlsx")
        prev_sbd = prev_data[prev_data["Event"] == "SBD"]
        prev_singles = prev_data[prev_data["Event"].isin(["B", "D"])]

        prev_sbd_view = filter_with_controls(prev_sbd)
        show_table(prev_sbd_view, "Previous Year — Full Power (SBD)")

        st.markdown("---")
        prev_singles_view = filter_with_controls(prev_singles)
        show_table(prev_singles_view, "Previous Year — Single Lifts (B & D)")


with tab_qualified:
    st.markdown("### Qualified Athletes")
    st.caption("Search for an athlete to see whether they have qualified for Teen, Junior & Open Nationals, Masters Nationals or both.")
    st.caption("Please be aware, if you have qualified at a Novice event, or cross federation, you will not appear in this datbase.")
    st.caption("If you competed at a novice event with a WRPF UK Membership you will have received an invitation via email.")
    st.caption("Any queries, please send them to events@wrpf.uk")

    if not os.path.exists(QUALIFIED_FILE):
        st.error(f"{QUALIFIED_FILE} not found.")
    else:
        try:
            qualified_data = load_qualified_athletes(QUALIFIED_FILE)
        except Exception as e:
            st.error(f"Could not read {QUALIFIED_FILE}: {e}")
        else:
            search_name = st.text_input(
                "Search athlete",
                placeholder="Start typing a name...",
                key="qualified_athlete_search",
            ).strip()

            if not search_name:
                st.info("Type an athlete name above to search.")
            elif len(search_name) < 2:
                st.info("Enter at least 2 characters.")
            else:
                query = search_name.lower()
                results = qualified_data[
                    qualified_data["Name"].str.lower().str.contains(query, regex=False, na=False)
                ].copy()

                if results.empty:
                    st.warning("No matching athlete found.")
                else:
                    results["_rank"] = results["Name"].str.lower().apply(
                        lambda n: 0 if n == query else 1 if n.startswith(query) else 2
                    )
                    results = results.sort_values(["_rank", "Name"]).drop(columns=["_rank"])
                    render_qualified_cards(results.head(20))
