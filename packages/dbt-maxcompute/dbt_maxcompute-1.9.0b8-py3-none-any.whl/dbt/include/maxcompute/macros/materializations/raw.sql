{% materialization raw,  adapter='maxcompute' -%}
  {{ adapter.run_raw_sql(sql, config) }}
  {% call statement("main") %}
  {% endcall %}
  {{ return({'relations': []}) }}
{%- endmaterialization %}
