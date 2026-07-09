import streamlit as st
from src.engine import load_consultas_enriched

data = load_consultas_enriched()

st.title('Painel Geral de Consultas')
st.caption('Estatísticas operacionais e gestão de consultas.')

consultas_marcadas = data[data["Estado"] == "Marcado"]
consultas_com_mcdt_pendente = data[data["Tem MCDT Pendente"] == "Sim"]

metrics = st.columns(2)

metrics[0].metric(label='Consultas Marcadas', value=len(consultas_marcadas))
metrics[1].metric(label='Consultas com MCDT Pendente', value=len(consultas_com_mcdt_pendente))

st.divider()

st.subheader("Listagem de Consultas")

filters = st.columns([2, 1, 1])

name = filters[0].text_input('Nome do Utente:')
status = filters[1].selectbox('Estado:', options=['----'] + list(data['Estado'].dropna().unique()))
risk = filters[2].selectbox('Nível de Risco:', options=['----'] + list(data['Nível de Risco'].dropna().unique()))

filtered_data = data.copy()

if name: filtered_data = filtered_data[filtered_data['Nome'].str.contains(name, case=False, na=False)]
if status != '----': filtered_data = filtered_data[filtered_data['Estado'] == status]
if risk != '----': filtered_data = filtered_data[filtered_data['Nível de Risco'] == risk]

# Flagged rows appear first
filtered_data = (
    filtered_data.assign(
        Alerta_Ordem=(filtered_data['Alerta MCDT'] == 'Sim').astype(int)
    )
    .sort_values(
        by=["Alerta_Ordem", "Data Marcação Normalizada"],
        ascending=[False, True],
        na_position="last",
    )
    .drop(columns=["Alerta_Ordem"])
)

st.caption(f'A mostrar {len(filtered_data)} de {len(data)} registos encontrados.')

home_columns = [
    "Número SNS",
    #"Número Processo",
    "Episódio.Código Episódio",
    "Nome",
    "Anos",
    "Data Marcação Formatada",
    "Serviço Executante.Serviço SIG - DW",
    "Estado",
    "Nível de Risco",
    "MCDT Pendentes",
    #"Tem MCDT Pendente",
    "Alerta MCDT",
]

table_data = filtered_data[home_columns].copy()

table_data = table_data.rename(
    columns={"Data Marcação Formatada": "Data Marcação",
             "Número SNS": "Nº SNS",
             "Episódio.Código Episódio": "Episódio",
             "Serviço Executante.Serviço SIG - DW": "Serviço Executante"}
)

def color_estado(value):
    if value == "Realizado":
        return "color: #16a34a"
    if value == "Marcado":
        return "color: #f59e0b"
    return "color: #6b7280"

st.session_state.setdefault('idx', None)

table, detail = st.columns([2, 1]) if st.session_state.idx is not None else (st.container(), None)

def highlight_alert(row):
    if row["Alerta MCDT"] == "Sim":
        return ["background-color: #fee2e2; color: #991b1b"] * len(row)

    return [""] * len(row)

with table:
    if not filtered_data.empty:
        appointments = st.dataframe(
            table_data.style.apply(highlight_alert, axis=1).map(color_estado, subset=["Estado"]),
            width='stretch',
            hide_index=True,
            on_select='rerun',
            selection_mode='single-row'
        )

        idx = appointments.get('selection', {}).get('rows', [])

        if idx and st.session_state.idx != idx[0]:
            st.session_state.idx = idx[0]
            st.rerun()
        elif not idx and st.session_state.idx is not None:
            st.session_state.idx = None
            st.rerun()
    else:
        st.warning('Nenhum registo encontrado com os filtros selecionados.')

if detail and st.session_state.idx is not None:
    with detail:
        consulta = filtered_data.iloc[st.session_state.idx]

        st.subheader('Detalhes da Consulta')

        with st.container(border=True):
            st.title(f"{consulta['Nome']}")
            st.caption(f"Número SNS: {consulta['Número SNS']}")
            st.caption(f"Número Processo: {consulta['Número Processo']}")
            st.markdown(f"**Consulta nos Próximos 7 Dias:** {consulta['Consulta nos Próximos 7 Dias']}")
            st.markdown(f"**Alerta MCDT:** {consulta['Alerta MCDT']}")

            st.divider()

            st.markdown(f"**Idade:** {consulta['Anos']}")
            st.markdown(f"**Sexo:** {consulta['Sexo']}")
            st.markdown(f"**Telefone 1:** {consulta['Número Telefone 1']}")
            st.markdown(f"**Telefone 2:** {consulta['Número Telefone 2']}")
            st.markdown(f"**Nível de Risco:** {consulta['Nível de Risco']}")

            st.divider()

            st.markdown(f"**Episódio:** {consulta['Episódio.Código Episódio']}")
            st.markdown(f"**Data Marcação:** {consulta['Data Marcação Formatada']}")

            if consulta["Estado"] == "Realizado":
                status_color = "green"
            elif consulta["Estado"] == "Marcado":
                status_color = "orange"
            else:
                status_color = "gray"

            st.markdown(f"**Estado:** :{status_color}[{consulta['Estado']}]")
            st.markdown(f"**Tipo Consulta:** {consulta['Tipo Consulta']}")
            st.markdown(f"**Tipo Consulta MTS:** {consulta['Tipo Consulta MTS']}")
            st.markdown(f"**Especialidade:** {consulta['Serviço Executante.Serviço SIG - DW']}")
            st.markdown(f"**Hospital:** {consulta['Serviço Executante.Hospital - DW']}")

            st.divider()

            st.markdown(f"**MCDT Total:** {consulta['MCDT Total']}")
            st.markdown(f"**MCDT Pendentes:** {consulta['MCDT Pendentes']}")
            st.markdown(f"**MCDT Realizados:** {consulta['MCDT Realizados']}")
            #st.markdown(f"**Tem MCDT Pendente:** {consulta['Tem MCDT Pendente']}")
