import polars as pl
from src.config import DATA_DIR


def xlsx_to_parquet():
    df_consulta = pl.read_excel(DATA_DIR / 'consulta.xlsx', engine='calamine')
    df_risco = pl.read_excel(DATA_DIR / 'risco.xlsx', engine='calamine')
    df_mcdt = pl.read_excel(DATA_DIR / 'mcdt.xlsx', engine='calamine')

    df_consulta.write_parquet(DATA_DIR / 'consulta_raw.parquet', compression='zstd')
    df_risco.write_parquet(DATA_DIR / 'risco_raw.parquet', compression='zstd')
    df_mcdt.write_parquet(DATA_DIR / 'mcdt_raw.parquet', compression='zstd')


def process_data():
    df_consulta = pl.scan_parquet(DATA_DIR / 'consulta_raw.parquet')
    df_risco = pl.scan_parquet(DATA_DIR / 'risco_raw.parquet')
    df_mcdt = pl.scan_parquet(DATA_DIR / 'mcdt_raw.parquet')

    df_risco = df_risco.rename({'Ano': 'Ano Risco'}).sort('Ano Risco').unique(subset=['Nº Utente'], keep='last')

    df_utente = (
        df_consulta
        .select([
            pl.col('Número SNS').alias('Nº Utente'),
            pl.col('Número Processo').alias('Processo'),
            pl.col('Anos').alias('Idade'),
            pl.col('Número Telefone 1').alias('Tel. 1'),
            pl.col('Número Telefone 2').alias('Tel. 2'),
            pl.col('Data Nascimento').cast(pl.Date),
            pl.col('Nome'),
            pl.col('Sexo'),
            pl.col('Distrito'),
            pl.col('Concelho'),
            pl.col('Freguesia'),
            pl.col('Indicação Alta Clínica'),
            pl.col('Indicação Óbito')
        ])
        .unique(subset=['Nº Utente'])
        .join(df_risco, on='Nº Utente', how='left')
        .sort('Nº Utente')
    )

    df_mcdt = (
        df_mcdt
        .select([
            pl.col('Número SNS').alias('Nº Utente'),
            pl.col('Número Processo').alias('Processo'),
            pl.col('Episódio.Código Episódio').alias('Episódio'),
            pl.col('Episódio.Episódio Pai').alias('Episódio Pai'),
            pl.col('Estado.Estado').alias('Estado'),
            pl.col('Serviço Requisitante.Serviço SIG - DW').alias('Serviço'),
            pl.col('Serviço Requisitante.Hospital - DW').alias('Hospital'),
            pl.col('Serviço Requisitante.Serviço GH').alias('Código Serviço'),
            pl.col('Estado.Indicação Conta Actividade').alias('Indicação Conta Atividade'),
            pl.col('Indicação Exame Análise').alias('Tipo'),
            pl.coalesce([
                pl.col('Tempo.Data').cast(pl.String).str.to_date("%Y-%m-%d", exact=False, strict=False),
                pl.col('Tempo.Data').cast(pl.String).str.to_date("%d-%m-%Y", exact=False, strict=False),
            ]).alias('Data'),
            pl.col('Quantidade'),
            pl.col('Grupo'),
            pl.col('Rubrica'),
            pl.col('Tipo Rubrica')
        ])
        .sort('Data')
    )

    mcdt_pending = (
        df_mcdt
        .group_by('Episódio')
        .agg(pl.col('Estado').str.contains('(?i)Realizad').not_().sum().alias('MCDT Pendentes'))
    )

    df_consulta = (
        df_consulta
        .select([
            pl.col('Número SNS').alias('Nº Utente'),
            pl.col('Número Processo').alias('Processo'),
            pl.col('Episódio.Código Episódio').alias('Episódio'),
            pl.col('Tipo Produção.Tipo Produção').alias('Tipo Produção'),
            pl.col('Médico Executante.Nome').alias('Médico'),
            pl.col('Serviço Executante.Serviço SIG - DW').alias('Serviço'),
            pl.col('Serviço Executante.Hospital - DW').alias('Hospital'),
            pl.col('Serviço Executante.Indicação Médica - DW').alias('Indicação Médica'),
            pl.col('Serviço Executante.Serviço GH').alias('Código Serviço'),
            pl.col('ID B ACTIVIDADE').alias('Id Atividade'),
            pl.col('Indicação Conta Actividade').alias('Indicação Conta Atividade'),
            pl.coalesce([
                pl.col('Data Marcação.Data').cast(pl.String).str.to_date("%Y-%m-%d", exact=False, strict=False),
                pl.col('Data Marcação.Data').cast(pl.String).str.to_date("%d-%m-%Y", exact=False, strict=False),
            ]).alias('Data'),
            pl.col('Quantidade'),
            pl.col('Estado'),
            pl.col('Tipo Consulta'),
            pl.col('Tipo Consulta MTS'),
            pl.col('Âmbito')
        ])
        .join(mcdt_pending, on='Episódio', how='left')
        .join(df_risco, on='Nº Utente', how='left')
        .with_columns(pl.col('MCDT Pendentes').fill_null(0).cast(pl.Int64))
        .sort(
            by=['Data', pl.col('Nível de Risco').cast(pl.Enum(['Alto', 'Moderado', 'Baixo'])), 'MCDT Pendentes'],
            descending=[False, False, True]
        )
    )

    df_utente.collect().write_parquet(DATA_DIR / 'utente.parquet', compression='zstd')
    df_mcdt.collect().write_parquet(DATA_DIR / 'mcdt.parquet', compression='zstd')
    df_consulta.collect().write_parquet(DATA_DIR / 'consulta.parquet', compression='zstd')


if __name__ == '__main__':
    xlsx_to_parquet()
    process_data()

    (DATA_DIR / 'consulta_raw.parquet').unlink()
    (DATA_DIR / 'risco_raw.parquet').unlink()
    (DATA_DIR / 'mcdt_raw.parquet').unlink()
