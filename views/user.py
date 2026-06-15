import pandas as pd
import streamlit as st

from database import load_utente_history
from html import escape

consulta_detail_columns = [
    "Episódio.Código Episódio",
    "Estado",
    "Data Marcação Formatada",
    "Tipo Consulta",
    "Tipo Consulta MTS",
    "Tipo Produção.Tipo Produção",
    "Médico Executante.Nome",
    "Serviço Executante.Serviço SIG - DW",
    "Serviço Executante.Hospital - DW",
    "Serviço Executante.Indicação Médica - DW",
    "Serviço Executante.Serviço GH",
]

consulta_column_labels = {
    "Episódio.Código Episódio": "Código Episódio",
    "Data Marcação Formatada": "Data Marcação",
    "Tipo Produção.Tipo Produção": "Tipo Produção",
    "Médico Executante.Nome": "Médico Executante",
    "Serviço Executante.Serviço SIG - DW": "Serviço SIG",
    "Serviço Executante.Hospital - DW": "Hospital",
    "Serviço Executante.Indicação Médica - DW": "Indicação Médica",
    "Serviço Executante.Serviço GH": "Serviço GH",
}

mcdt_columns = [
    "Estado.Estado",
    "Indicação Exame Análise",
    "Tipo Rubrica",
    "Grupo",
    "Rubrica",
    "Tempo.Data",
    "Serviço Requisitante.Serviço SIG - DW",
    "Serviço Requisitante.Hospital - DW",
    "Serviço Requisitante.Serviço GH",
    "Estado.Indicação Conta Actividade",
]

mcdt_column_labels = {
    "Estado.Estado": "Estado",
    "Indicação Exame Análise": "Tipo",
    "Tempo.Data": "Data",
    "Serviço Requisitante.Serviço SIG - DW": "Serviço SIG Requisitante",
    "Serviço Requisitante.Hospital - DW": "Hospital Requisitante",
    "Serviço Requisitante.Serviço GH": "Serviço GH Requisitante",
    "Estado.Indicação Conta Actividade": "Indicação Conta Actividade",
}

st.title("Histórico do Utente")
st.caption("Pesquisa por Nº SNS para consultar histórico de consultas e MCDT associados.")

default_numero_sns = st.session_state.get("utente_numero_sns", "")

with st.form("utente_search"):
    numero_sns = st.text_input("Nº SNS", value=default_numero_sns)
    submitted = st.form_submit_button("Pesquisar")

selected_numero_sns = numero_sns.strip() if submitted else default_numero_sns.strip()

if not selected_numero_sns:
    st.info("Introduzir um Nº SNS para consultar o histórico do utente.")
    st.stop()

if not selected_numero_sns.isdigit():
    st.error("Introduza um Nº SNS válido.")
    st.stop()

st.session_state["utente_numero_sns"] = selected_numero_sns

consultas, mcdt, risco = load_utente_history(selected_numero_sns)

if consultas.empty:
    st.warning("Não foram encontradas consultas para este utente.")
    st.stop()

utente = consultas.iloc[0]

risk_value = ""
risk_year = ""

if not risco.empty:
    risk_value = risco.iloc[0]["Nível de Risco"]
    risk_year = risco.iloc[0]["Ano"]

st.subheader("Resumo do Utente")

summary = st.columns(4)

summary[0].metric("Nº SNS", utente["Número SNS"])
summary[1].metric("Nome", utente["Nome"])
summary[2].metric("Nível de Risco", risk_value if risk_value else "Sem registo")
summary[3].metric("Total Consultas", len(consultas))

with st.container(border=True):
    left, right = st.columns(2)

    with left:
        st.markdown(f"**Número Processo:** {utente['Número Processo']}")
        st.markdown(f"**Sexo:** {utente['Sexo']}")
        st.markdown(f"**Idade:** {utente['Anos']}")

    with right:
        st.markdown(f"**Telefone 1:** {utente['Número Telefone 1']}")
        st.markdown(f"**Telefone 2:** {utente['Número Telefone 2']}")
        st.markdown(f"**Ano Risco:** {risk_year if risk_year else "Sem registo"}")

st.subheader("Histórico de Consultas")

for _, consulta in consultas.iterrows():
    episodio = consulta["Episódio.Código Episódio"]

    mcdt_consulta = mcdt[
        mcdt["Episódio.Código Episódio"] == episodio
    ].copy()

    mcdt_pendentes = mcdt_consulta[
        ~mcdt_consulta["Estado.Estado"].astype(str).str.contains(
            "Realizad",
            case=False,
            na=False,
        )
    ]

    expander_label = (
        f"{consulta['Data Marcação Formatada']} | "
        f"{consulta['Serviço Executante.Serviço SIG - DW']} | "
        f"{consulta['Estado']} | "
        f"{len(mcdt_pendentes)} MCDT associado(s)"
    )

    with st.expander(expander_label):
        st.markdown("#### Consulta")

        status_color = "green" if consulta["Estado"] == "Realizado" else "orange"

        top = st.columns(3)
        top[0].markdown(f"**Estado**  \n:{status_color}[{consulta['Estado']}]")
        top[1].markdown(f"**Data Marcação**  \n{consulta['Data Marcação Formatada']}")
        top[2].markdown(f"**Código Episódio**  \n{consulta['Episódio.Código Episódio']}")

        detail_row_1 = st.columns(3)
        detail_row_1[0].markdown(
            f"**Tipo Consulta**  \n{consulta['Tipo Consulta']}"
        )
        detail_row_1[1].markdown(
            f"**Tipo Consulta MTS**  \n{consulta['Tipo Consulta MTS']}"
        )
        detail_row_1[2].markdown(
            f"**Tipo Produção**  \n{consulta['Tipo Produção.Tipo Produção']}"
        )

        detail_row_2 = st.columns(3)
        detail_row_2[0].markdown(
            f"**Médico Executante**  \n{consulta['Médico Executante.Nome']}"
        )
        detail_row_2[1].markdown(
            f"**Serviço SIG**  \n{consulta['Serviço Executante.Serviço SIG - DW']}"
        )
        detail_row_2[2].markdown(
            f"**Hospital**  \n{consulta['Serviço Executante.Hospital - DW']}"
        )

        detail_row_3 = st.columns(3)
        detail_row_3[0].markdown(
            f"**Indicação Médica**  \n{consulta['Serviço Executante.Indicação Médica - DW']}"
        )
        detail_row_3[1].markdown(
            f"**Serviço GH**  \n{consulta['Serviço Executante.Serviço GH']}"
        )
        detail_row_3[2].markdown(
            f"**Conta Actividade**  \n{consulta.get('Indicação Conta Actividade', '')}"
        )

        st.markdown("**MCDT associados**")

        if mcdt_consulta.empty:
            st.info("Sem MCDT associados a esta consulta.")
        else:
            mcdt_table = mcdt_consulta[mcdt_columns].copy()

            mcdt_table["Tempo.Data"] = (
                pd.to_datetime(mcdt_table["Tempo.Data"], errors="coerce")
                .dt.strftime("%d-%m-%Y")
            )

            mcdt_table = mcdt_table.rename(columns=mcdt_column_labels)

            mcdt_table["_Pendente"] = ~mcdt_table["Estado"].astype(str).str.contains(
                "Realizad",
                case=False,
                na=False,
            )

            mcdt_table = (
                mcdt_table.sort_values("_Pendente", ascending=False)
                .drop(columns=["_Pendente"])
            )

            st.dataframe(
                mcdt_table,
                width="stretch",
                hide_index=True,
            )