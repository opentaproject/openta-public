.. _exercise_xml:

.. role:: xml(code)
   :language: xml

Exercise XML format
===================

This first part describes the XML tags that are common to all exercises.

.. list-table:: Top level tags
  :widths: 20 40 40
  :header-rows: 1

  * - Tag 
    - Attributes
    - Description
  * - :xml:`<exercise>` 
    -
    - Root tag
  * - :xml:`<exercisename>`
    -
    - The visible name/title of the exercise
  * - :xml:`<question>`
    - - ``key`` = unique id (within the exercise)
      - ``type`` = question type (see ...)
    - Question root tag
  * - :xml:`<global>`
    - - ``type`` = question type (optional)
    - Data that will be passed to all questions in this exercise. For example variables for multiple symbolic questions.

--------------
Question types
--------------

^^^^^^^^^^^^^^
compareNumeric
^^^^^^^^^^^^^^
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

""""""""
Example
""""""""

.. code-block:: xml

  <question type="compareNumeric">
    <text>What is 1+1?</text>
    <expression>2</expression>
  </question>
