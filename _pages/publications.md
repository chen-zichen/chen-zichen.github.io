---
layout: page
permalink: /publications/
title: publications
description: \[ \* \] contributes equally to this work. \[ \+ \] the first author is my guided student.
years: [2023,2022,2021,2020,2019]
nav: true
nav_order: 2

---
<!-- _pages/publications.md -->
<div class="publications">

{%- for y in page.years %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f papers -q @*[year={{y}}]* %}
{% endfor %}

</div>
