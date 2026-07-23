from __future__ import annotations
import streamlit as st

JAMEF_RED = "#E30613"
JAMEF_RED_DARK = "#B6000A"
JAMEF_BLACK = "#1B1D20"
JAMEF_DARK = "#25282D"
JAMEF_GRAY = "#6B7280"
JAMEF_LIGHT = "#F4F5F7"
JAMEF_BORDER = "#E2E5E9"
JAMEF_GREEN = "#1B8A5A"
JAMEF_AMBER = "#E39B17"
JAMEF_BLUE = "#2D6DA3"


def inject_css() -> None:
    st.markdown(
        f"""
<style>
:root {{
  --j-red: {JAMEF_RED};
  --j-red-dark: {JAMEF_RED_DARK};
  --j-black: {JAMEF_BLACK};
  --j-dark: {JAMEF_DARK};
  --j-gray: {JAMEF_GRAY};
  --j-light: {JAMEF_LIGHT};
  --j-border: {JAMEF_BORDER};
}}
html, body, [class*="css"] {{
  font-family: "Segoe UI", Arial, sans-serif;
}}
.stApp {{
  background: var(--j-light);
}}
.block-container {{
  max-width: 1680px;
  padding-top: 0.8rem;
  padding-left: 1.25rem;
  padding-right: 1.25rem;
  padding-bottom: 2rem;
}}
header[data-testid="stHeader"] {{
  background: transparent;
  height: 0;
}}
[data-testid="stToolbar"] {{
  visibility: hidden;
  height: 0;
}}
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #181A1D 0%, #202328 100%);
  border-right: 1px solid #34373C;
}}
[data-testid="stSidebar"] > div:first-child {{
  padding-top: 0.7rem;
}}
[data-testid="stSidebar"] * {{
  color: #F8F9FA;
}}
[data-testid="stSidebar"] .stRadio > label {{
  display: none;
}}
[data-testid="stSidebar"] div[role="radiogroup"] label {{
  background: transparent;
  border-radius: 8px;
  padding: 0.48rem 0.55rem;
  margin: 0.12rem 0;
  transition: all .16s ease;
}}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
  background: #2D3035;
}}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
  background: linear-gradient(90deg, {JAMEF_RED} 0%, {JAMEF_RED_DARK} 100%);
  box-shadow: 0 5px 14px rgba(227, 6, 19, .22);
}}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSlider label {{
  color: #F8F9FA !important;
  font-size: .77rem;
  font-weight: 600;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
  background: #111316;
  border-color: #3A3D42;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] {{
  background: {JAMEF_RED};
}}
[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {{
  background: {JAMEF_RED};
}}
[data-testid="stSidebar"] hr {{
  border-color: #373A40;
}}
.jamef-logo-box {{
  padding: 0.2rem 0.4rem 0.75rem 0.4rem;
}}
.sidebar-title {{
  color: white;
  font-weight: 700;
  font-size: 1.02rem;
  margin-top: .25rem;
}}
.sidebar-subtitle {{
  color: #AEB4BC;
  font-size: .72rem;
  line-height: 1.35;
  margin-bottom: .6rem;
}}
.sidebar-section {{
  text-transform: uppercase;
  letter-spacing: .08em;
  color: #AEB4BC;
  font-size: .65rem;
  font-weight: 700;
  margin: .8rem 0 .35rem;
}}
.page-title-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: .35rem;
}}
.page-title {{
  color: #17191C;
  font-size: 1.62rem;
  line-height: 1.1;
  font-weight: 750;
  margin: 0;
}}
.page-subtitle {{
  color: #737983;
  font-size: .82rem;
  margin-top: .2rem;
}}
.page-number {{
  color: {JAMEF_RED};
  font-size: .82rem;
  font-weight: 800;
  letter-spacing: .04em;
}}
.filter-shell {{
  background: #FFFFFF;
  border: 1px solid var(--j-border);
  border-radius: 10px;
  padding: .35rem .55rem .15rem .55rem;
  box-shadow: 0 2px 8px rgba(20, 24, 31, .035);
  margin-bottom: .55rem;
}}
[data-testid="stVerticalBlockBorderWrapper"] {{
  border-color: var(--j-border) !important;
  border-radius: 10px !important;
  background: #FFFFFF;
  box-shadow: 0 2px 8px rgba(20, 24, 31, .035);
}}
[data-testid="stMetric"] {{
  background: #FFFFFF;
  border: 1px solid var(--j-border);
  border-radius: 10px;
  padding: .7rem .8rem;
  min-height: 108px;
  box-shadow: 0 3px 10px rgba(20, 24, 31, .04);
}}
[data-testid="stMetricLabel"] {{
  color: #626872;
  font-size: .7rem;
  font-weight: 750;
  letter-spacing: .04em;
  text-transform: uppercase;
}}
[data-testid="stMetricValue"] {{
  color: #15171A;
  font-size: 1.38rem;
  font-weight: 760;
}}
[data-testid="stMetricDelta"] {{
  font-size: .7rem;
}}
.kpi-card {{
  height: 112px;
  background: #FFFFFF;
  border: 1px solid var(--j-border);
  border-top: 4px solid {JAMEF_RED};
  border-radius: 10px;
  padding: .68rem .78rem;
  box-shadow: 0 3px 10px rgba(20, 24, 31, .04);
}}
.kpi-label {{
  color: #666D77;
  font-size: .66rem;
  font-weight: 780;
  letter-spacing: .055em;
  text-transform: uppercase;
}}
.kpi-value {{
  color: #15171A;
  font-size: 1.38rem;
  font-weight: 780;
  margin-top: .3rem;
  line-height: 1.05;
}}
.kpi-foot {{
  color: #858B94;
  font-size: .67rem;
  margin-top: .34rem;
}}
.kpi-foot.positive {{ color: #19734A; }}
.kpi-foot.negative {{ color: #BE101B; }}
.section-title {{
  color: #202328;
  font-size: .92rem;
  line-height: 1.2;
  font-weight: 760;
  margin: .25rem 0 .4rem;
}}
.section-kicker {{
  color: {JAMEF_RED};
  font-size: .66rem;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
  margin-bottom: .1rem;
}}
.stage-row {{
  display:grid;
  grid-template-columns: repeat(5,1fr);
  gap:.55rem;
  margin:.25rem 0 .75rem;
}}
.stage-card {{
  background:#FFF;
  border:1px solid var(--j-border);
  border-radius:9px;
  padding:.55rem .65rem;
  min-height:73px;
}}
.stage-card.active {{
  border:1.5px solid {JAMEF_RED};
  background:#FFF8F8;
}}
.stage-num {{
  color:{JAMEF_RED};
  font-size:.65rem;
  font-weight:800;
}}
.stage-name {{
  color:#25282D;
  font-size:.76rem;
  font-weight:760;
  margin-top:.15rem;
}}
.stage-owner {{
  color:#8A9099;
  font-size:.61rem;
  margin-top:.16rem;
}}
.chart-box {{
  background:#FFF;
  border:1px solid var(--j-border);
  border-radius:10px;
  padding:.15rem .45rem .35rem;
  box-shadow:0 3px 10px rgba(20,24,31,.035);
}}
.note-box {{
  background:#FFF8F8;
  border:1px solid #F0C5C8;
  border-left:4px solid {JAMEF_RED};
  border-radius:8px;
  padding:.65rem .8rem;
  color:#555B64;
  font-size:.74rem;
}}
.rule-box {{
  background:#F8F9FA;
  border:1px solid var(--j-border);
  border-radius:8px;
  padding:.65rem .8rem;
  font-size:.73rem;
  color:#505761;
}}
.status-pill {{
  display:inline-block;
  border-radius:999px;
  padding:.12rem .45rem;
  font-size:.62rem;
  font-weight:750;
}}
.status-green {{background:#E8F5EE;color:#177146;}}
.status-yellow {{background:#FFF5DA;color:#9A6710;}}
.status-red {{background:#FDEBEC;color:#B20E18;}}
.stTabs [data-baseweb="tab-list"] {{
  gap: .2rem;
  border-bottom: 1px solid var(--j-border);
}}
.stTabs [data-baseweb="tab"] {{
  height: 2.15rem;
  border-radius: 7px 7px 0 0;
  padding: 0 .75rem;
  font-size: .76rem;
  font-weight: 650;
}}
.stTabs [aria-selected="true"] {{
  color: {JAMEF_RED} !important;
  border-bottom-color: {JAMEF_RED} !important;
}}
.stButton > button, .stDownloadButton > button {{
  border-radius: 7px;
  font-size: .74rem;
  min-height: 2.2rem;
  font-weight: 650;
}}
.stButton > button[kind="primary"] {{
  background: {JAMEF_RED};
  border-color: {JAMEF_RED};
}}
.stButton > button[kind="primary"]:hover {{
  background: {JAMEF_RED_DARK};
  border-color: {JAMEF_RED_DARK};
}}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {{
  border:1px solid var(--j-border);
  border-radius:9px;
  overflow:hidden;
}}
div[data-testid="stExpander"] {{
  background:#FFF;
  border:1px solid var(--j-border);
  border-radius:9px;
}}
hr {{
  border-color: var(--j-border);
}}
@media (max-width: 1100px) {{
  .stage-row {{grid-template-columns:1fr 1fr;}}
}}
</style>
""",
        unsafe_allow_html=True,
    )
