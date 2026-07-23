from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from .data import FORECAST_START, FORECAST_END


def _weighted_recomposition(df: pd.DataFrame, recomposition: str) -> pd.Series:
    keys=[df["data"],df["filial"]]
    available=(df["demanda_pos_override"]-df["demanda_apos_restricao"]).clip(lower=0)
    shortfall=(df["piso_caixas"]-df["restrito_filial"]).clip(lower=0)
    available_sum=available.groupby(keys).transform("sum")
    target=np.minimum(shortfall,available_sum)

    if recomposition=="Prioridade estratégica":
        score=df["prioridade"].map({"Alta":3.0,"Média":2.0,"Baixa":1.0}).fillna(1.0)
    elif recomposition=="Maior margem":
        score=df["margem_pct"].clip(lower=1.0)
    elif recomposition=="B2B primeiro":
        score=pd.Series(np.where(df["tipo_negocio"].eq("B2B"),3.0,1.0),index=df.index)
    else:
        score=pd.Series(1.0,index=df.index)

    weighted=available*score
    weighted_sum=weighted.groupby(keys).transform("sum")
    first_share=np.divide(weighted,weighted_sum,out=np.zeros(len(df)),where=weighted_sum.to_numpy()>0)
    first=np.minimum(target*first_share,available)

    first_group=pd.Series(first,index=df.index).groupby(keys).transform("sum")
    residual=(target-first_group).clip(lower=0)
    room=(available-first).clip(lower=0)
    room_sum=room.groupby(keys).transform("sum")
    second_share=np.divide(room,room_sum,out=np.zeros(len(df)),where=room_sum.to_numpy()>0)
    second=np.minimum(residual*second_share,room)
    return pd.Series(first+second,index=df.index)


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
    override=df["override_pct"].fillna(0)+float(global_override or 0)
    df["demanda_pos_override"]=(df["previsao_cenario"]*(1+override.clip(-95,300)/100)).clip(lower=0)

    active=df["aplicar"].fillna(False).astype(bool)&df["data"].between(
        pd.to_datetime(df["vigencia_inicio"]),pd.to_datetime(df["vigencia_fim"])
    )
    extra=np.where(df["tipo_negocio"].eq("B2C"),float(s["restricao_b2c_adicional_pct"]),0)
    df["restricao_efetiva_pct"]=np.where(active,(df["restricao_pct"].fillna(0)+extra).clip(0,100),0)
    after_pct=df["demanda_pos_override"]*(1-df["restricao_efetiva_pct"]/100)
    absolute_cap=np.where(active&df["limite_diario_caixas"].fillna(0).gt(0),df["limite_diario_caixas"],np.inf)
    df["demanda_apos_restricao"]=np.minimum(after_pct,absolute_cap).clip(lower=0)

    # O piso é obrigatoriamente tratado por filial. O parâmetro global_floor é
    # mantido apenas para compatibilidade com versões anteriores e não sobrescreve
    # a tabela de premissas.
    df=df.merge(branch_premises[["filial","piso_demanda_pct"]],on="filial",how="left")
    daily=df.groupby(["data","filial"],as_index=False).agg(
        bruto_filial=("demanda_pos_override","sum"),
        restrito_filial=("demanda_apos_restricao","sum"),
        piso_pct=("piso_demanda_pct","first"),
    )
    daily["piso_caixas"]=daily["bruto_filial"]*daily["piso_pct"]/100
    df=df.merge(daily[["data","filial","bruto_filial","restrito_filial","piso_caixas"]],on=["data","filial"],how="left")
    df["recomposicao_piso"]=_weighted_recomposition(df,recomposition)
    df["demanda_final"]=df["demanda_apos_restricao"]+df["recomposicao_piso"]
    df["piso_acionado"]=(df["piso_caixas"]-df["restrito_filial"])>1e-8
    df["receita_pos_override"]=df["demanda_pos_override"]*df["receita_caixa"]
    df["receita_final"]=df["demanda_final"]*df["receita_caixa"]
    df["receita_em_risco"]=(df["receita_pos_override"]-df["receita_final"]).clip(lower=0)
    df["margem_pos_override"]=df["receita_pos_override"]*df["margem_pct"]/100
    df["margem_final"]=df["receita_final"]*df["margem_pct"]/100
    df["volume_restringido"]=(df["demanda_pos_override"]-df["demanda_final"]).clip(lower=0)
    return df


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
    flow["capacidade_piso_fisico"]=[row[capmap[row["processo"]]] for _,row in flow.iterrows()]
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
    df["fte_necessario"]=np.divide(df["demanda_caixas"],df["capacidade_fte_dia"],out=np.zeros(len(df)),where=df["capacidade_fte_dia"].to_numpy()>0)
    df["gap_fte"]=df["fte_necessario"]-df["fte_atual"]
    deficit=(df["demanda_caixas"]-df["capacidade_limitante"]).clip(lower=0)
    prod_h=prod*eff*avail
    he_need=np.divide(deficit,prod_h,out=np.zeros(len(df)),where=prod_h.to_numpy()>0)
    he_limit=df["fte_atual"]*df["limite_he_hora_fte_dia"]
    df["he_horas"]=np.minimum(he_need,he_limit)
    residual=(deficit-df["he_horas"]*prod_h).clip(lower=0)
    df["terceiro_horas"]=np.divide(residual,prod_h,out=np.zeros(len(df)),where=prod_h.to_numpy()>0)
    cost_mult=float(s["multiplicador_custos"])
    df["custo_he"]=df["he_horas"]*df["custo_he_hora"]*cost_mult
    df["custo_terceiro"]=df["terceiro_horas"]*df["custo_terceiro_hora"]*cost_mult
    df["utilizacao_pct"]=np.divide(df["demanda_caixas"],df["capacidade_limitante"],out=np.zeros(len(df)),where=df["capacidade_limitante"].to_numpy()>0)*100
    return df


def people_plan(people: pd.DataFrame) -> pd.DataFrame:
    df=people.copy(); df["mes"]=df["data"].dt.to_period("M").dt.to_timestamp()
    out=df.groupby(["mes","filial","processo","funcao"],as_index=False).agg(
        fte_atual=("fte_atual","mean"),fte_necessario_medio=("fte_necessario","mean"),
        fte_necessario_pico=("fte_necessario","max"),custo_mensal_fte=("custo_mensal_fte","first"),
        custo_he=("custo_he","sum"),custo_terceiro=("custo_terceiro","sum"),
    )
    out["gap_medio"]=out["fte_necessario_medio"]-out["fte_atual"]
    out["necessidade_contratacao"]=np.ceil(out["gap_medio"].clip(lower=0)).astype(int)
    out["potencial_reducao"]=np.floor((-out["gap_medio"]).clip(lower=0)).astype(int)

    # Uma decisão de quadro não deve ser somada doze vezes. Registra-se uma única
    # ação por filial/processo/função, no primeiro mês, usando a maior necessidade
    # do horizonte. Os demais meses continuam exibindo a necessidade mensal.
    keys=["filial","processo","funcao"]
    first_month=out["mes"].eq(out.groupby(keys)["mes"].transform("min"))
    max_hire=out.groupby(keys)["necessidade_contratacao"].transform("max")
    max_reduce=out.groupby(keys)["potencial_reducao"].transform("max")
    out["contratar"]=np.where(first_month,max_hire,0).astype(int)
    out["realocar_reduzir"]=np.where(first_month,max_reduce,0).astype(int)
    out["custo_fte_adicional"]=out["contratar"]*out["custo_mensal_fte"]
    return out


def calculate_vehicles(flow: pd.DataFrame, premise: pd.DataFrame, scenario_settings: pd.DataFrame, scenario: str) -> pd.DataFrame:
    delivery=flow.loc[flow["processo"].eq("Entrega")].groupby(["data","filial"],as_index=False)["demanda_caixas"].sum()
    v=premise.copy(); s=scenario_settings.loc[scenario_settings["cenario"].eq(scenario)].iloc[0]
    v["capacidade_unitaria"]=v["drop_size_caixas_parada"]*v["paradas_viagem"]*v["viagens_dia"]*(v["ocupacao_pct"]/100)*(v["disponibilidade_pct"]/100)
    v["capacidade_frota"]=v["capacidade_unitaria"]*v["frota_atual"]
    total=v.groupby("filial",as_index=False).agg(capacidade_total=("capacidade_frota","sum"),share_total=("apropriacao_novo_volume_pct","sum"))
    df=delivery.merge(total,on="filial",how="left").merge(v,on="filial",how="left")
    df["delta_volume"]=df["demanda_caixas"]-df["capacidade_total"]
    df["share_normalizado"]=np.divide(df["apropriacao_novo_volume_pct"],df["share_total"],out=np.zeros(len(df)),where=df["share_total"].to_numpy()>0)
    df["novo_volume_tipo"]=df["delta_volume"].clip(lower=0)*df["share_normalizado"]
    df["ociosidade_tipo"]=(-df["delta_volume"]).clip(lower=0)*df["share_normalizado"]
    df["veiculos_adicionais"]=np.ceil(np.divide(df["novo_volume_tipo"],df["capacidade_unitaria"],out=np.zeros(len(df)),where=df["capacidade_unitaria"].to_numpy()>0)).astype(int)
    df["veiculos_reduziveis"]=np.floor(np.divide(df["ociosidade_tipo"],df["capacidade_unitaria"],out=np.zeros(len(df)),where=df["capacidade_unitaria"].to_numpy()>0)).astype(int)
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
    he=float(people["custo_he"].sum()); third=float(people["custo_terceiro"].sum())
    fte=float(plan["custo_fte_adicional"].sum()+plan["contratar"].sum()*p.get("Custo de contratação por FTE",0)+plan["realocar_reduzir"].sum()*p.get("Custo de desligamento por FTE",0))
    vehicle=float(vehicles["custo_incremental"].sum())
    # Apenas a variação de custos proporcionais entra na ponte, não o custo total
    # da receita ajustada.
    other=(revenue_final-revenue_base)*p.get("Outros custos variáveis sobre receita (%)",0)/100
    base=float(p.get("EBITDA base mensal",0))*months
    impact=margin_delta-he-third-fte-vehicle-other
    return {
        "volume_base":float(demand["demanda_pos_override"].sum()),"volume_final":float(demand["demanda_final"].sum()),
        "receita_base":revenue_base,"receita_final":revenue_final,"receita_risco":max(revenue_base-revenue_final,0),
        "margem_delta":margin_delta,"custo_he":he,"custo_terceiro":third,"custo_fte":fte,
        "custo_veiculos":vehicle,"outros":other,"ebitda_base":base,"impacto_ebitda":impact,"ebitda_final":base+impact,
    }


@st.cache_data(show_spinner=False)
def run_scenario(data: dict, scenario: str, recomposition: str, global_override: float, global_floor: float|None) -> dict:
    demand=apply_demand(data["demand"],data["restrictions"],data["branch_premises"],data["scenario_settings"],scenario,recomposition,global_override,global_floor)
    flow=build_flow(demand,data["branch_premises"])
    people=calculate_people(flow,data["people_premises"],data["scenario_settings"],scenario)
    plan=people_plan(people)
    vehicles=calculate_vehicles(flow,data["vehicle_premises"],data["scenario_settings"],scenario)
    fin=financials(demand,people,plan,vehicles,data["financial_premises"])
    return {"demand":demand,"flow":flow,"people":people,"people_plan":plan,"vehicles":vehicles,"financial":fin}
