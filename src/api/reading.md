---
title: Reading APIs
...
{% set cat = category("api-reading") %}

# {{ cat.title }}

{{ cat.description }}

{% for doc in cat.documents %}
## {{ doc.title }}

{{ doc.description }}

{% for link in doc.links %}
* [{{ link.label }}]({{ link.url }})
{% endfor %}
{% endfor %}
