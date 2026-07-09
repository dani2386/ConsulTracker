import streamlit as st
import polars as pl
from datetime import datetime, date, timedelta
from src.engine import load_data
from src.config import VIEWS_DIR


today = date.today()
df_consulta, df_mcdt, df_utente = load_data()

df_alerta = (
    df_consulta
    .filter(
        pl.col('MCDT Pendentes') > 0,
        (pl.col('Data') >= today) & (pl.col('Data') <= today + timedelta(days=7))
    )
    .with_columns((pl.col('Data') - today).dt.total_days().alias('Dias Restantes'))
)

current_hour = datetime.now().hour
st.title('Bom Dia!' if 6 <= current_hour < 12 else ('Boa Tarde!' if 12 <= current_hour < 20 else 'Boa Noite!'))
st.caption('Aqui estão as consultas dos próximos 7 dias com MCDT pendentes.')

metrics = st.columns(3)

metrics[0].metric('Alertas', len(df_alerta))
metrics[1].metric('MCDT Pendentes', int(df_alerta['MCDT Pendentes'].sum()) if len(df_alerta) > 0 else 0)
metrics[2].metric('Utentes Afetados', df_alerta['Nº Utente'].n_unique())

st.divider()

if df_alerta.is_empty():
    st.success('Não existem consultas com MCDT pendentes nos próximos 7 dias.')
    st.stop()

mode = st.radio('Agrupar por', options=['Data', 'Nível de Risco'], horizontal=True)

headers = df_alerta.get_column(mode).unique(maintain_order=True)

for header in headers:
    st.markdown(f'#### {header}')

    group = df_alerta.filter(pl.col(mode) == header)

    for consulta in group.iter_rows(named=True):
        user = df_utente.filter(pl.col('Nº Utente') == consulta['Nº Utente']).to_dicts()[0]

        mcdt_pending = (
            df_mcdt
            .filter(
                pl.col('Episódio') == consulta['Episódio'],
                pl.col('Estado').str.contains('(?i)Realizad').not_()
            )
        )

        label = (
            f'{user['Nome']} | '
            f'{consulta['Nível de Risco'] if mode == 'Data' else consulta['Data']} | '
            f'{consulta['Serviço']} | '
            f'{consulta['MCDT Pendentes']} MCDT pendentes'
        )

        status_color = {'Realizado': 'green', 'Marcado': 'orange'}.get(consulta['Estado'], '')
        risk_color = {'Baixo': 'green', 'Moderado': 'orange', 'Alto': 'red'}.get(user['Nível de Risco'], '')

        with st.expander(label):
            user_header = st.columns([3, 1])

            with user_header[0]:
                st.subheader(user['Nome'])
                st.caption(f'{user['Nº Utente']} | Processo: {user['Processo']}')

            with user_header[1]:
                if st.button('Ver histórico completo'):
                    st.session_state['user_id'] = str(consulta['Nº Utente'])
                    st.switch_page(VIEWS_DIR / 'user.py')

            user_info = st.columns(5)

            user_info[0].markdown(f'**Idade**  \n{user['Idade']} anos')
            user_info[1].markdown(f'**Sexo**  \n{user['Sexo']}')
            user_info[2].markdown(f'**Nível de Risco**  \n:{risk_color}[{user['Nível de Risco']}]')
            user_info[3].markdown(f'**Tel. 1**  \n{user['Tel. 1']}')
            user_info[4].markdown(f'**Tel. 2**  \n{user['Tel. 2']}')

            st.divider()

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

            for mcdt in mcdt_pending.iter_rows(named=True):
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
