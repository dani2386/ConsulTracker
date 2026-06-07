import streamlit as st

from database import load_consultas_enriched, load_sources

def format_risk(value):
    if value == "Alto":
        return ":red[Alto]"
    if value == "Moderado":
        return ":orange[Moderado]"
    if value == "Baixo":
        return ":green[Baixo]"
    return str(value)


def format_status(value):
    if value == "Realizado":
        return ":green[Realizado]"
    if value == "Marcado":
        return ":orange[Marcado]"
    return str(value)

data = load_consultas_enriched()
_, mcdt, _ = load_sources()

today = data["Data Marcação Normalizada"].min()

st.title("Bom dia! ☀️")
st.caption("Aqui estão as consultas dos próximos 7 dias com MCDT pendentes.")

alertas = data[data["Alerta MCDT"] == "Sim"].copy()
consultas_7_dias = data[data["Consulta nos Próximos 7 Dias"] == "Sim"].copy()

metrics = st.columns(4)

metrics[0].metric("Consultas com Alerta", len(alertas))
metrics[1].metric("Consultas nos Próximos 7 Dias", len(consultas_7_dias))
metrics[2].metric("MCDT Pendentes", int(alertas["MCDT Pendentes"].sum()))
metrics[3].metric("Utentes Afetados", alertas["Número SNS"].nunique())

st.divider()

if alertas.empty:
    st.success("Não existem consultas com MCDT pendentes nos próximos 7 dias.")
    st.stop()

alertas = alertas.sort_values(
    by=["Data Marcação Normalizada", "MCDT Pendentes"],
    ascending=[True, False],
    na_position="last",
)

group_mode = st.radio(
    "Agrupar por",
    options=["Data", "Risco"],
    horizontal=True,
)

st.subheader("Consultas com MCDT Pendente")

if group_mode == "Data":
    groups = alertas.groupby("Data Marcação Formatada", sort=False)
else:
    risk_order = {
        "Alto": 0,
        "Moderado": 1,
        "Baixo": 2,
    }

    alertas = (
        alertas.assign(
            Risco_Ordem=alertas["Nível de Risco"].map(risk_order).fillna(99)
        )
        .sort_values(
            by=["Risco_Ordem", "Data Marcação Normalizada", "MCDT Pendentes"],
            ascending=[True, True, False],
            na_position="last",
        )
    )

    groups = alertas.groupby("Nível de Risco", sort=False)

for group_name, grupo in groups:
    st.markdown(f"### {group_name}")

    for _, consulta in grupo.iterrows():
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

        label = (
            f"Nº SNS {consulta['Número SNS']} | "
            f"{consulta['Nome']} | "
            f"{consulta['Serviço Executante.Serviço SIG - DW']} | "
            f"{consulta['MCDT Pendentes']} MCDT pendente(s)"
        )

        with st.expander(label):
            header_cols = st.columns([3, 1])

            with header_cols[0]:
                st.markdown("#### Utente")

            with header_cols[1]:
                if st.button(
                        "Ver histórico completo",
                        key=f"utente_{consulta['Número SNS']}_{episodio}",
                ):
                    st.session_state["utente_numero_sns"] = str(consulta["Número SNS"])
                    st.switch_page("views/user.py")

            utente_cols = st.columns(4)
            utente_cols[0].markdown(f"**Nome**  \n{consulta['Nome']}")
            utente_cols[1].markdown(f"**Idade**  \n{consulta['Anos']}")
            utente_cols[2].markdown(f"**Sexo**  \n{consulta['Sexo']}")
            utente_cols[3].markdown(f"**Risco**  \n{format_risk(consulta['Nível de Risco'])}")

            st.markdown("#### Contactos")
            st.markdown(f"**Telefone 1:** {consulta['Número Telefone 1']}")
            st.markdown(f"**Telefone 2:** {consulta['Número Telefone 2']}")

            st.markdown("#### Consulta")

            consulta_top = st.columns(3)
            consulta_top[0].markdown(f"**Estado**  \n{format_status(consulta['Estado'])}")
            consulta_top[1].markdown(f"**Data Marcação**  \n{consulta['Data Marcação Formatada']}")
            consulta_top[2].markdown(f"**Código Episódio**  \n{consulta['Episódio.Código Episódio']}")

            consulta_details = st.columns(3)
            consulta_details[0].markdown(f"**Tipo Consulta**  \n{consulta['Tipo Consulta']}")
            consulta_details[1].markdown(f"**Tipo MTS**  \n{consulta['Tipo Consulta MTS']}")
            consulta_details[2].markdown(f"**Tipo Produção**  \n{consulta['Tipo Produção.Tipo Produção']}")

            consulta_service = st.columns(3)
            consulta_service[0].markdown(f"**Médico**  \n{consulta['Médico Executante.Nome']}")
            consulta_service[1].markdown(f"**Hospital**  \n{consulta['Serviço Executante.Hospital - DW']}")
            consulta_service[2].markdown(f"**Serviço GH**  \n{consulta['Serviço Executante.Serviço GH']}")

            st.markdown("#### MCDT Pendentes")

            if mcdt_pendentes.empty:
                st.info("Sem MCDT pendentes associados a esta consulta.")
            else:
                for _, exame in mcdt_pendentes.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{exame['Rubrica']}**")
                        st.caption(f"{exame['Tipo Rubrica']} · {exame['Grupo']}")
                        st.markdown(f"**Estado:** {exame['Estado.Estado']}")
                        st.markdown(f"**Tipo:** {exame['Indicação Exame Análise']}")
                        st.markdown(
                            f"**Serviço requisitante:** {exame['Serviço Requisitante.Serviço SIG - DW']}"
                        )
                        st.markdown(
                            f"**Hospital requisitante:** {exame['Serviço Requisitante.Hospital - DW']}"
                        )