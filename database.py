import pandas as pd
import streamlit as st


@st.cache_data
def load_data():
    return pd.DataFrame({
        'Utente': [101, 102, 103, 103],
        'Nome': ['João Silva', 'Maria Freitas', 'Carlos Costa', 'Carlos Costa'],
        'Idade': [24, 32, 62, 62],
        'Tel.': ['939749612', '925909653', '965509424', '965509424'],
        'Data': ['22-05-2024', '23-05-2024', '24-05-2024', '22-05-2024'],
        'Especialidade': ['Medicina Geral', 'Ginecologia', 'Urologia', 'Ortopedia'],
        'Estado': ['Agendado', 'Agendado', 'Agendado', 'Realizado'],
        'Risco': ['Baixo', 'Baixo', 'Moderado', 'Moderado'],
        'Flagged': [True, False, False, True]
    })
