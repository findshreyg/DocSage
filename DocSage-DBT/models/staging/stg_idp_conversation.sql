-- models/staging/stg_idp_conversation.sql
with base as (
  select
    -- stable surrogate id per physical row
    row_number() over (order by (select null)) as src_row_id,
    record
  from {{ source('idp','raw_idp_conversation') }}
),
flat as (
  -- flatten attributes within each physical row
  select
    b.src_row_id,
    f.key   as attr_name,
    f.value as attr_value
  from base b,
       lateral flatten(input => b.record) f
),
agg as (
  select
    -- choose grp_key: prefer file_hash_timestamp.S if present, else fallback to src_row_id
    coalesce(
      max(case when attr_name = 'file_hash_timestamp' then attr_value:"S"::string end),
      to_varchar(src_row_id)
    ) as grp_key,

    -- strings
    max(case when attr_name = 'user_id' then attr_value:"S"::string end) as user_id,
    max(case when attr_name = 'file_hash' then attr_value:"S"::string end) as file_hash,
    max(case when attr_name = 'file_hash_timestamp' then attr_value:"S"::string end) as file_hash_timestamp,
    max(case when attr_name = 'question' then attr_value:"S"::string end) as question,
    max(case when attr_name = 'answer' then attr_value:"S"::string end) as answer,
    max(case when attr_name = 'reasoning' then attr_value:"S"::string end) as reasoning,
    max(case when attr_name = 'data_quality_notes' then attr_value:"S"::string end) as data_quality_notes,
    max(case when attr_name = 'source' then attr_value:"S"::string end) as source_raw,
    max(case when attr_name = 'alternative_interpretations' then attr_value:"S"::string end) as alternative_interpretations_raw,

    -- numbers (Dynamo N as string)
    try_to_decimal(max(case when attr_name = 'confidence' then attr_value:"N"::string end)) as confidence,

    -- booleans
    max(case when attr_name = 'verified' then attr_value:"BOOL"::boolean end) as verified

  from flat
  group by src_row_id
)
select
  grp_key,
  user_id,
  file_hash,
  file_hash_timestamp,
  question,
  answer,
  confidence,
  verified,
  reasoning,
  data_quality_notes,
  source_raw,
  alternative_interpretations_raw
from agg
