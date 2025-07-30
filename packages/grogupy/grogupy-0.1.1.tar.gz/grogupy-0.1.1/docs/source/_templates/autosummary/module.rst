{{ name | escape | underline }}

.. automodule:: {{ fullname }}

   {% block functions %}
   {% if functions %}
   .. rubric:: Functions

   .. autosummary::
      :toctree:
      {% for item in functions %}
      {% if item.__module__ == fullname %}
      {{ item }}
      {% endif %}
      {% endfor %}
   {% endif %}
   {% endblock %}
