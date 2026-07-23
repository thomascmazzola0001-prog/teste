from __future__ import annotations
import base64
from pathlib import Path
import streamlit as st


def image_as_base64(path: str | Path) -> str:
    p = Path(path)
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def sidebar_brand(logo_path: str | Path) -> None:
    encoded = image_as_base64(logo_path)
    st.markdown(
        f"""
        <div class="jamef-logo-box">
          <img src="data:image/png;base64,{encoded}" style="width:170px;max-width:100%;display:block;margin:0 auto 8px;">
          <div class="sidebar-title">S&OP Control Tower</div>
          <div class="sidebar-subtitle">Planejamento integrado de demanda, capacidade e resultado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(number: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="page-title-row">
          <div>
            <div class="page-number">{number}</div>
            <div class="page-title">{title}</div>
            <div class="page-subtitle">{subtitle}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, kicker: str | None = None) -> None:
    if kicker:
        st.markdown(f'<div class="section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, foot: str = "", sentiment: str = "") -> None:
    foot_class = ""
    if sentiment == "positive":
        foot_class = " positive"
    elif sentiment == "negative":
        foot_class = " negative"
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-foot{foot_class}">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stage_cards(active: int = 5) -> None:
    stages = [
        ("01", "Consenso de demanda", "Comercial + IM"),
        ("02", "Capacidade operacional", "Operações"),
        ("03", "Plano de atuação", "Pessoas + frota"),
        ("04", "Conciliação financeira", "Finanças"),
        ("05", "Reconciliação executiva", "Decisão"),
    ]
    html = ['<div class="stage-row">']
    for i, (num, name, owner) in enumerate(stages, start=1):
        active_class = " active" if i == active else ""
        html.append(
            f"""<div class="stage-card{active_class}">
              <div class="stage-num">{num}</div>
              <div class="stage-name">{name}</div>
              <div class="stage-owner">{owner}</div>
            </div>"""
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def note_box(text: str) -> None:
    st.markdown(f'<div class="note-box">{text}</div>', unsafe_allow_html=True)


def rule_box(title: str, lines: list[str]) -> None:
    html = f"<div class='rule-box'><b>{title}</b><br>"
    html += "<br>".join(lines)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
