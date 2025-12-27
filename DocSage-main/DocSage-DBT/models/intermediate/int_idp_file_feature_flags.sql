-- models/intermediate/int_idp_file_feature_flags.sql
select
  m.hash,
  m.user_id,
  case
    when m.question_1 is not null
     and m.question_2 is not null
     and m.question_3 is not null
     and m.question_4 is not null
     and m.question_5 is not null
    then 1 else 0
  end as has_five_questions
from {{ ref('stg_idp_metadata') }} m
