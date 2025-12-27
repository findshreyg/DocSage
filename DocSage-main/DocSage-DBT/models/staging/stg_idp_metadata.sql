-- models/staging/stg_idp_metadata_fixed.sql
with base as (
  select
    row_number() over (order by (select null)) as src_row_id,
    record
  from {{ source('idp','raw_idp_metadata') }}
),
top_level as (
  select
    src_row_id,
    record:"hash":"S"::string      as hash,
    record:"user_id":"S"::string   as user_id,
    record:"filename":"S"::string  as filename,
    record:"s3_key":"S"::string    as s3_key,
    record:"metadata":"M"          as md_obj
  from base
),
md_scalars as (
  select
    src_row_id,
    md_obj:"created_date":"S"::string as created_date_raw,
    md_obj:"title":"S"::string        as title,
    md_obj:"type":"S"::string         as doc_type,
    try_to_number(md_obj:"pages":"N"::string) as pages
  from top_level
)
select
  coalesce(t.hash, to_varchar(t.src_row_id)) as grp_key,
  t.hash,
  t.user_id,
  t.filename,
  t.s3_key,
  s.title,
  s.doc_type,
  s.pages,
  s.created_date_raw,
  {{ project_questions('t.md_obj', 5) }}
from top_level t
join md_scalars s using (src_row_id)
