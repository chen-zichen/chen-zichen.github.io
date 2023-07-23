---
layout: page
permalink: /publications/
title: publications
description: \* contributes equally to this work. \+ the first author is my guided student.
years: [2023]
nav: true
nav_order: 2

---
<!-- _pages/publications.md -->
<div class="publications">

{%- for y in page.years %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f papers -q @*[year={{y}}]* %}
{% endfor %}
<!-- if the year is before 2022 -->
<h2 class="year">Before</h2>
{% bibliography -f papers -q @*[year=2022]* %}
{% bibliography -f papers -q @*[year=2021]* %}
{% bibliography -f papers -q @*[year=2020]* %}
{% bibliography -f papers -q @*[year=2019]* %}

</div>
