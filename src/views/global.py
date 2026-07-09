import streamlit as st
import polars as pl
from datetime import date, timedelta
from src.engine import load_data


today = date.today()
df_consulta, df_mcdt, df_utente = load_data()

st.title('Painel Geral')
st.caption('Visualização global de dados')

st.divider()

mode = st.radio('Tabela', options=['Consulta', 'MCDT', 'Utente'], horizontal=True)

df_filtered = df_consulta if mode == 'Consulta' else (df_mcdt if mode == 'MCDT' else df_utente)

if mode == 'Consulta':
    filters = st.columns(6)

    status = filters[0].selectbox('Estado', options=['----', 'Marcado', 'Realizado'])
    risk = filters[1].selectbox('Nível de Risco', options=['----', 'Baixo', 'Moderado', 'Alto'])
    mcdt = filters[2].selectbox('MCDT Pendentes', options=['----', 'Sim', 'Não'])
    alert = filters[3].selectbox('Alerta', options=['----', 'Sim', 'Não'])
    service = filters[4].selectbox('Serviço', options=['----'] + sorted(df_consulta['Serviço'].unique().to_list()))
    date = filters[5].date_input('Data', (df_consulta['Data'].min(), df_consulta['Data'].max()))

    if status != '----':
        df_filtered = df_filtered.filter(pl.col('Estado') == status)

    if risk != '----':
        df_filtered = df_filtered.filter(pl.col('Nível de Risco') == risk)

    if mcdt != '----':
        if mcdt == 'Sim':
            df_filtered = df_filtered.filter(pl.col('MCDT Pendentes') > 0)
        else:
            df_filtered = df_filtered.filter(pl.col('MCDT Pendentes') == 0)

    if alert != '----':
        if alert == 'Sim':
            df_filtered = df_filtered.filter(
                pl.col('MCDT Pendentes') > 0,
                (pl.col('Data') >= today) & (pl.col('Data') <= today + timedelta(days=7))
            )
        else:
            df_filtered = df_filtered.filter(
                (pl.col('MCDT Pendentes') == 0) | (pl.col('Data') < today) | (pl.col('Data') > today + timedelta(days=7))
            )

    if service != '----':
        df_filtered = df_filtered.filter(pl.col('Serviço') == service)

    if isinstance(date, tuple):
        if len(date) == 2:
            df_filtered = df_filtered.filter(pl.col('Data').is_between(date[0], date[1]))
        else:
            df_filtered = df_filtered.filter(pl.col('Data') >= date[0])
    else:
        df_filtered = df_filtered.filter(pl.col('Data') == date)

elif mode == 'MCDT':
    filters = st.columns(4)

    status = filters[0].selectbox('Estado', options=['----', 'Marcado', 'Realizado'])
    rubric_type = filters[1].selectbox('Tipo Rubrica', options=['----'] + sorted(df_mcdt['Tipo Rubrica'].unique().to_list()))
    group = filters[2].selectbox('Grupo', options=['----'] + sorted(df_mcdt['Grupo'].unique().to_list()))
    date = filters[3].date_input('Data', (df_mcdt['Data'].min(), df_mcdt['Data'].max()))

    if status != '----':
        df_filtered = df_filtered.filter(pl.col('Estado') == status)

    if rubric_type != '----':
        df_filtered = df_filtered.filter(pl.col('Tipo Rubrica') == rubric_type)

    if group != '----':
        df_filtered = df_filtered.filter(pl.col('Grupo') == group)

    if isinstance(date, tuple):
        if len(date) == 2:
            df_filtered = df_filtered.filter(pl.col('Data').is_between(date[0], date[1]))
        else:
            df_filtered = df_filtered.filter(pl.col('Data') >= date[0])
    else:
        df_filtered = df_filtered.filter(pl.col('Data') == date)

else:
    filters = st.columns(3)

    risk = filters[0].selectbox('Nível de Risco', options=['----', 'Baixo', 'Moderado', 'Alto'])

    if risk != '----':
        df_filtered = df_filtered.filter(pl.col('Nível de Risco') == risk)

if df_filtered.is_empty():
    st.error('Não existem dados correspondentes aos filtros aplicados.')
    st.stop()

if mode == 'Consulta':
    def highlight(row):
        if row['MCDT Pendentes'] > 0 and row['Data'].date() <= today + timedelta(days=7):
            return ['background-color: #ffcccc'] * len(row)
        return [''] * len(row)

    df_filtered = df_filtered.to_pandas().style.apply(highlight, axis=1)

st.dataframe(
    df_filtered,
    width='stretch',
    hide_index=True,
    column_config={
        col: st.column_config.DateColumn(col, format='YYYY-MM-DD')
        for col in df_filtered.columns if col in ['Data', 'Data Nascimento']
    }
)
