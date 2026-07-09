import sys
import subprocess
import streamlit as st
import polars as pl
from src.config import ROOT_DIR, DATA_DIR


def sync_data():
    raw_file = DATA_DIR / 'consulta.xlsx'
    file = DATA_DIR / 'consulta.parquet'

    if not file.exists() or (raw_file.stat().st_mtime > file.stat().st_mtime):
        subprocess.run([sys.executable, ROOT_DIR / 'pipeline.py'])
        st.cache_data.clear()


@st.cache_data
def read_data():
    df_consulta = pl.read_parquet(DATA_DIR / 'consulta.parquet')
    df_mcdt = pl.read_parquet(DATA_DIR / 'mcdt.parquet')
    df_utente = pl.read_parquet(DATA_DIR / 'utente.parquet')

    return df_consulta, df_mcdt, df_utente


def load_data():
    sync_data()

    return read_data()
