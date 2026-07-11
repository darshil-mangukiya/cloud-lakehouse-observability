{% macro safe_cast_numeric(column_name) -%}
    nullif(regexp_replace({{ column_name }}::text, '[^0-9\.-]', '', 'g'), '')::numeric
{%- endmacro %}
