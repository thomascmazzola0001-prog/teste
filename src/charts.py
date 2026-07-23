from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .theme import JAMEF_RED, JAMEF_RED_DARK, JAMEF_BLACK, JAMEF_GRAY, JAMEF_GREEN, JAMEF_AMBER, JAMEF_BLUE

CONFIG={"displaylogo":False,"responsive":True,"modeBarButtonsToRemove":["lasso2d","select2d"]}


def base_layout(fig: go.Figure, height: int=340, ytitle: str="") -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="#FFFFFF",plot_bgcolor="#FFFFFF",
        margin=dict(l=42,r=16,t=24,b=40),
        font=dict(family="Segoe UI, Arial",size=11,color="#505761"),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="left",x=0,font=dict(size=10)),
        hovermode="x unified",
        xaxis=dict(showgrid=False,linecolor="#E3E6EA",tickfont=dict(size=10)),
        yaxis=dict(showgrid=True,gridcolor="#EDF0F2",zeroline=False,title=ytitle,tickfont=dict(size=10)),
    )
    return fig


def demand_12m(demand: pd.DataFrame, capacity: pd.DataFrame|None=None) -> go.Figure:
    df=demand.copy(); df["mes"]=df["data"].dt.to_period("M").dt.to_timestamp()
    m=df.groupby("mes",as_index=False).agg(
        bruto=("demanda_pos_override","sum"),
        restrito=("demanda_apos_restricao","sum"),
        piso=("piso_caixas","sum"),
        final=("demanda_final","sum"),
    )
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=m["mes"],y=m["bruto"],name="Demanda bruta",mode="lines",line=dict(color="#A8AFB7",width=2)))
    fig.add_trace(go.Scatter(x=m["mes"],y=m["restrito"],name="Após restrições",mode="lines",line=dict(color=JAMEF_AMBER,width=2)))
    fig.add_trace(go.Scatter(x=m["mes"],y=m["piso"],name="Piso das filiais",mode="lines",line=dict(color=JAMEF_RED_DARK,width=2,dash="dot")))
    fig.add_trace(go.Scatter(x=m["mes"],y=m["final"],name="Demanda ajustada",mode="lines+markers",line=dict(color=JAMEF_RED,width=3),marker=dict(size=5)))
    return base_layout(fig,345,"Caixas")


def demand_daily(demand: pd.DataFrame, branch: str|None=None) -> go.Figure:
    df=demand.copy()
    if branch and branch!="Todas":
        df=df.loc[df["filial"].eq(branch)]
    d=df.groupby("data",as_index=False).agg(
        bruto=("demanda_pos_override","sum"),
        restrito=("demanda_apos_restricao","sum"),
        piso=("piso_caixas","sum"),
        final=("demanda_final","sum"),
    )
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=d["data"],y=d["bruto"],name="Previsão pós-override",mode="lines",line=dict(color="#9BA3AD",width=1.7)))
    fig.add_trace(go.Scatter(x=d["data"],y=d["restrito"],name="Após restrições",mode="lines",line=dict(color=JAMEF_AMBER,width=1.8)))
    fig.add_trace(go.Scatter(x=d["data"],y=d["piso"],name="Piso mínimo",mode="lines",line=dict(color=JAMEF_RED_DARK,dash="dot",width=2)))
    fig.add_trace(go.Scatter(x=d["data"],y=d["final"],name="Demanda final",mode="lines",line=dict(color=JAMEF_RED,width=2.6)))
    return base_layout(fig,365,"Caixas/dia")


def history_forecast(demand_source: pd.DataFrame, adjusted: pd.DataFrame) -> go.Figure:
    hist=demand_source.loc[demand_source["data"]<adjusted["data"].min()].copy()
    hist=hist.groupby("data",as_index=False)["real_caixas"].sum().tail(180)
    fut=adjusted.groupby("data",as_index=False)["demanda_final"].sum()
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=hist["data"],y=hist["real_caixas"],name="Histórico",mode="lines",line=dict(color="#A8AFB7",width=1.8)))
    fig.add_trace(go.Scatter(x=fut["data"],y=fut["demanda_final"],name="Previsão ajustada",mode="lines",line=dict(color=JAMEF_RED,width=2.5)))
    return base_layout(fig,330,"Caixas/dia")


def people_daily(detail: pd.DataFrame) -> go.Figure:
    d=detail.groupby("data",as_index=False).agg(
        demanda=("demanda_caixas","sum"),capacidade=("capacidade_limitante","sum"),
        he=("he_horas","sum"),terceiro=("terceiro_horas","sum")
    )
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=d["data"],y=d["capacidade"],name="Capacidade regular",mode="lines",line=dict(color=JAMEF_GREEN,width=2.3)))
    fig.add_trace(go.Scatter(x=d["data"],y=d["demanda"],name="Demanda ajustada",mode="lines",line=dict(color=JAMEF_RED,width=2.4)))
    fig.add_trace(go.Bar(x=d["data"],y=d["demanda"]-d["capacidade"],name="Déficit / excedente",marker_color=np.where((d["demanda"]-d["capacidade"])>0,JAMEF_RED,"#B8D9C9"),opacity=.42))
    return base_layout(fig,355,"Caixas/dia")


def fte_monthly(plan: pd.DataFrame) -> go.Figure:
    d=plan.groupby(["mes","funcao"],as_index=False).agg(atual=("fte_atual","sum"),necessario=("fte_necessario_medio","sum"))
    fig=go.Figure()
    colors={"Ajudante":JAMEF_RED,"Conferente":JAMEF_BLACK}
    for func in d["funcao"].unique():
        f=d.loc[d["funcao"].eq(func)]
        fig.add_trace(go.Scatter(x=f["mes"],y=f["necessario"],name=f"{func} necessário",mode="lines+markers",line=dict(color=colors.get(func,JAMEF_GRAY),width=2.4)))
    actual=plan.groupby("mes",as_index=False)["fte_atual"].sum()
    fig.add_trace(go.Scatter(x=actual["mes"],y=actual["fte_atual"],name="FTE atual",mode="lines",line=dict(color="#9BA3AD",dash="dash",width=2)))
    return base_layout(fig,355,"FTE")


def vehicle_capacity(vehicle: pd.DataFrame) -> go.Figure:
    d=vehicle.groupby("tipo_veiculo",as_index=False).agg(
        demanda=("demanda_caixas","mean"),
        capacidade=("capacidade_total","mean"),
        adicional=("novo_volume_tipo","sum")
    )
    fig=go.Figure()
    fig.add_trace(go.Bar(x=d["tipo_veiculo"],y=d["demanda"],name="Demanda apropriada",marker_color=JAMEF_RED))
    fig.add_trace(go.Bar(x=d["tipo_veiculo"],y=d["capacidade"],name="Capacidade atual",marker_color="#B7BDC5"))
    fig.update_layout(barmode="group")
    return base_layout(fig,350,"Caixas/dia")


def waterfall(fin: dict) -> go.Figure:
    labels=["EBITDA atual","Δ margem","Pessoas","Frota","Outros custos","EBITDA projetado"]
    values=[fin["ebitda_base"],fin["margem_delta"],-(fin["custo_he"]+fin["custo_terceiro"]+fin["custo_fte"]),-fin["custo_veiculos"],-fin["outros"],fin["ebitda_final"]]
    measures=["absolute","relative","relative","relative","relative","total"]
    fig=go.Figure(go.Waterfall(
        x=labels,y=values,measure=measures,
        increasing={"marker":{"color":JAMEF_GREEN}},
        decreasing={"marker":{"color":JAMEF_RED}},
        totals={"marker":{"color":JAMEF_BLACK}},
        connector={"line":{"color":"#B8BDC4"}},
        text=[f"R$ {v/1e6:.1f} mi" for v in values],textposition="outside",
    ))
    return base_layout(fig,345,"R$")


def scenario_compare(rows: list[tuple[str,float]]) -> go.Figure:
    names=[r[0] for r in rows]; vals=[r[1] for r in rows]
    colors=[JAMEF_RED if n=="Cenário Base" else (JAMEF_GREEN if n=="Otimista" else (JAMEF_AMBER if n=="Peak Season" else "#7D848D")) for n in names]
    fig=go.Figure(go.Bar(x=vals,y=names,orientation="h",marker_color=colors,text=[f"R$ {v/1e6:.1f} mi" for v in vals],textposition="outside"))
    fig.update_layout(showlegend=False)
    return base_layout(fig,330,"R$")
