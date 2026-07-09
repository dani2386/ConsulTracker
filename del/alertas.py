import streamlit as st

from src.engine import load_consultas_enriched, load_sources


data = load_consultas_enriched()
_, mcdt, _ = load_sources()

st.title("Bom dia! ☀️")
st.caption("Aqui estão as consultas marcadas nos próximos 7 dias com MCDT pendentes.")

alertas = data[data["Alerta MCDT"] == "Sim"].copy()
consultas_7_dias = data[data["Consulta nos Próximos 7 Dias"] == "Sim"].copy()

metrics = st.columns(3)

metrics[0].metric("Alertas Ativos", len(alertas))
metrics[1].metric("Consultas nos Próximos 7 Dias", len(consultas_7_dias))
metrics[2].metric("MCDT Pendentes em Alerta", int(alertas["MCDT Pendentes"].sum()))

st.divider()

st.subheader("Consultas com Alerta")

if alertas.empty:
    st.success("Não existem consultas com MCDT pendentes nos próximos 7 dias.")
    st.stop()

alertas = alertas.sort_values(
    by=["Data Marcação Normalizada", "MCDT Pendentes"],
    ascending=[True, False],
    na_position="last",
)

alert_columns = [
    "Número SNS",
    "Nome",
    "Anos",
    "Data Marcação Formatada",
    "Serviço Executante.Serviço SIG - DW",
    "Tipo Consulta MTS",
    "Nível de Risco",
    "MCDT Pendentes",
]

table_data = alertas[alert_columns].copy()

table_data = table_data.rename(
    columns={
        "Número SNS": "Nº SNS",
        "Data Marcação Formatada": "Data Marcação",
        "Serviço Executante.Serviço SIG - DW": "Serviço SIG",
    }
)

st.session_state.setdefault("alertas_idx", None)

table, detail = (
    st.columns([2, 1])
    if st.session_state.alertas_idx is not None
    else (st.container(), None)
)

with table:
    selected = st.dataframe(
        table_data,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="alertas_table",
    )

    idx = selected.get("selection", {}).get("rows", [])

    if idx and st.session_state.alertas_idx != idx[0]:
        st.session_state.alertas_idx = idx[0]
        st.rerun()
    elif not idx and st.session_state.alertas_idx is not None:
        st.session_state.alertas_idx = None
        st.rerun()

if detail and st.session_state.alertas_idx is not None:
    with detail:
        consulta = alertas.iloc[st.session_state.alertas_idx]
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
        ].copy()

        st.subheader("Detalhes do Alerta")

        with st.container(border=True):
            st.title(f"{consulta['Nome']}")
            st.caption(f"**Nº SNS**: {consulta['Número SNS']}")
            st.caption(f"**Telefone 1:** {consulta['Número Telefone 1']}")
            st.caption(f"**Telefone 2:** {consulta['Número Telefone 2']}")

            if st.button("Ver histórico do utente"):
                st.session_state["utente_numero_sns"] = str(consulta["Número SNS"])
                st.switch_page("views/user.py")

            st.markdown(f"**Tipo Consulta:** {consulta['Tipo Consulta']}")
            st.markdown(f"**Médico:** {consulta['Médico Executante.Nome']}")
            st.markdown(f"**Hospital:** {consulta['Serviço Executante.Hospital - DW']}")

        st.markdown("### MCDT Pendentes")

        if mcdt_pendentes.empty:
            st.info("Sem MCDT pendentes associados a esta consulta.")
        else:
            for _, exame in mcdt_pendentes.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{exame['Rubrica']}**")
                    st.caption(f"{exame['Tipo Rubrica']} · {exame['Grupo']}")
                    st.markdown(f"**Estado:** {exame['Estado.Estado']}")
                    st.markdown(
                        f"**Serviço requisitante:** {exame['Serviço Requisitante.Serviço SIG - DW']}"
                    )
                    st.markdown(
                        f"**Hospital requisitante:** {exame['Serviço Requisitante.Hospital - DW']}"
                    )