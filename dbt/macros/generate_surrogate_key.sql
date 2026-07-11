{% macro generate_surrogate_key(columns) -%}
    md5(concat_ws('||', {% for column in columns %}coalesce({{ column }}::text, ''){% if not loop.last %}, {% endif %}{% endfor %}))
{%- endmacro %}
