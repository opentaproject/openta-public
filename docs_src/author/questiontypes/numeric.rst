.. role:: xml(code)
   :language: xml

.. _numeric:

Numeric
==============

.. code-block:: xml

  <question type="Numeric">
   ...
  </question>

Question with a numeric answer that has a certain tolerance for error.

.. code-block:: xml

  <question type="Numeric" precision="0.005">
    <text>What is $\sqrt{2}$?</text>
    <expression>1.44</expression>
  </question>

The following tags can be used inside a **Numeric** block.

.. list-table::
  :header-rows: 1
  :widths: 20 10 70

  * - Tag 
    - Attributes
    - Description
  * -
    - - ``precision`` = [string] String with a floating point number representing the relative tolerance of the answer. 
    - For example :xml:`<question type="Numeric" precision="0.05">` will accept answers within a 5% interval of the correct answer, i.e. :math:`correct \pm 0.05 \cdot correct`.
  * - :xml:`<text>`
    -
    - Question text.
  * - :xml:`<expression>`
    -
    - The correct answer. 
  * - :xml:`<rate>`
    -
    - Specifies how many tries a student can make per length of time. The time
      is specified as "number/unit" where unit is s (second) or h (hour). For
      example :xml:`<rate>3/h</rate>` permits three tries per hour. See `rates
      <https://django-ratelimit.readthedocs.io/en/v1.0.0/rates.html>`_ for the
      detailed syntax description.

Examples
--------

Basic
^^^^^^^^^^^^^^^^^^

.. code-block:: xml

  <question type="Numeric">
  </question>

Advanced
^^^^^^^^^^^^^^^^^^

.. code-block:: xml

  <question type="Numeric">
  </question>
