import polars as pl
import streamlit as st

from src.config import DATA_DIR


# Helper function to uniformize date formats
def format_date(value):
    date = pd.to_datetime(value, errors="coerce")

    if pd.isna(date): return ""

    return date.strftime("%d-%m-%Y")


def data_to_parquet():
    df_consulta = pl.read_excel(DATA_DIR / 'consulta.xlsx', engine='calamine').lazy()
    df_risco = pl.read_excel(DATA_DIR / 'risco.xlsx', engine='calamine').lazy()
    df_mcdt = pl.read_excel(DATA_DIR / 'mcdt.xlsx', engine='calamine')

    df_risco = (
        df_risco.sort('Ano')
        .unique(subset=['Número SNS'], keep='last')
        .rename({'Nº Utente': 'Número SNS', 'Ano': 'Ano de risco'})
    )

    df_consulta = df_consulta.join(df_risco, on='Número SNS', how='inner')

    df_consulta.sink_parquet(DATA_DIR / 'consulta.parquet', compression='zstd')
    df_mcdt.write_parquet(DATA_DIR / 'mcdt.parquet', compression='zstd')


@st.cache_data
def load_sources():
    consultas = pd.read_excel(DATA_DIR / "consulta_demo.xlsx", sheet_name="Folha1")
    mcdt = pd.read_excel(DATA_DIR / "mcdt_demo.xlsx", sheet_name="Folha1")
    risco = pd.read_excel(DATA_DIR / "risco_demo.xlsx", sheet_name="Folha1")

    return consultas, mcdt, risco

@st.cache_data
def load_consultas_with_risk():
    # Load consultations, exams, and risk tables
    consultas, mcdt, risco = load_sources()

    # Clean the risk table so there is only one risk row per patient
    risco_latest = (
        risco.sort_values("Ano")
        .drop_duplicates("Nº Utente", keep="last")
        .rename(columns={"Ano": "Ano Risco"})
    )

    # Join the latest risk level onto each consultation using the patient number
    consultas = consultas.merge(
        risco_latest[["Nº Utente", "Ano Risco", "Nível de Risco"]],
        left_on="Número SNS",
        right_on="Nº Utente",
        how="left",
    )

    # keep only "Número SNS" column as "Nº Utente" is the same
    consultas = consultas.drop(columns=["Nº Utente"])

    # Return the consultation table with risk info added
    return consultas

@st.cache_data
def load_consultas_enriched():
    # Start with consultations + risk
    # then add MCDT summary info per consultation episode
    # => Each row is still one consultation, but now it also knows how many MCDTs are associated with it
    consultas = load_consultas_with_risk()
    _, mcdt, _ = load_sources()

    mcdt = mcdt.copy()

    # Create new column in MCDT table: MCDT Pendente = status does NOT contain Realizad
    # catches "Exame Realizado", "Análise REalizada", "Exame Realizado no Exterior"
    mcdt["MCDT Pendente"] = ~mcdt["Estado.Estado"].astype(str).str.contains(
        "Realizad",
        case = False,       # uppercase/lowercase does not matter
        na = False,         # empty values are treated as not matching "Realizad"
    )

    # Group MCDT rows by episode (aka consultation)
    # Calculate summary values for each episode
    mcdt_summary = (
        mcdt.groupby("Episódio.Código Episódio").agg(
            MCDT_Total=("Estado.Estado", "size"),
            MCDT_Pendentes=("MCDT Pendente", "sum"),
        ).reset_index()
        .rename(
            columns={
                "MCDT_Total": "MCDT Total",
                "MCDT_Pendentes": "MCDT Pendentes",
            }
        )
    )

    # Crete column "MCDT Realizados" = number of completed MCDTs = total - pending
    mcdt_summary["MCDT Realizados"] = (
        mcdt_summary["MCDT Total"] - mcdt_summary["MCDT Pendentes"]
    )

    # Merging MCDT summary into consultations
    consultas = consultas.merge(
        mcdt_summary,
        on="Episódio.Código Episódio",
        how="left",
    )

    # Filling missing MCDT counts (NaN->0)
    consultas[["MCDT Total", "MCDT Pendentes", "MCDT Realizados"]] = consultas[
        ["MCDT Total", "MCDT Pendentes", "MCDT Realizados"]
    ].fillna(0).astype(int)

    consultas["Data Marcação Normalizada"] = pd.to_datetime(
        consultas["Data Marcação.Data"],
        errors="coerce",
    )

    consultas["Data Marcação Formatada"] = consultas["Data Marcação Normalizada"].apply(format_date)

    today = pd.Timestamp.today().normalize()
    limit_date = today + pd.Timedelta(days=7)

    consultas["Consulta nos Próximos 7 Dias"] = (
    (consultas["Estado"] == "Marcado")
        & (consultas["Data Marcação Normalizada"] >= today)
        & (consultas["Data Marcação Normalizada"] <= limit_date)
    )

    consultas["Alerta MCDT"] = (
        consultas["Consulta nos Próximos 7 Dias"]
        & (consultas["MCDT Pendentes"] > 0)
    )

    consultas["Consulta nos Próximos 7 Dias"] = consultas["Consulta nos Próximos 7 Dias"].map(
    {True: "Sim", False: "Não"}
    )

    consultas["Alerta MCDT"] = consultas["Alerta MCDT"].map(
        {True: "Sim", False: "Não"}
    )

    # Creating "Tem MCDT Pendente" as yes/no column
    consultas["Tem MCDT Pendente"] = consultas["MCDT Pendentes"].apply(
        lambda value: "Sim" if value > 0 else "Não"
    )

    return consultas

@st.cache_data
def load_utente_history(numero_sns):
    consultas, mcdt, risco = load_sources()

    numero_sns = int(numero_sns)

    patient_consultas = consultas[
        consultas["Número SNS"] == numero_sns
    ].copy()

    risco_latest = (
        risco.sort_values("Ano")
        .drop_duplicates("Nº Utente", keep="last")
    )

    patient_risk = risco_latest[
        risco_latest["Nº Utente"] == numero_sns
    ]

    episode_codes = patient_consultas["Episódio.Código Episódio"].dropna().unique()

    patient_mcdt = mcdt[
        mcdt["Episódio.Código Episódio"].isin(episode_codes)
    ].copy()

    patient_consultas["Data Marcação Normalizada"] = pd.to_datetime(
        patient_consultas["Data Marcação.Data"],
        errors="coerce",
    )

    patient_consultas["Data Marcação Formatada"] = (
        patient_consultas["Data Marcação Normalizada"].dt.strftime("%d-%m-%Y")
    )

    patient_consultas = patient_consultas.sort_values(
        "Data Marcação Normalizada",
        ascending=False,
        na_position="last",
    )

    return patient_consultas, patient_mcdt, patient_risk
