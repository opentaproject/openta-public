.. role:: xml(code)
   :language: xml

.. _multipleChoice:

multipleChoice
==============

.. code-block:: xml

  <question type="multipleChoice">
   ...
  </question>

Multiple choice questions contains different alternatives where one or more can
be correct. They are answered by marking the correct alternatives and then
submitting. The content of the alternatives can be text, math or elements such
as figures.

.. code-block:: xml

  <question type="multipleChoice">
    <text>Pick the correct alternatives below.</text>
    <choice key="0">The first choice</choice>
    <choice key="1" correct="true">The second choice</choice>
    <choice key="2">The third choice</choice>
    <choice key="3" correct="true">The fourth choice</choice>
  </question>

The following tags can be used inside a **multipleChoice** block.

.. list-table::
  :header-rows: 1
  :widths: 20 10 70

  * - Tag 
    - Attributes
    - Description
  * - :xml:`<text>`
    -
    - Question text.
  * - :xml:`<choice>`
    - - ``key`` = [string] unique id (within question)
      - ``correct`` = ["true"] marks this alternative as correct.
    - An alternative for the answer. 
  * - :xml: `<hint>`
    -
    - Shows a hint if the student answers incorrectly.
  * - :xml:`<rate>`
    -
    - Specifies how many tries a student can make per length of time. The time
      is specified as "number/unit" where unit is s (second) or h (hour). For
      example :xml:`<rate>3/h</rate>` permits three tries per hour. See `rates
      <https://django-ratelimit.readthedocs.io/en/v1.0.0/rates.html>`_ for the
      detailed syntax description.

Examples
--------

Basic (with math)
^^^^^^^^^^^^^^^^^^

.. code-block:: xml

  <question type="multipleChoice">
    <text>How many people live of planet earth?</text>
    <choice key="0">$9\ctimes 10^9$</choice>
    <choice key="1" correct="true">$9\ctimes 10^10$</choice>
    <choice key="2">$9\ctimes 10^11$</choice>
  </question>
