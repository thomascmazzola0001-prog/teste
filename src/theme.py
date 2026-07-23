from __future__ import annotations
import streamlit as st

JAMEF_RED = "#E30613"
JAMEF_RED_DARK = "#B5000B"
JAMEF_BLACK = "#17191C"
JAMEF_DARK = "#25282D"
JAMEF_GRAY = "#69717C"
JAMEF_LIGHT = "#F4F5F7"
JAMEF_BORDER = "#E2E5EA"
JAMEF_GREEN = "#1C8A59"
JAMEF_AMBER = "#D99213"
JAMEF_BLUE = "#386FA4"


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
html, body, [class*="css"] {{ font-family: "Segoe UI", Arial, sans-serif; }}
.stApp {{ background: var(--j-light); }}
.block-container {{
  max-width: 1760px;
  padding: .75rem 1.15rem 2.5rem 1.15rem;
}}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
[data-testid="stToolbar"] {{ visibility: hidden; height: 0; }}
[data-testid="stDecoration"] {{ display: none; }}

/* Sidebar */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #15171A 0%, #21242A 100%);
  border-right: 1px solid #34383F;
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: .6rem; }}
[data-testid="stSidebar"] * {{ color: #F6F7F8; }}
[data-testid="stSidebar"] hr {{ border-color: #393D44; }}
[data-testid="stSidebar"] .stButton > button {{
  width: 100%;
  justify-content: flex-start;
  text-align: left;
  border: 0;
  border-radius: 9px;
  min-height: 2.55rem;
  padding: .48rem .65rem;
  font-size: .83rem;
  font-weight: 650;
  box-shadow: none;
}}
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
  background: transparent;
  color: #EEF0F2;
}}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{
  background: #2C3036;
  color: white;
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background: linear-gradient(90deg, var(--j-red) 0%, var(--j-red-dark) 100%);
  color: white;
  box-shadow: 0 5px 15px rgba(227, 6, 19, .22);
}}
.jamef-logo-box {{ padding: .25rem .4rem .7rem .4rem; }}
.sidebar-title {{ color: white; font-weight: 800; font-size: 1.08rem; margin-top: .35rem; }}
.sidebar-subtitle {{ color: #ADB3BC; font-size: .72rem; line-height: 1.4; margin-top: .2rem; }}
.sidebar-section {{
  color: #9EA5AF;
  text-transform: uppercase;
  letter-spacing: .09em;
  font-size: .63rem;
  font-weight: 800;
  margin: .85rem 0 .3rem;
}}
.sidebar-status {{
  background: #111316;
  border: 1px solid #34383F;
  border-radius: 9px;
  padding: .65rem .7rem;
  font-size: .7rem;
  color: #C7CCD3;
  line-height: 1.55;
}}

/* Cabeçalhos */
.page-title-row {{ margin-bottom: .35rem; }}
.page-title {{ color: #17191C; font-size: 1.7rem; line-height: 1.08; font-weight: 820; margin: 0; }}
.page-subtitle {{ color: #747B85; font-size: .84rem; margin-top: .2rem; }}
.page-number {{ color: var(--j-red); font-size: .72rem; font-weight: 850; letter-spacing: .08em; }}
.section-kicker {{ color: var(--j-red); font-size: .64rem; font-weight: 850; letter-spacing: .09em; margin-bottom: .1rem; }}
.section-title {{ color: #202329; font-size: .96rem; font-weight: 780; margin: .1rem 0 .42rem; }}

/* Containers */
[data-testid="stVerticalBlockBorderWrapper"] {{
  border-color: var(--j-border) !important;
  border-radius: 11px !important;
  background: white;
  box-shadow: 0 2px 9px rgba(25, 29, 36, .035);
}}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {{
  border: 1px solid var(--j-border);
  border-radius: 9px;
  overflow: hidden;
  background: white;
}}
.stTabs [data-baseweb="tab-list"] {{ gap: .15rem; border-bottom: 1px solid var(--j-border); }}
.stTabs [data-baseweb="tab"] {{
  height: 2.2rem;
  border-radius: 8px 8px 0 0;
  padding: 0 .72rem;
  font-size: .75rem;
  font-weight: 680;
}}
.stTabs [aria-selected="true"] {{ color: var(--j-red) !important; border-bottom-color: var(--j-red) !important; }}
.stButton > button, .stDownloadButton > button {{
  border-radius: 8px;
  font-size: .76rem;
  min-height: 2.25rem;
  font-weight: 680;
}}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
  background: var(--j-red);
  border-color: var(--j-red);
}}

/* KPIs: sem altura fixa e com quebra de linha controlada */
.kpi-card {{
  min-height: 112px;
  height: 100%;
  background: white;
  border: 1px solid var(--j-border);
  border-top: 4px solid var(--j-red);
  border-radius: 11px;
  padding: .68rem .75rem;
  box-shadow: 0 3px 11px rgba(24, 28, 34, .04);
  overflow: hidden;
}}
.kpi-label {{
  color: #666E79;
  font-size: .63rem;
  font-weight: 820;
  letter-spacing: .045em;
  text-transform: uppercase;
  line-height: 1.25;
  overflow-wrap: anywhere;
}}
.kpi-value {{
  color: #16181B;
  font-size: clamp(1.02rem, 1.35vw, 1.38rem);
  font-weight: 820;
  margin-top: .33rem;
  line-height: 1.08;
  overflow-wrap: anywhere;
}}
.kpi-foot {{
  color: #818894;
  font-size: .66rem;
  margin-top: .38rem;
  line-height: 1.25;
  overflow-wrap: anywhere;
}}
.kpi-foot.positive {{ color: #19744A; }}
.kpi-foot.negative {{ color: #B90F1A; }}

/* Etapas */
.stage-row {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .48rem; margin: .25rem 0 .72rem; }}
.stage-card {{
  background: white;
  border: 1px solid var(--j-border);
  border-radius: 10px;
  padding: .55rem .62rem;
  min-height: 76px;
  overflow: hidden;
}}
.stage-card.active {{ border: 1.5px solid var(--j-red); background: #FFF8F8; }}
.stage-num {{ color: var(--j-red); font-size: .62rem; font-weight: 850; }}
.stage-name {{ color: #24272C; font-size: .72rem; font-weight: 760; margin-top: .16rem; line-height: 1.2; }}
.stage-owner {{ color: #8A919A; font-size: .6rem; margin-top: .18rem; line-height: 1.2; }}

/* Notas e regras */
.note-box {{
  background: #FFF8F8;
  border: 1px solid #F0C6C9;
  border-left: 4px solid var(--j-red);
  border-radius: 9px;
  padding: .68rem .78rem;
  color: #555D67;
  font-size: .73rem;
  line-height: 1.45;
  overflow-wrap: anywhere;
  word-break: normal;
  white-space: normal;
}}
.rule-box {{
  background: #F9FAFB;
  border: 1px solid var(--j-border);
  border-radius: 9px;
  padding: .72rem .82rem;
  color: #4E5660;
  font-size: .72rem;
  line-height: 1.55;
}}
@media (max-width: 1150px) {{
  .stage-row {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .kpi-card {{ min-height: 100px; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )
