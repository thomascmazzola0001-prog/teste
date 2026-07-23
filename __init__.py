from __future__ import annotations
import numpy as np
import pandas as pd
from .data import FORECAST_START, FORECAST_END


def _priority_score(series: pd.Series) -> np.ndarray:
    return series.map({"Alta":3.0,"Média":2.0,"Baixa":1.0}).fillna(1.0).to_numpy()


def _allocate_with_caps(capacity: np.ndarray, weight: np.ndarray, target: float) -> np.ndarray:
    allocation=np.zeros(len(capacity),dtype=float)
    remaining=float(target)
    active=capacity>1e-9
    for _ in range(20):
        if remaining<=1e-8 or not active.any():
            break
        w=np.where(active,weight,0.0)
        if w.sum()<=1e-9:
            w=np.where(active,1.0,0.0)
        proposal=remaining*w/w.sum()
        room=capacity-allocation
        add=np.minimum(proposal,np.maximum(room,0))
        allocation+=add
        remaining-=add.sum()
        active=(capacity-allocation)>1e-8
    return allocation


def apply_demand(
    demand: pd.DataFrame,
    restrictions: pd.DataFrame,
    branch_premises: pd.DataFrame,
    scenario_settings: pd.DataFrame,
    scenario: str,
    recomposition: str,
    global_override: float=0.0,
    global_floor: float|None=None,
) -> pd.DataFrame:
    df=demand.loc[demand["data"].between(FORECAST_START,FORECAST_END)].copy()
    s=scenario_settings.loc[scenario_settings["cenario"].eq(scenario)].iloc[0]
    df=df.merge(restrictions,on=["filial","cliente"],how="left",suffixes=("","_r"))
    df["previsao_cenario"]=df["previsao_caixas"]*float(s["multiplicador_demanda"])
    effective_override=df["override_pct"].fillna(0)+global_override
    df["demanda_pos_override"]=(df["previsao_cenario"]*(1+effective_override.clip(-95,300)/100)).clip(lower=0)
    active=df["aplicar"].fillna(False).astype(bool)&df["data"].between(
        pd.to_datetime(df["vigencia_inicio"]),pd.to_datetime(df["vigencia_fim"])
    )
    extra=np.where(df["tipo_negocio"].eq("B2C"),float(s["restricao_b2c_adicional_pct"]),0)
    df["restricao_efetiva_pct"]=np.where(active,(df["restricao_pct"].fillna(0)+extra).clip(0,100),0)
    after_pct=df["demanda_pos_override"]*(1-df["restricao_efetiva_pct"]/100)
    cap=np.where(active&df["limite_diario_caixas"].fillna(0).gt(0),df["limite_diario_caixas"],np.inf)
    df["demanda_apos_restricao"]=np.minimum(after_pct,cap).clip(lower=0)

    floor=branch_premises[["filial","piso_demanda_pct"]].copy()
    if global_floor is not None:
        floor["piso_demanda_pct"]=float(global_floor)
    df=df.merge(floor,on="filial",how="left")
    daily=df.groupby(["data","filial"],as_index=False).agg(
        bruto_filial=("demanda_pos_override","sum"),
        restrito_filial=("demanda_apos_restricao","sum"),
        piso_pct=("piso_demanda_pct","first"),
    )
    daily["piso_caixas"]=daily["bruto_filial"]*daily["piso_pct"]/100
    df=df.merge(daily[["data","filial","bruto_filial","restrito_filial","piso_caixas"]],
                on=["data","filial"],how="left")

    out=[]
    for (_, _),g in df.groupby(["data","filial"],sort=False):
        g=g.copy()
        short=max(float(g["piso_caixas"].iloc[0])-float(g["demanda_apos_restricao"].sum()),0)
        available=(g["demanda_pos_override"]-g["demanda_apos_restricao"]).clip(lower=0)
        if short>1e-8 and available.sum()>1e-8:
            if recomposition=="Prioridade estratégica":
                weights=available.to_numpy()*_priority_score(g["prioridade"])
            elif recomposition=="Maior margem":
                weights=available.to_numpy()*g["margem_pct"].clip(lower=1).to_numpy()
            elif recomposition=="B2B primeiro":
                weights=available.to_numpy()*np.where(g["tipo_negocio"].eq("B2B"),3.0,1.0)
            else:
                weights=available.to_numpy()
            allocation=_allocate_with_caps(available.to_numpy(),weights,short)
        else:
            allocation=np.zeros(len(g))
        g["recomposicao_piso"]=allocation
        g["demanda_final"]=g["demanda_apos_restricao"]+allocation
        g["piso_acionado"]=short>1e-8
        out.append(g)
    final=pd.concat(out,ignore_index=True)
    final["receita_pos_override"]=final["demanda_pos_override"]*final["receita_caixa"]
    final["receita_final"]=final["demanda_final"]*final["receita_caixa"]
    final["receita_em_risco"]=(final["receita_pos_override"]-final["receita_final"]).clip(lower=0)
    final["margem_pos_override"]=final["receita_pos_override"]*final["margem_pct"]/100
    final["margem_final"]=final["receita_final"]*final["margem_pct"]/100
    final["volume_restringido"]=(final["demanda_pos_override"]-final["demanda_final"]).clip(lower=0)
    return final


def build_flow(demand: pd.DataFrame, branch: pd.DataFrame) -> pd.DataFrame:
    coleta=demand.groupby(["data","origem"],as_index=False)["demanda_final"].sum()
    coleta.columns=["data","filial","demanda_caixas"]; coleta["processo"]="Coleta"
    entrega=demand.groupby(["data","destino"],as_index=False)["demanda_final"].sum()
    entrega.columns=["data","filial","demanda_caixas"]; entrega["processo"]="Entrega"
    trans=pd.concat([coleta,entrega]).groupby(["data","filial"],as_index=False)["demanda_caixas"].sum()
    trans=trans.merge(branch[["filial","fator_transbordo_pct"]],on="filial",how="left")
    trans["demanda_caixas"]*=trans["fator_transbordo_pct"]/100
    trans["processo"]="Transbordo"
    flow=pd.concat([coleta,trans[["data","filial","demanda_caixas","processo"]],entrega],ignore_index=True)
    flow=flow.merge(branch,on="filial",how="left")
    capmap={"Coleta":"cap_coleta_caixas_dia","Transbordo":"cap_transbordo_caixas_dia","Entrega":"cap_entrega_caixas_dia"}
    flow["capacidade_piso_fisico"]=[r[capmap[r["processo"]]] for _,r in flow.iterrows()]
    return flow


def calculate_people(flow: pd.DataFrame, premise: pd.DataFrame, scenario_settings: pd.DataFrame, scenario: str) -> pd.DataFrame:
    df=flow.merge(premise,on=["filial","processo"],how="left")
    s=scenario_settings.loc[scenario_settings["cenario"].eq(scenario)].iloc[0]
    prod=df["produtividade_caixas_hora"]*float(s["multiplicador_produtividade"])
    eff=df["eficiencia_pct"]/100
    avail=1-df["absenteismo_pct"]/100
    df["capacidade_fte_dia"]=df["horas_produtivas_dia"]*prod*eff*avail
    df["capacidade_regular"]=df["fte_atual"]*df["capacidade_fte_dia"]
    df["capacidade_limitante"]=np.minimum(df["capacidade_regular"],df["capacidade_piso_fisico"])
    df["fte_necessario"]=np.divide(df["demanda_caixas"],df["capacidade_fte_dia"],
        out=np.zeros(len(df)),where=df["capacidade_fte_dia"].to_numpy()>0)
    df["gap_fte"]=df["fte_necessario"]-df["fte_atual"]
    deficit=(df["demanda_caixas"]-df["capacidade_limitante"]).clip(lower=0)
    prod_h=prod*eff*avail
    he_need=np.divide(deficit,prod_h,out=np.zeros(len(df)),where=prod_h.to_numpy()>0)
    he_limit=df["fte_atual"]*df["limite_he_hora_fte_dia"]
    df["he_horas"]=np.minimum(he_need,he_limit)
    cap_he=df["he_horas"]*prod_h
    residual=(deficit-cap_he).clip(lower=0)
    df["terceiro_horas"]=np.divide(residual,prod_h,out=np.zeros(len(df)),where=prod_h.to_numpy()>0)
    cost_mult=float(s["multiplicador_custos"])
    df["custo_he"]=df["he_horas"]*df["custo_he_hora"]*cost_mult
    df["custo_terceiro"]=df["terceiro_horas"]*df["custo_terceiro_hora"]*cost_mult
    df["utilizacao_pct"]=np.divide(df["demanda_caixas"],df["capacidade_limitante"],
        out=np.zeros(len(df)),where=df["capacidade_limitante"].to_numpy()>0)*100
    return df


def people_plan(people: pd.DataFrame) -> pd.DataFrame:
    df=people.copy()
    df["mes"]=df["data"].dt.to_period("M").dt.to_timestamp()
    out=df.groupby(["mes","filial","processo","funcao"],as_index=False).agg(
        fte_atual=("fte_atual","mean"),
        fte_necessario_medio=("fte_necessario","mean"),
        fte_necessario_pico=("fte_necessario","max"),
        custo_mensal_fte=("custo_mensal_fte","first"),
        custo_he=("custo_he","sum"),
        custo_terceiro=("custo_terceiro","sum"),
    )
    out["gap_medio"]=out["fte_necessario_medio"]-out["fte_atual"]
    out["contratar"]=np.ceil(out["gap_medio"].clip(lower=0)).astype(int)
    out["realocar_reduzir"]=np.floor((-out["gap_medio"]).clip(lower=0)).astype(int)
    out["custo_fte_adicional"]=out["contratar"]*out["custo_mensal_fte"]
    return out


def calculate_vehicles(flow: pd.DataFrame, premise: pd.DataFrame, scenario_settings: pd.DataFrame, scenario: str) -> pd.DataFrame:
    delivery=flow.loc[flow["processo"].eq("Entrega")].groupby(["data","filial"],as_index=False)["demanda_caixas"].sum()
    v=premise.copy()
    s=scenario_settings.loc[scenario_settings["cenario"].eq(scenario)].iloc[0]
    v["capacidade_unitaria"]=v["drop_size_caixas_parada"]*v["paradas_viagem"]*v["viagens_dia"]*(v["ocupacao_pct"]/100)*(v["disponibilidade_pct"]/100)
    v["capacidade_frota"]=v["capacidade_unitaria"]*v["frota_atual"]
    total=v.groupby("filial",as_index=False).agg(capacidade_total=("capacidade_frota","sum"),share_total=("apropriacao_novo_volume_pct","sum"))
    df=delivery.merge(total,on="filial",how="left").merge(v,on="filial",how="left")
    df["delta_volume"]=df["demanda_caixas"]-df["capacidade_total"]
    df["share_normalizado"]=np.divide(df["apropriacao_novo_volume_pct"],df["share_total"],
        out=np.zeros(len(df)),where=df["share_total"].to_numpy()>0)
    df["novo_volume_tipo"]=df["delta_volume"].clip(lower=0)*df["share_normalizado"]
    df["ociosidade_tipo"]=(-df["delta_volume"]).clip(lower=0)*df["share_normalizado"]
    df["veiculos_adicionais"]=np.ceil(np.divide(df["novo_volume_tipo"],df["capacidade_unitaria"],
        out=np.zeros(len(df)),where=df["capacidade_unitaria"].to_numpy()>0)).astype(int)
    df["veiculos_reduziveis"]=np.floor(np.divide(df["ociosidade_tipo"],df["capacidade_unitaria"],
        out=np.zeros(len(df)),where=df["capacidade_unitaria"].to_numpy()>0)).astype(int)
    df["veiculos_reduziveis"]=np.minimum(df["veiculos_reduziveis"],df["frota_atual"])
    df["frota_sugerida"]=(df["frota_atual"]+df["veiculos_adicionais"]-df["veiculos_reduziveis"]).clip(lower=0)
    df["custo_incremental"]=(df["veiculos_adicionais"]-df["veiculos_reduziveis"])*df["custo_diaria"]*float(s["multiplicador_custos"])
    return df


def financials(demand: pd.DataFrame, people: pd.DataFrame, plan: pd.DataFrame, vehicles: pd.DataFrame, premise: pd.DataFrame) -> dict:
    p=premise.set_index("parametro")["valor"].to_dict()
    months=max(1,demand["data"].dt.to_period("M").nunique())
    revenue_base=float(demand["receita_pos_override"].sum())
    revenue_final=float(demand["receita_final"].sum())
    margin_delta=float((demand["margem_final"]-demand["margem_pos_override"]).sum())
    he=float(people["custo_he"].sum())
    third=float(people["custo_terceiro"].sum())
    fte=float(plan["custo_fte_adicional"].sum()+plan["contratar"].sum()*p.get("Custo de contratação por FTE",0)+plan["realocar_reduzir"].sum()*p.get("Custo de desligamento por FTE",0))
    vehicle=float(vehicles["custo_incremental"].sum())
    other=max(revenue_final,0)*p.get("Outros custos variáveis sobre receita (%)",0)/100
    base=float(p.get("EBITDA base mensal",0))*months
    impact=margin_delta-he-third-fte-vehicle-other
    return {
        "volume_base":float(demand["demanda_pos_override"].sum()),
        "volume_final":float(demand["demanda_final"].sum()),
        "receita_base":revenue_base,"receita_final":revenue_final,
        "receita_risco":max(revenue_base-revenue_final,0),
        "margem_delta":margin_delta,"custo_he":he,"custo_terceiro":third,
        "custo_fte":fte,"custo_veiculos":vehicle,"outros":other,
        "ebitda_base":base,"impacto_ebitda":impact,"ebitda_final":base+impact
    }


def run_scenario(data: dict, scenario: str, recomposition: str, global_override: float, global_floor: float) -> dict:
    d=apply_demand(data["demand"],data["restrictions"],data["branch_premises"],
        data["scenario_settings"],scenario,recomposition,global_override,global_floor)
    flow=build_flow(d,data["branch_premises"])
    people=calculate_people(flow,data["people_premises"],data["scenario_settings"],scenario)
    plan=people_plan(people)
    vehicles=calculate_vehicles(flow,data["vehicle_premises"],data["scenario_settings"],scenario)
    fin=financials(d,people,plan,vehicles,data["financial_premises"])
    return {"demand":d,"flow":flow,"people":people,"people_plan":plan,"vehicles":vehicles,"financial":fin}
