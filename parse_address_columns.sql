-- ============================================================
-- PARSE: insured_address → 5 colunas
--
-- Formato esperado (mais comum):
--   [TIPO] NOME, NÚMERO - COMPLEMENTO - BAIRRO
--   [TIPO] NOME, NÚMERO - BAIRRO
--   [TIPO] NOME - NÚMERO - BAIRRO          (sem vírgula)
--   NOME - BAIRRO                          (sem tipo, sem número)
--
-- Prefixos de tipo reconhecidos:
--   R / RUA · AV / AVENIDA · AL / ALAMEDA
--   TV / TRAV / TRAVESSA · EST / ESTR / ESTRADA
--   ROD / RODOVIA · PC / PCA / PRACA · LG / LARGO
--   QD / QUADRA / SQS / SQN / SQE / SQW
--
-- Prefixos honoríficos (DR, PRF, GEN, VER, DEP, PE, SRG…)
-- são mantidos no nome e o tipo cai como 'RUA'.
-- ============================================================

-- 1. TIPO DE LOGRADOURO ─────────────────────────────────────
CASE
  WHEN upper(trim(insured_address)) RLIKE '^(AV|AVE|AVEN|AVENIDA)[\\s.,]'   THEN 'AVENIDA'
  WHEN upper(trim(insured_address)) RLIKE '^(AL|ALAM|ALAMEDA)[\\s.,]'        THEN 'ALAMEDA'
  WHEN upper(trim(insured_address)) RLIKE '^(TV|TRAV|TRAVESSA)[\\s.,]'       THEN 'TRAVESSA'
  WHEN upper(trim(insured_address)) RLIKE '^(EST|ESTR|ESTRADA)[\\s.,]'       THEN 'ESTRADA'
  WHEN upper(trim(insured_address)) RLIKE '^(ROD|RODOV|RODOVIA)[\\s.,]'      THEN 'RODOVIA'
  WHEN upper(trim(insured_address)) RLIKE '^(PC|PCA|PRACA|LG|LARGO)[\\s.,]'  THEN 'PRACA'
  WHEN upper(trim(insured_address)) RLIKE '^(QD|QUADRA|SQS|SQN|SQE|SQW)[\\s.,\\d]' THEN 'QUADRA'
  WHEN upper(trim(insured_address)) RLIKE '^(R|RUA)[\\s.,]'                   THEN 'RUA'
  ELSE 'RUA'
END AS insured_address_type,

-- 2. NOME DA RUA (remove prefixo de tipo) ───────────────────
trim(regexp_replace(
  upper(coalesce(
    -- preferência: tudo antes da vírgula
    nullif(regexp_extract(trim(insured_address), '^(.+?)\\s*,', 1), ''),
    -- sem vírgula: tudo antes de "- NULL" ou "- dígito"
    nullif(regexp_extract(trim(insured_address), '^(.+?)\\s*-\\s*(NULL|\\d)', 1), ''),
    -- fallback: tudo antes do primeiro traço
    nullif(regexp_extract(trim(insured_address), '^(.+?)\\s*-', 1), ''),
    -- sem nenhum separador: endereço inteiro
    trim(insured_address)
  )),
  '^(AVENIDA|ALAMEDA|TRAVESSA|ESTRADA|RODOVIA|PRACA|LARGO|QUADRA|SQS|SQN|SQE|SQW|RUA|AV|AL|TV|TRAV|EST|ESTR|ROD|PC|PCA|LG|QD|R)\\.?\\s+',
  ''
)) AS insured_address_name,

-- 3. NÚMERO ─────────────────────────────────────────────────
-- Busca dígitos após vírgula; se não houver vírgula, busca após o 1º traço
coalesce(
  nullif(nullif(
    coalesce(
      nullif(regexp_extract(insured_address, ',\\s*(\\d[\\d\\/]*)', 1), ''),
      nullif(regexp_extract(insured_address, '^[^,]+-\\s*(\\d[\\d\\/]*)', 1), '')
    ),
  ''), 'NULL'),
  'SN'
) AS insured_address_number,

-- 4. COMPLEMENTO ────────────────────────────────────────────
-- Só existe quando há pelo menos 2 traços após o número.
-- Captura o segmento entre o 1º e o 2º traço (depois do número).
coalesce(
  nullif(nullif(nullif(
    trim(coalesce(
      -- com vírgula: "NOME, NUM - COMP - BAIRRO"
      nullif(regexp_extract(insured_address, ',\\s*\\d[^-]*-\\s*([^-]+?)\\s*-[^-]+$', 1), ''),
      -- sem vírgula: "NOME - NUM - COMP - BAIRRO"
      nullif(regexp_extract(insured_address, '^[^,]+-\\s*\\d[^-]*-\\s*([^-]+?)\\s*-[^-]+$', 1), '')
    )),
  ''), 'NULL'), 'NAO INFORMADO'),
  'NAO INFORMADO'
) AS insured_address_complement,

-- 5. BAIRRO ─────────────────────────────────────────────────
-- Sempre o último segmento após o último traço
coalesce(
  nullif(nullif(
    trim(regexp_extract(insured_address, '-\\s*([^-]+?)\\s*$', 1)),
  ''), 'NULL'),
  'NAO INFORMADO'
) AS insured_address_district
