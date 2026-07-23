from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st

from .data import BRANCHES, PROCESSES, FUNCTIONS, VEHICLES, SCENARIOS, export_excel
from .engine import run_scenario
from .components import page_header, section_title, kpi_card, stage_cards, note_box, rule_box
from .charts import CONFIG, demand_12m, demand_daily, history_forecast, people_daily, fte_monthly, vehicle_capacity, waterfall, scenario_compare
from .theme import JAMEF_RED


def fmt_num(v, d=0):
    return f"{v:,.{d}f}".replace(",","X").replace(".",",").replace("X",".")

def fmt_money(v):
    sign="-" if v<0 else ""
    return f"{sign}R$ {fmt_num(abs(v),0)}"

def fmt_mi(v):
    return f"{v/1_000_000:.2f}".replace(".",",")+" mi"


def data_dict():
    return {k:st.session_state[k] for k in [
        "demand","restrictions","branch_premises","people_premises",
        "vehicle_premises","financial_premises","scenario_settings"
    ]}


def period_bounds(label):
    start=pd.Timestamp("2026-08-01")
    months={"Próximos 3 meses":3,"Próximos 6 meses":6,"Próximos 12 meses":12}[label]
    return start,start+pd.DateOffset(months=months)-pd.Timedelta(days=1)


def filter_result(result):
    start,end=period_bounds(st.session_state.period)
    branches=st.session_state.branches
    for key in ["demand","flow","people","vehicles"]:
        if key in result:
            df=result[key]
            mask=df["data"].between(start,end)
            if "filial" in df.columns:
                mask &= df["filial"].isin(branches)
            result[key]=df.loc[mask].copy()
    p=result["people_plan"]
    result["people_plan"]=p.loc[p["filial"].isin(branches)&p["mes"].between(start,end)].copy()
    return result


def run_current():
    return filter_result(run_scenario(
        data_dict(),st.session_state.scenario,st.session_state.recomposition,
        st.session_state.global_override,st.session_state.global_floor
    ))


def top_filters(include_route=False, include_function=False, include_vehicle=False):
    with st.container(border=True):
        cols=st.columns([1.15,1.2,1.1,1.0,1.0]+([1.0] if include_route else [])+([1.0] if include_function else [])+([1.0] if include_vehicle else [])+[.65])
        idx=0
        st.session_state.scenario=cols[idx].selectbox("Cenário",SCENARIOS,index=SCENARIOS.index(st.session_state.scenario)); idx+=1
        st.session_state.branches=cols[idx].multiselect("Filiais",BRANCHES,default=st.session_state.branches); idx+=1
        st.session_state.period=cols[idx].selectbox("Período",["Próximos 3 meses","Próximos 6 meses","Próximos 12 meses"],index=["Próximos 3 meses","Próximos 6 meses","Próximos 12 meses"].index(st.session_state.period)); idx+=1
        st.session_state.view=cols[idx].selectbox("Visão",["Diária","Semanal","Mensal"],index=["Diária","Semanal","Mensal"].index(st.session_state.view)); idx+=1
        recomps=["Proporcional","Prioridade estratégica","Maior margem","B2B primeiro"]
        st.session_state.recomposition=cols[idx].selectbox("Recomposição do piso",recomps,index=recomps.index(st.session_state.recomposition)); idx+=1
        route="Todas"
        if include_route:
            route=cols[idx].selectbox("Rota",["Todas"]+sorted(st.session_state.demand["rota"].unique().tolist())); idx+=1
        function="Todas"
        if include_function:
            function=cols[idx].selectbox("Função",["Todas"]+FUNCTIONS); idx+=1
        vehicle="Todos"
        if include_vehicle:
            vehicle=cols[idx].selectbox("Tipo de veículo",["Todos"]+VEHICLES); idx+=1
        if cols[idx].button("Recalcular",type="primary",use_container_width=True):
            st.rerun()
    return {"route":route,"function":function,"vehicle":vehicle}


def resumo():
    page_header("01","Resumo Executivo","Consolidação das decisões de demanda, capacidade, frota e resultado do ciclo.")
    top_filters()
    stage_cards(5)
    result=run_current(); d=result["demand"]; people=result["people"]; plan=result["people_plan"]; vehicles=result["vehicles"]; fin=result["financial"]
    hire=int(plan["contratar"].sum()); reduce=int(plan["realocar_reduzir"].sum())
    veh=int(vehicles.groupby(["filial","tipo_veiculo"])["veiculos_adicionais"].max().sum())
    cols=st.columns(7)
    cards=[
        ("MAPE do modelo","12,4%","últimos 12 meses",""),
        ("Demanda projetada",fmt_mi(fin["volume_final"])+" caixas","+2,3% vs. previsão","positive"),
        ("Headcount sugerido",f"+{hire} FTE",f"-{reduce} realocar/reduzir",""),
        ("Hora extra necessária",fmt_num(people["he_horas"].sum())+" h","próximo ciclo",""),
        ("Terceiros necessários",fmt_num(people["terceiro_horas"].sum())+" h","próximo ciclo",""),
        ("Veículos adicionais",f"+{veh}","pico do horizonte",""),
        ("Impacto no EBITDA",fmt_money(fin["impacto_ebitda"]),"vs. cenário base","negative" if fin["impacto_ebitda"]<0 else "positive"),
    ]
    for c,card in zip(cols,cards):
        with c:kpi_card(*card)
    st.write("")
    c1,c2,c3=st.columns([1.42,.82,1.02])
    with c1:
        section_title("Demanda ajustada — próximos 12 meses","PLANEJAMENTO")
        st.plotly_chart(demand_12m(d),use_container_width=True,config=CONFIG)
    with c2:
        section_title("Resumo de headcount","PESSOAS")
        summary=plan.groupby("funcao",as_index=False).agg(
            Atual=("fte_atual","mean"),Necessário=("fte_necessario_medio","mean"),
            Diferença=("gap_medio","mean")
        )
        summary[["Atual","Necessário","Diferença"]]=summary[["Atual","Necessário","Diferença"]].round(0)
        st.dataframe(summary,use_container_width=True,hide_index=True,height=280)
        note_box(f"Contratações sugeridas: <b>{hire}</b><br>Realocações/reduções potenciais: <b>{reduce}</b>")
    with c3:
        section_title("Impacto no EBITDA","RESULTADO")
        st.plotly_chart(waterfall(fin),use_container_width=True,config=CONFIG)
    section_title("Decisões para o fórum executivo","GOVERNANÇA")
    decisions=[]
    top_people=plan.groupby(["filial","funcao"],as_index=False).agg(contratar=("contratar","max"),custo=("custo_he","sum"))
    for _,r in top_people.sort_values("contratar",ascending=False).head(5).iterrows():
        if r["contratar"]>0:
            decisions.append(["Aprovar cobertura de FTE",r["filial"],f"{int(r['contratar'])} {r['funcao'].lower()}(s)",fmt_money(r["custo"]),"Operações","Pendente"])
    rv=vehicles.groupby(["filial","tipo_veiculo"],as_index=False).agg(adicionar=("veiculos_adicionais","max"),custo=("custo_incremental","sum"))
    for _,r in rv.sort_values("adicionar",ascending=False).head(4).iterrows():
        if r["adicionar"]>0:
            decisions.append(["Contratar frota flexível",r["filial"],f"{int(r['adicionar'])} {r['tipo_veiculo']}",fmt_money(r["custo"]),"Frota","Em análise"])
    risks=d.groupby(["filial","cliente"],as_index=False).agg(receita_risco=("receita_em_risco","sum"))
    for _,r in risks.nlargest(3,"receita_risco").iterrows():
        if r["receita_risco"]>0:
            decisions.append(["Revisar restrição comercial",r["filial"],r["cliente"],fmt_money(r["receita_risco"]),"Comercial","Em análise"])
    st.dataframe(pd.DataFrame(decisions,columns=["Decisão","Filial","Detalhe","Impacto","Responsável","Status"]),use_container_width=True,hide_index=True)


def demanda():
    page_header("02","Demanda & Restrições B2C","Previsão, overrides, limites por cliente, passagem e piso mínimo por filial.")
    f=top_filters(include_route=True)
    result=run_current(); d=result["demand"]; flow=result["flow"]; people=result["people"]
    if f["route"]!="Todas": d=d.loc[d["rota"].eq(f["route"])]
    tabs=st.tabs(["Previsão de demanda","Passagem: coleta / transbordo / entrega","Clientes & restrições B2C","Piso por filial"])
    with tabs[0]:
        cols=st.columns(5)
        metrics=[
            ("Previsão bruta",fmt_mi(d["demanda_pos_override"].sum())+" cx","após override",""),
            ("Demanda ajustada",fmt_mi(d["demanda_final"].sum())+" cx","após restrições e piso",""),
            ("Volume restringido",fmt_num(d["volume_restringido"].sum())+" cx","capacidade retirada",""),
            ("Receita em risco",fmt_money(d["receita_em_risco"].sum()),"efeito das restrições","negative"),
            ("Filial-dia com piso",str(d.groupby(["data","filial"])["piso_acionado"].first().sum()),"piso acionado",""),
        ]
        for c,x in zip(cols,metrics):
            with c:kpi_card(*x)
        c1,c2=st.columns([1.22,.78])
        with c1:
            section_title("Previsão diária, restrição e piso","DEMANDA")
            st.plotly_chart(demand_daily(d),use_container_width=True,config=CONFIG)
        with c2:
            section_title("Histórico e previsão ajustada","ACURÁCIA")
            st.plotly_chart(history_forecast(st.session_state.demand,d),use_container_width=True,config=CONFIG)
        rule_box("Ordem de cálculo",[
            "1. Previsão estatística × cenário.",
            "2. Aplicação do override comercial.",
            "3. Aplicação da restrição percentual e/ou limite diário.",
            "4. Comparação com o piso mínimo da filial.",
            "5. Recomposição do volume conforme o método selecionado."
        ])
    with tabs[1]:
        table=people.groupby(["filial","processo"],as_index=False).agg(
            Demanda=("demanda_caixas","sum"),Capacidade=("capacidade_limitante","sum"),
            Utilização=("utilizacao_pct","mean")
        )
        table["Gap"]=table["Capacidade"]-table["Demanda"]
        pivot=table.pivot(index="filial",columns="processo",values=["Demanda","Capacidade","Gap","Utilização"])
        pivot.columns=[f"{a} | {b}" for a,b in pivot.columns]
        st.dataframe(pivot.reset_index(),use_container_width=True,hide_index=True,height=420)
        note_box("A capacidade operacional considera simultaneamente a capacidade calculada por pessoas e a restrição física de piso da filial. O menor valor entre as duas é tratado como capacidade limitante.")
    with tabs[2]:
        editable=st.session_state.restrictions.copy()
        editable=editable.loc[editable["filial"].isin(st.session_state.branches)]
        edited=st.data_editor(
            editable,use_container_width=True,hide_index=True,height=480,
            disabled=["filial","cliente","b2c_pct","prioridade"],
            column_config={
                "b2c_pct":st.column_config.NumberColumn("% B2C",format="%.1f%%"),
                "override_pct":st.column_config.NumberColumn("Override (%)",min_value=-95.,max_value=300.,format="%.1f%%"),
                "restricao_pct":st.column_config.NumberColumn("Restrição (%)",min_value=0.,max_value=100.,format="%.1f%%"),
                "limite_diario_caixas":st.column_config.NumberColumn("Limite diário",min_value=0.,format="%.0f"),
                "aplicar":st.column_config.CheckboxColumn("Aplicar"),
            },
            key="restriction_editor_v3"
        )
        if st.button("Salvar overrides e restrições",type="primary"):
            base=st.session_state.restrictions.set_index(["filial","cliente"])
            base.update(edited.set_index(["filial","cliente"]))
            st.session_state.restrictions=base.reset_index()
            st.success("Regras atualizadas.")
    with tabs[3]:
        edited=st.data_editor(
            st.session_state.branch_premises,use_container_width=True,hide_index=True,
            disabled=["filial"],height=380,
            column_config={
                "piso_demanda_pct":st.column_config.NumberColumn("Piso mínimo (%)",min_value=0.,max_value=100.,format="%.1f%%"),
                "fator_transbordo_pct":st.column_config.NumberColumn("Fator transbordo (%)",min_value=0.,max_value=200.,format="%.1f%%"),
            },key="branch_floor_editor"
        )
        if st.button("Salvar piso por filial",type="primary"):
            st.session_state.branch_premises=edited
            st.session_state.global_floor=float(edited["piso_demanda_pct"].mean())
            st.success("Premissas das filiais atualizadas.")
        st.plotly_chart(demand_daily(d),use_container_width=True,config=CONFIG)


def pessoas():
    page_header("03","Capacidade de Pessoas","Dimensionamento de ajudantes e conferentes por filial, processo, dia e mês.")
    f=top_filters(include_function=True)
    r=run_current(); p=r["people"]; plan=r["people_plan"]
    if f["function"]!="Todas":
        p=p.loc[p["funcao"].eq(f["function"])]; plan=plan.loc[plan["funcao"].eq(f["function"])]
    cols=st.columns(7)
    vals=[
        ("FTE atual",fmt_num(p.groupby(["filial","processo","funcao"])["fte_atual"].first().sum()),"quadro disponível",""),
        ("FTE necessário médio",fmt_num(plan["fte_necessario_medio"].sum()),"demanda do ciclo",""),
        ("FTE no pico",fmt_num(plan["fte_necessario_pico"].sum()),"maior necessidade",""),
        ("Contratar",f"+{int(plan['contratar'].sum())}","efetivo/temporário","negative"),
        ("Realocar/reduzir",f"-{int(plan['realocar_reduzir'].sum())}","potencial","positive"),
        ("Hora extra",fmt_num(p["he_horas"].sum())+" h","capacidade transitória",""),
        ("Terceiros",fmt_num(p["terceiro_horas"].sum())+" h","capacidade residual",""),
    ]
    for c,x in zip(cols,vals):
        with c:kpi_card(*x)
    c1,c2=st.columns([1.12,1])
    with c1:
        section_title("Capacidade x demanda — visão diária","OPERAÇÃO")
        st.plotly_chart(people_daily(p),use_container_width=True,config=CONFIG)
    with c2:
        section_title("Necessidade de pessoas — visão mensal","HEADCOUNT")
        st.plotly_chart(fte_monthly(plan),use_container_width=True,config=CONFIG)
    section_title("Plano sugerido de headcount","DECISÃO")
    display=plan.copy()
    display["Ação"]="Manter"
    display.loc[display["contratar"].gt(0),"Ação"]="Contratar / temporarizar"
    display.loc[display["realocar_reduzir"].gt(0),"Ação"]="Realocar / reduzir"
    st.dataframe(display[["mes","filial","processo","funcao","fte_atual","fte_necessario_medio","fte_necessario_pico","gap_medio","contratar","realocar_reduzir","custo_he","custo_terceiro","Ação"]],use_container_width=True,hide_index=True,height=390)


def veiculos():
    page_header("04","Frota & Veículos","Apropriação dos novos volumes por tipo de veículo utilizando drop size e capacidade diária.")
    f=top_filters(include_vehicle=True)
    st.markdown("##### Premissas de frota por filial e tipo")
    edited=st.data_editor(
        st.session_state.vehicle_premises,use_container_width=True,hide_index=True,height=330,
        disabled=["filial","tipo_veiculo"],
        column_config={
            "drop_size_caixas_parada":st.column_config.NumberColumn("Drop size (cx/parada)",min_value=1.),
            "paradas_viagem":st.column_config.NumberColumn("Paradas/viagem",min_value=1.),
            "viagens_dia":st.column_config.NumberColumn("Viagens/dia",min_value=.1),
            "ocupacao_pct":st.column_config.NumberColumn("Ocupação",min_value=1.,max_value=100.,format="%.1f%%"),
            "disponibilidade_pct":st.column_config.NumberColumn("Disponibilidade",min_value=1.,max_value=100.,format="%.1f%%"),
            "apropriacao_novo_volume_pct":st.column_config.NumberColumn("% novo volume",min_value=0.,max_value=100.,format="%.1f%%"),
            "custo_diaria":st.column_config.NumberColumn("Custo diário",min_value=0.,format="R$ %.2f")
        },key="vehicle_editor_v3")
    if st.button("Salvar premissas de frota",type="primary"):
        st.session_state.vehicle_premises=edited
        st.success("Premissas atualizadas.")
    check=edited.groupby("filial")["apropriacao_novo_volume_pct"].sum()
    if (~check.between(99.9,100.1)).any():
        st.warning("A soma da apropriação por filial deve ser 100%. O motor normaliza os percentuais apenas para a simulação.")
    r=run_current(); v=r["vehicles"]
    if f["vehicle"]!="Todos": v=v.loc[v["tipo_veiculo"].eq(f["vehicle"])]
    cols=st.columns(6)
    peak=v.groupby(["filial","tipo_veiculo"])["veiculos_adicionais"].max()
    reduce=v.groupby(["filial","tipo_veiculo"])["veiculos_reduziveis"].max()
    vals=[
        ("Frota atual",fmt_num(v.groupby(["filial","tipo_veiculo"])["frota_atual"].first().sum()),"veículos disponíveis",""),
        ("Frota sugerida",fmt_num(v.groupby(["filial","tipo_veiculo"])["frota_sugerida"].max().sum()),"pico do período",""),
        ("Veículos adicionais",f"+{int(peak.sum())}","necessidade máxima","negative"),
        ("Veículos reduzíveis",f"-{int(reduce.sum())}","ociosidade potencial","positive"),
        ("Novo volume",fmt_num(v["novo_volume_tipo"].sum())+" cx","apropriado por tipo",""),
        ("Custo incremental",fmt_money(v["custo_incremental"].sum()),"horizonte selecionado",""),
    ]
    for c,x in zip(cols,vals):
        with c:kpi_card(*x)
    c1,c2=st.columns([1.15,1])
    with c1:
        section_title("Demanda versus capacidade por tipo","CAPACIDADE")
        st.plotly_chart(vehicle_capacity(v),use_container_width=True,config=CONFIG)
    with c2:
        section_title("Frota sugerida","DIMENSIONAMENTO")
        summary=v.groupby(["filial","tipo_veiculo"],as_index=False).agg(
            Frota_atual=("frota_atual","first"),
            Capacidade_unitária=("capacidade_unitaria","first"),
            Drop_size=("drop_size_caixas_parada","first"),
            Adicionar=("veiculos_adicionais","max"),
            Reduzir=("veiculos_reduziveis","max"),
            Frota_sugerida=("frota_sugerida","max"),
            Custo_incremental=("custo_incremental","sum"),
        )
        st.dataframe(summary,use_container_width=True,hide_index=True,height=330)
    rule_box("Regra de dimensionamento",[
        "Capacidade unitária = drop size × paradas/viagem × viagens/dia × ocupação × disponibilidade.",
        "Novo volume = demanda de entrega – capacidade da frota atual.",
        "O novo volume é distribuído pela participação de cada tipo de veículo.",
        "Veículos adicionais = teto do novo volume apropriado ÷ capacidade unitária."
    ])


def financeiro():
    page_header("05","Financeiro & EBITDA","Conciliação da receita, margem, pessoas, frota e demais custos do cenário.")
    top_filters()
    r=run_current(); fin=r["financial"]; d=r["demand"]
    cols=st.columns(7)
    vals=[
        ("Receita base",fmt_money(fin["receita_base"]),"pré-restrição",""),
        ("Receita ajustada",fmt_money(fin["receita_final"]),"cenário final",""),
        ("Receita em risco",fmt_money(fin["receita_risco"]),"efeito das restrições","negative"),
        ("Custo de pessoas",fmt_money(fin["custo_he"]+fin["custo_terceiro"]+fin["custo_fte"]),"HE + terceiros + FTE",""),
        ("Custo de veículos",fmt_money(fin["custo_veiculos"]),"frota incremental",""),
        ("Impacto EBITDA",fmt_money(fin["impacto_ebitda"]),"variação do cenário","negative" if fin["impacto_ebitda"]<0 else "positive"),
        ("EBITDA projetado",fmt_money(fin["ebitda_final"]),"resultado final",""),
    ]
    for c,x in zip(cols,vals):
        with c:kpi_card(*x)
    c1,c2,c3=st.columns([1.1,.8,1])
    with c1:
        section_title("Impacto no EBITDA","PONTE FINANCEIRA")
        st.plotly_chart(waterfall(fin),use_container_width=True,config=CONFIG)
    with c2:
        section_title("Resumo financeiro","DRE SIMPLIFICADA")
        table=pd.DataFrame({
            "Descrição":["Receita base","Receita ajustada","Δ margem","Hora extra","Terceiros","FTE adicional","Frota","Outros custos","EBITDA projetado"],
            "Valor":[fin["receita_base"],fin["receita_final"],fin["margem_delta"],-fin["custo_he"],-fin["custo_terceiro"],-fin["custo_fte"],-fin["custo_veiculos"],-fin["outros"],fin["ebitda_final"]]
        })
        table["Valor formatado"]=table["Valor"].map(fmt_money)
        st.dataframe(table[["Descrição","Valor formatado"]],use_container_width=True,hide_index=True,height=330)
    with c3:
        section_title("Comparação de cenários","SIMULAÇÃO")
        rows=[]
        original=st.session_state.scenario
        for sc in SCENARIOS:
            tmp=run_scenario(data_dict(),sc,st.session_state.recomposition,st.session_state.global_override,st.session_state.global_floor)
            rows.append((sc,tmp["financial"]["ebitda_final"]))
        st.plotly_chart(scenario_compare(rows),use_container_width=True,config=CONFIG)
    section_title("Resultado por filial","ANÁLISE")
    branch=d.groupby("filial",as_index=False).agg(
        Volume_base=("demanda_pos_override","sum"),Volume_final=("demanda_final","sum"),
        Receita_base=("receita_pos_override","sum"),Receita_final=("receita_final","sum"),
        Receita_em_risco=("receita_em_risco","sum"),Margem_final=("margem_final","sum")
    )
    st.dataframe(branch,use_container_width=True,hide_index=True)


def premises():
    page_header("06","Premissas & Governança","Administração das regras, produtividade, capacidade, custos e qualidade dos dados.")
    tabs=st.tabs(["Filiais e piso","Pessoas","Veículos","Financeiro","Cenários","Exportação"])
    with tabs[0]:
        st.session_state.branch_premises=st.data_editor(st.session_state.branch_premises,use_container_width=True,hide_index=True,key="prem_branch")
    with tabs[1]:
        st.session_state.people_premises=st.data_editor(st.session_state.people_premises,use_container_width=True,hide_index=True,key="prem_people",height=460)
    with tabs[2]:
        st.session_state.vehicle_premises=st.data_editor(st.session_state.vehicle_premises,use_container_width=True,hide_index=True,key="prem_vehicle",height=460)
    with tabs[3]:
        st.session_state.financial_premises=st.data_editor(st.session_state.financial_premises,use_container_width=True,hide_index=True,key="prem_fin")
    with tabs[4]:
        st.session_state.scenario_settings=st.data_editor(st.session_state.scenario_settings,use_container_width=True,hide_index=True,key="prem_scenario")
    with tabs[5]:
        tables=data_dict()
        st.download_button("Exportar todas as bases do cenário",data=export_excel(tables),file_name="SOP_Jamef_bases.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",type="primary")
        st.markdown("#### Governança recomendada")
        st.dataframe(pd.DataFrame([
            ["Override comercial","Comercial","Gerência Comercial","Obrigatória","Por alteração"],
            ["Restrição de cliente","S&OP + Comercial","Diretoria Comercial","Obrigatória","Por ciclo"],
            ["Piso por filial","Operação","Diretoria Operacional","Obrigatória","Mensal"],
            ["Produtividade","Operação","Gerência Operacional","Obrigatória","Mensal"],
            ["Custos","Financeiro","Controladoria","Obrigatória","Mensal"],
            ["Cenário final","S&OP","Fórum Executivo","Obrigatória","Por ciclo"],
        ],columns=["Objeto","Owner","Aprovador","Justificativa","Frequência"]),use_container_width=True,hide_index=True)


PAGES={
    "Resumo Executivo":resumo,
    "Demanda & Restrições":demanda,
    "Capacidade de Pessoas":pessoas,
    "Frota & Veículos":veiculos,
    "Financeiro & EBITDA":financeiro,
    "Premissas & Governança":premises,
}
