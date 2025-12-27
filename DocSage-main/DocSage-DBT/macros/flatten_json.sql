-- macros/flatten_json.sql
{% macro flatten_json(source_ref, object_key=None) -%}
  (
    select
      f.value as value,
      f.key   as attr_key,
      f.path  as attr_path,
      f.index as attr_index
    from {{ source_ref }} as src,
         lateral flatten(input => {% if object_key %} src.{{ object_key }} {% else %} coalesce(src.record, src.data, src.payload) {% endif %}) as f
  )
{%- endmacro %}
