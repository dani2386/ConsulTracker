import streamlit as st
from database import load_data


data = load_data()

st.title('Painel Geral de Consultas')
st.caption('Estatísticas operacionais e gestão de consultas.')

metrics = st.columns(2)

metrics[0].metric(label='Consultas Agendadas', value=len(data[data['Estado'] == 'Agendado']))
metrics[1].metric(label='Consultas com Exames em Falta', value=len(data[data['Flagged']]))

st.divider()

st.subheader("Listagem de Agendamentos")

filters = st.columns([2, 1, 1])

name = filters[0].text_input('Nome do Utente:')
status = filters[1].selectbox('Estado:', options=['----'] + list(data['Estado'].unique()))
risk = filters[2].selectbox('Risco:', options=['----'] + list(data['Risco'].unique()))

filtered_data = data.copy()

if name: filtered_data = filtered_data[filtered_data['Nome'].str.contains(name, case=False, na=False)]
if status != '----': filtered_data = filtered_data[filtered_data['Estado'] == status]
if risk != '----': filtered_data = filtered_data[filtered_data['Risco'] == risk]

st.caption(f'A mostrar {len(filtered_data)} de {len(data)} registos encontrados.')

st.session_state.setdefault('idx', None)

table, detail = st.columns([2, 1]) if st.session_state.idx is not None else (st.container(), None)

with table:
    if not filtered_data.empty:
        appointments = st.dataframe(filtered_data, width='stretch', hide_index=True, on_select='rerun', selection_mode='single-row')

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
        appointment = filtered_data.iloc[st.session_state.idx]

        st.subheader('Detalhes do Agendamento')

        with st.container(border=True):
            st.title(f'{appointment['Nome']}')
            st.caption(f'Utente: {appointment['Utente']}')
            st.caption(f'Contacto: {appointment['Tel.']}')

            st.divider()

            st.markdown(f'**Especialidade:** {appointment['Especialidade']}')
            st.markdown(f'**Data:** {appointment['Data']}')

            status_color = 'green' if appointment['Estado'] == 'Realizado' else 'orange'
            st.markdown(f'**Estado:** :{status_color}[{appointment['Estado']}]')
