{% macro maxcompute__get_alter_materialized_view_as_sql(
    relation,
    new_config,
    sql,
    existing_relation,
    backup_relation,
    intermediate_relation
) %}
    {{ get_replace_sql(existing_relation, relation, sql) }}
{% endmacro %}

{% macro maxcompute__get_materialized_view_configuration_changes(existing_relation, new_config) %}
{% endmacro %}
