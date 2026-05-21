from pyspark.sql import functions as F
from pyspark.sql.functions import col
from pyspark.sql.types import (
    LongType, StringType, TimestampType, DecimalType
)

# ---------------------------------------------------------------------------
# 1. Leitura bruta (tudo string)
# ---------------------------------------------------------------------------
path = "dbfs:/mnt/databub/pega/landzone/VIDA_SOCIOS/VidaSocio_Coberturas/*.csv"

df_raw = (
    spark.read.format("csv")
    .option("delimiter", ",")
    .option("header", "True")
    .load(path)
)

# ---------------------------------------------------------------------------
# 2. SELECT com CAST  →  essa lista também alimenta o CREATE TABLE
# ---------------------------------------------------------------------------
COLUNAS = [
    # (nome_original,            cast_type,               alias)
    ("PersonData_id",            LongType(),              "PersonData_id"),
    ("Quotes_id",                LongType(),              "Quotes_id"),
    ("plastey",                  StringType(),            "plastey"),
    ("pnExtractionIdentifier",   StringType(),            "pnExtractionIdentifier"),
    ("pnExtractionDateTime",     TimestampType(),         "pnExtractionDateTime"),
    ("Premio_Bruto_Por_Cobertura", DecimalType(18, 2),    "Premio_Bruto_Por_Cobertura"),
    ("Valor_Carencia",           DecimalType(18, 2),      "Valor_Carencia"),
    ("Fator_Total",              DecimalType(18, 2),      "Fator_Total"),
    ("Saldo_Confrontado_Acumulo_Risco", DecimalType(18, 2), "Saldo_Confrontado_Acumulo_Risco"),
    ("Codigo_Cobertura",         StringType(),            "Codigo_Cobertura"),
    ("CommunCoverages_id",       LongType(),              "CommunCoverages_id"),
    ("Saldo_Confronto",          DecimalType(18, 2),      "Saldo_Confronto"),
    ("Taxa_Base",                DecimalType(18, 2),      "Taxa_Base"),
]

df = df_raw.select(
    *[
        col(src).cast(dtype).alias(alias)
        for src, dtype, alias in COLUNAS
    ]
)

display(df)

# ---------------------------------------------------------------------------
# 3. Geração automática do CREATE TABLE a partir da mesma lista COLUNAS
# ---------------------------------------------------------------------------
def _spark_type_to_sql(dtype) -> str:
    if isinstance(dtype, LongType):
        return "BIGINT"
    if isinstance(dtype, StringType):
        return "STRING"
    if isinstance(dtype, TimestampType):
        return "TIMESTAMP"
    if isinstance(dtype, DecimalType):
        return f"DECIMAL({dtype.precision}, {dtype.scale})"
    return "STRING"


def gerar_create_table(tabela: str, colunas: list, location: str = "") -> str:
    col_defs = ",\n    ".join(
        f"{alias}  {_spark_type_to_sql(dtype)}"
        for _, dtype, alias in colunas
    )
    loc_clause = f"\nLOCATION '{location}'" if location else ""
    return (
        f"CREATE TABLE IF NOT EXISTS {tabela} (\n"
        f"    {col_defs}\n"
        f"){loc_clause};"
    )


ddl = gerar_create_table(
    tabela="vida_socios.coberturas",
    colunas=COLUNAS,
    # location="dbfs:/mnt/gold/vida_socios/coberturas",  # descomente se necessário
)

print(ddl)
