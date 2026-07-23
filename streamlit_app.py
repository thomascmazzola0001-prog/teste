from __future__ import annotations

from pathlib import Path
import streamlit as st

from src.data import init_state, BRANCHES
from src.theme import inject_css
from src.components import sidebar_brand
from src.pages import PAGES


def _sidebar_navigation() -> None:
    with st.sidebar:
        sidebar_brand(Path(__file__).parent / "assets" / "jamef_logo.png")
        st.markdown('<div class="sidebar-section">Navegação</div>', unsafe_allow_html=True)

        labels = {
            "Resumo Executivo": "▥  Resumo Executivo",
            "Demanda & Restrições": "◉  Demanda & Restrições",
            "Capacidade de Pessoas": "●  Capacidade de Pessoas",
            "Frota & Veículos": "▰  Frota & Veículos",
            "Financeiro & EBITDA": "$  Financeiro & EBITDA",
            "Premissas & Governança": "⚙  Premissas & Governança",
        }
        for page_name in PAGES:
            active = page_name == st.session_state.page
            if st.button(
                labels[page_name],
                key=f"nav_{page_name}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                st.session_state.page = page_name
                st.rerun()

        st.divider()
        st.markdown('<div class="sidebar-section">Status do ciclo</div>', unsafe_allow_html=True)
        branches = st.session_state.branches or BRANCHES
        st.markdown(
            f"""
            <div class="sidebar-status">
              <b>{st.session_state.scenario}</b><br>
              Horizonte: {st.session_state.period}<br>
              Filiais: {len(branches)} selecionadas<br>
              Unidade: caixas
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Os filtros e editores recalculam demanda → pessoas → frota → EBITDA.")


def main() -> None:
    st.set_page_config(
        page_title="S&OP Jamef",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get help": None,
            "Report a bug": None,
            "About": "Plataforma integrada de S&OP Jamef",
        },
    )
    init_state()
    # O piso é controlado por filial na base de premissas. Evita sobrescrever
    # todas as filiais por um único slider global.
    st.session_state.global_floor = None
    inject_css()
    _sidebar_navigation()
    PAGES[st.session_state.page]()


if __name__ == "__main__":
    main()
