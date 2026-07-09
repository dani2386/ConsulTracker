import streamlit as st
import polars as pl
from src.engine import load_data


df_consulta, df_mcdt, df_utente = load_data()

st.title('Histórico do Utente')
st.caption('Pesquisa por Nº Utente para consultar histórico de consultas e MCDT associados.')

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = ''

with st.form("utente_search"):
    st.text_input('Nº Utente', key='user_id')
    st.form_submit_button('Pesquisar')

user_id = st.session_state['user_id'].strip()

if not user_id:
    st.info('Introduzir um Nº Utente para consultar o histórico do utente.')
    st.stop()

if not user_id.isdigit():
    st.error('Nº Utente inválido.')
    st.stop()

if int(user_id) not in df_utente['Nº Utente']:
    st.error('Nº Utente não encontrado.')
    st.stop()

user = df_utente.filter(pl.col('Nº Utente') == int(user_id)).to_dicts()[0]
df_consulta_user = df_consulta.filter(pl.col('Nº Utente') == int(user_id))

if df_consulta_user.is_empty():
    st.warning('Não foram encontradas consultas para este utente.')
    st.stop()

st.subheader('Resumo do Utente')

metrics = st.columns(4)

metrics[0].metric('Nº Utente', user['Nº Utente'])
metrics[0].caption('Nº Utente', user['Nº Utente'])
metrics[1].metric('Nome', user['Nome'])
metrics[2].metric('Nível de Risco', user['Nível de Risco'])
metrics[3].metric('Total Consultas', len(df_consulta_user))

with st.container(border=True):
    cols = st.columns(2)

    with cols[0]:
        st.markdown(f'**Processo:** {user['Processo']}')
        st.markdown(f'**Sexo:** {user['Sexo']}')
        st.markdown(f'**Idade:** {user['Idade']}')

    with cols[1]:
        st.markdown(f'**Tel. 1:** {user['Tel. 1']}')
        st.markdown(f'**Tel. 2:** {user['Tel. 2']}')
        st.markdown(f'**Ano Risco:** {user['Ano Risco']}')

st.subheader('Histórico de Consultas')

for consulta in df_consulta_user.iter_rows(named=True):
    df_mcdt_consulta = df_mcdt.filter(pl.col('Episódio') == consulta['Episódio'])

    label = (
        f'{consulta['Data']} | '
        f'{consulta['Serviço']} | '
        f'{consulta['Estado']} | '
        f'{len(df_mcdt_consulta)} MCDT associado(s)'
    )

    status_color = {'Realizado': 'green', 'Marcado': 'orange'}.get(consulta['Estado'], '')

    with st.expander(label):
        consulta_info = st.columns([2, 1, 1, 1])

        with consulta_info[0]:
            st.subheader(f'Consulta - {consulta['Serviço']}')
            st.caption(f'Episódio: {consulta['Episódio']}')

        with consulta_info[1]:
            st.markdown(f'**Data de Marcação**  \n{consulta['Data']}')
            st.markdown(f'**Estado**  \n:{status_color}[{consulta['Estado']}]')

        with consulta_info[2]:
            st.markdown(f'**Médico**  \n{consulta['Médico']}')
            st.markdown(f'**Hospital**  \n{consulta['Hospital']}')

        with consulta_info[3]:
            st.markdown(f'**Tipo de Consulta**  \n{consulta['Tipo Consulta']}')
            st.markdown(f'**Tipo de Produção**  \n{consulta['Tipo Produção']}')

        st.markdown("##### MCDT Pendentes")

        for mcdt in df_mcdt_consulta.iter_rows(named=True):
            with st.container(border=True):
                mcdt_info = st.columns([2, 1, 1])

                with mcdt_info[0]:
                    st.markdown(f"**{mcdt['Rubrica']}**")
                    st.caption(f"{mcdt['Tipo Rubrica']} - {mcdt['Grupo']}")

                with mcdt_info[1]:
                    st.markdown(f"**Estado**  \n{mcdt['Estado']}")
                    st.markdown(f"**Tipo**  \n{mcdt['Tipo']}")

                with mcdt_info[2]:
                    st.markdown(f"**Serviço requisitante**  \n{mcdt['Serviço']}")
                    st.markdown(f"**Hospital requisitante**  \n{mcdt['Hospital']}")
