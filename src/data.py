from __future__ import annotations
from io import BytesIO
import numpy as np
import pandas as pd
import streamlit as st

BRANCHES = ["SÃO", "BHZ", "RIO", "CWB", "SSA", "REC", "FOR", "CGB"]
PROCESSES = ["Coleta", "Transbordo", "Entrega"]
FUNCTIONS = ["Ajudante", "Conferente"]
VEHICLES = ["VUC", "3/4", "Toco", "Truck", "Carreta"]
SCENARIOS = ["Cenário Base", "Peak Season", "Otimista", "Conservador"]

FORECAST_START = pd.Timestamp("2026-08-01")
FORECAST_END = pd.Timestamp("2027-07-31")


@st.cache_data(show_spinner=False)
def generate_demo_data(seed: int = 100) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    clients = [f"Cliente {chr(65+i)}" for i in range(18)]
    dates = pd.date_range("2026-01-01", FORECAST_END, freq="D")
    client_master = pd.DataFrame({
        "cliente": clients,
        "b2c_pct": rng.integers(5, 92, len(clients)),
        "receita_caixa": rng.uniform(17, 42, len(clients)).round(2),
        "margem_pct": rng.uniform(18, 45, len(clients)).round(1),
        "prioridade": rng.choice(["Alta", "Média", "Baixa"], len(clients), p=[.25,.5,.25]),
    })
    branch_factor = {"SÃO":1.50,"BHZ":1.05,"RIO":1.20,"CWB":.95,"SSA":.88,"REC":.82,"FOR":.78,"CGB":.60}
    rows = []
    for dt in dates:
        is_forecast = dt >= FORECAST_START
        season = 1 + .10*np.sin((dt.dayofyear/365)*2*np.pi)
        weekday = .62 if dt.weekday() >= 5 else 1.0
        peak = 1.26 if dt.month in (10,11,12) else 1.0
        for branch in BRANCHES:
            chosen = rng.choice(clients, 11, replace=False)
            for client in chosen:
                cm = client_master.loc[client_master["cliente"].eq(client)].iloc[0]
                dest = rng.choice([b for b in BRANCHES if b != branch])
                base = rng.gamma(5.5, 44) * branch_factor[branch] * season * weekday * peak
                actual = max(0, int(base * rng.normal(1, .06)))
                forecast = max(0, int(base * rng.normal(1.015, .055)))
                rows.append({
                    "data": dt, "cliente": client, "filial": branch,
                    "origem": branch, "destino": dest, "rota": f"{branch}->{dest}",
                    "tipo_negocio": "B2C" if cm["b2c_pct"] >= 50 else "B2B",
                    "b2c_pct": float(cm["b2c_pct"]),
                    "real_caixas": actual if not is_forecast else np.nan,
                    "previsao_caixas": forecast,
                    "receita_caixa": float(cm["receita_caixa"]),
                    "margem_pct": float(cm["margem_pct"]),
                    "prioridade": cm["prioridade"],
                })
    demand = pd.DataFrame(rows)
    demand["receita_prevista"] = demand["previsao_caixas"] * demand["receita_caixa"]

    restrictions = client_master.merge(pd.DataFrame({"filial": BRANCHES}), how="cross")
    restrictions["override_pct"] = 0.0
    restrictions["restricao_pct"] = np.where(restrictions["b2c_pct"] >= 65, 12.0, 0.0)
    restrictions["limite_diario_caixas"] = 0.0
    restrictions["aplicar"] = restrictions["restricao_pct"].gt(0)
    restrictions["motivo"] = np.where(restrictions["aplicar"], "Controle de capacidade em peak season", "")
    restrictions["vigencia_inicio"] = FORECAST_START
    restrictions["vigencia_fim"] = FORECAST_END
    restrictions = restrictions[[
        "filial","cliente","b2c_pct","prioridade","override_pct","restricao_pct",
        "limite_diario_caixas","aplicar","motivo","vigencia_inicio","vigencia_fim"
    ]]

    branch_premises = pd.DataFrame({
        "filial": BRANCHES,
        "piso_demanda_pct": [82,80,81,83,79,78,80,84],
        "fator_transbordo_pct": [56,52,54,50,47,48,49,45],
        "cap_coleta_caixas_dia": [30000,21000,25000,18000,14500,13500,13000,9500],
        "cap_transbordo_caixas_dia": [36000,24000,29000,21000,17000,16000,15500,11000],
        "cap_entrega_caixas_dia": [32000,22000,27000,19000,15500,14500,14000,10000],
    })

    people_rows = []
    for branch in BRANCHES:
        scale = branch_factor[branch]
        for process in PROCESSES:
            for function in FUNCTIONS:
                prod = {
                    ("Coleta","Ajudante"):112,("Coleta","Conferente"):180,
                    ("Transbordo","Ajudante"):148,("Transbordo","Conferente"):220,
                    ("Entrega","Ajudante"):105,("Entrega","Conferente"):168,
                }[(process,function)]
                people_rows.append({
                    "filial": branch, "processo": process, "funcao": function,
                    "fte_atual": int(max(4, rng.normal(16*scale, 2.5))),
                    "produtividade_caixas_hora": round(prod*rng.uniform(.92,1.08),1),
                    "horas_produtivas_dia": 7.2,
                    "eficiencia_pct": round(rng.uniform(80,91),1),
                    "absenteismo_pct": round(rng.uniform(3,7),1),
                    "limite_he_hora_fte_dia": 2.0,
                    "custo_mensal_fte": 5300 if function=="Ajudante" else 7100,
                    "custo_he_hora": 43 if function=="Ajudante" else 58,
                    "custo_terceiro_hora": 61 if function=="Ajudante" else 79,
                })
    people = pd.DataFrame(people_rows)

    vehicle_defaults = {
        "VUC":(18,28,2.1,720,24),
        "3/4":(30,25,1.8,980,24),
        "Toco":(44,22,1.5,1450,21),
        "Truck":(68,20,1.3,2200,21),
        "Carreta":(110,16,1.0,3400,10),
    }
    vehicle_rows=[]
    for branch in BRANCHES:
        scale=branch_factor[branch]
        for vehicle,(drop,stops,trips,cost,share) in vehicle_defaults.items():
            vehicle_rows.append({
                "filial":branch,"tipo_veiculo":vehicle,
                "drop_size_caixas_parada":float(drop),
                "paradas_viagem":float(stops),
                "viagens_dia":float(trips),
                "ocupacao_pct":86.0,
                "disponibilidade_pct":92.0,
                "frota_atual":int(max(1,rng.normal(9*scale,1.6))),
                "custo_diaria":float(cost),
                "apropriacao_novo_volume_pct":float(share),
            })
    vehicles=pd.DataFrame(vehicle_rows)

    financial = pd.DataFrame({
        "parametro":[
            "EBITDA base mensal","Outros custos variáveis sobre receita (%)",
            "Custo de contratação por FTE","Custo de desligamento por FTE",
            "Dias úteis por mês"
        ],
        "valor":[12_600_000,2.5,1_800,4_200,22],
        "unidade":["R$/mês","%","R$/FTE","R$/FTE","dias"]
    })
    scenario = pd.DataFrame({
        "cenario":SCENARIOS,
        "multiplicador_demanda":[1.0,1.16,1.08,.92],
        "restricao_b2c_adicional_pct":[0,8,0,5],
        "multiplicador_produtividade":[1.0,.97,1.03,1.0],
        "multiplicador_custos":[1.0,1.07,1.0,.98],
    })
    return {
        "demand":demand,"restrictions":restrictions,
        "branch_premises":branch_premises,"people_premises":people,
        "vehicle_premises":vehicles,"financial_premises":financial,
        "scenario_settings":scenario,
    }


def init_state() -> None:
    demo=generate_demo_data()
    for key,value in demo.items():
        if key not in st.session_state:
            st.session_state[key]=value.copy()
    defaults={
        "page":"Resumo Executivo",
        "scenario":"Cenário Base",
        "branches":BRANCHES.copy(),
        "period":"Próximos 12 meses",
        "view":"Mensal",
        "recomposition":"Proporcional",
        "global_override":0.0,
        "global_floor":82.0,
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k]=v


def export_excel(tables: dict[str,pd.DataFrame]) -> bytes:
    output=BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        for name,df in tables.items():
            df.to_excel(writer,sheet_name=name[:31],index=False)
    return output.getvalue()
