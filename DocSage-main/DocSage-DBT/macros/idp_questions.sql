-- macros/idp_questions.sql
{% macro project_questions(md_obj_ref, count=5) -%}
  {# md_obj_ref should be a SQL expression pointing to the metadata M-object, e.g., md_obj #}
  {%- for i in range(count) -%}
    ({{ md_obj_ref }}:"questions":"L"[{{ i }}]:"S")::string as question_{{ i + 1 }}{{ "," if not loop.last }}
  {%- endfor -%}
{%- endmacro %}
