from __future__ import annotations
from pathlib import Path
import streamlit as st

from src.data import init_state, BRANCHES
from src.theme import inject_css
from src.components import sidebar_brand
from src.pages import PAGES

st.set_page_config(
    page_title="S&OP Jamef",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help":None,"Report a bug":None,"About":"Plataforma S&OP Jamef"},
)
init_state()
inject_css()

with st.sidebar:
    sidebar_brand(Path(__file__).parent / "assets" / "jamef_logo.png")
    st.markdown('<div class="sidebar-section">Navegação</div>',unsafe_allow_html=True)
    labels={
        "Resumo Executivo":"▥  Resumo Executivo",
        "Demanda & Restrições":"◉  Demanda & Restrições",
        "Capacidade de Pessoas":"●  Capacidade de Pessoas",
        "Frota & Veículos":"▰  Frota & Veículos",
        "Financeiro & EBITDA":"$  Financeiro & EBITDA",
        "Premissas & Governança":"⚙  Premissas & Governança",
    }
    pages=list(PAGES)
    selected=st.radio("Página",pages,index=pages.index(st.session_state.page),format_func=lambda x:labels[x],label_visibility="collapsed")
    st.session_state.page=selected
    st.divider()
    st.markdown('<div class="sidebar-section">Simulação rápida</div>',unsafe_allow_html=True)
    st.session_state.scenario=st.selectbox("Cenário",["Cenário Base","Peak Season","Otimista","Conservador"],index=["Cenário Base","Peak Season","Otimista","Conservador"].index(st.session_state.scenario),key="side_scenario")
    st.session_state.global_override=st.slider("Override comercial global (%)",-20.0,30.0,float(st.session_state.global_override),1.0)
    st.session_state.global_floor=st.slider("Piso mínimo global (%)",50.0,100.0,float(st.session_state.global_floor),1.0)
    st.caption("Os controles recalculam toda a cadeia: demanda → pessoas → veículos → EBITDA.")

PAGES[st.session_state.page]()
