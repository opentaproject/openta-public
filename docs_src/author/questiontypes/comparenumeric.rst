.. role:: xml(code)
   :language: xml

.. _compareNumeric:

compareNumeric
==============

.. code-block:: xml

  <question type="compareNumeric">
   ...
  </question>

The answer is a symbolic or numeric expression in a set of variables. Student answers are graded by comparing them with the correct expression by random numeric sampling.

The following tags can be used inside a **compareNumeric** block.

.. list-table::
  :header-rows: 1
  :widths: 20 10 70

  * - Tag 
    - Attributes
    - Description
  * - :xml:`<text>`
    -
    - Question text shown in viscinity of the input field.
  * - :xml:`<expression>`
    - 
    - Expression for the correct answer
  * - :xml:`<variables>`
    - 
    - Variables in semicolon separated list of var=value, e.g. "x=1;y=2;"

Examples
--------

Basic
^^^^^

.. code-block:: xml

  <question type="compareNumeric">
    <text>What is 1+1?</text>
    <expression>2</expression>
  </question>

Variables
^^^^^^^^^

.. code-block:: xml

  <question type="compareNumeric">
    <variables>
      a=3; b=5;
    </variables>
    <text>
      What is the length of the hypotenuse of a right angled 
      triangle with sides a and b?
    </text>
    <expression>sqrt(a^2+b^2)</expression>
  </question>

Global variables, multiple questions, latex, units
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: xml

  <exercise>
    <exercisename>Momentum and energy</exercisename>
    <text>
      A particle with mass $m$ is moving with velocity $v$.
    </text>

    <global type="compareNumeric">
      m = kg; v = meter / second;
    </global>

    <question type="compareNumeric">
      <text>
        What is the linear momentum of the particle?
      </text>
      <expression>m*v</expression>
    </question>

    <question type="compareNumeric">
      <text>
        What is the kinetic energy of the particle?
      </text>
      <expression>m*v^2/2</expression>
    </question>
  </exercise>
