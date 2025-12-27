-- models/mart/mrt_idp_metadata_question_feature_usage.sql
with flags as (
  select
    user_id,
    hash,
    has_five_questions
  from {{ ref('int_idp_file_feature_flags') }}
),
users_with_feature as (
  select distinct user_id
  from flags
  where has_five_questions = 1
),
files_with_feature as (
  select hash, user_id
  from flags
  where has_five_questions = 1
),
per_user as (
  select
    user_id,
    count(*) as files_with_5q
  from files_with_feature
  group by user_id
),
totals as (
  select
    count(distinct user_id) as users_using_questions,
    count(*) as files_with_5q_total
  from files_with_feature
)
select
  t.users_using_questions,
  t.files_with_5q_total,
  -- expose per-user distribution for downstream BI
  p.user_id,
  p.files_with_5q
from totals t
left join per_user p
  on 1=1
order by p.files_with_5q desc nulls last
