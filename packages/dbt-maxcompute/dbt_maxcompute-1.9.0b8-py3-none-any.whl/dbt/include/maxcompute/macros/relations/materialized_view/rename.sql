{% macro maxcompute__get_rename_materialized_view_sql(relation, new_name) %}
    {{ exceptions.raise_compiler_error(
        "maxcompute materialized view not support rename operation."
    ) }}
{% endmacro %}
