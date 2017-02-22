.. _exercise_xml:

.. role:: xml(code)
   :language: xml

Exercise XML format
===================

This first part describes the XML tags that are common to all exercises.

.. list-table:: Top level tags

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
    - - key = unique id (within the exercise)
      - type = question type (see ...)
    - Question root tag
  * - :xml:`<global>`
    - - type = question type (optional)
    - Data that will be passed to all questions in this exercise. For example variables for multiple symbolic questions.

--------------
Question types
--------------

^^^^^^^^^^^^^^
compareNumeric
^^^^^^^^^^^^^^

The answer is a symbolic or numeric expression in a set of variables. Student answers are graded by comparing them with the correct expression by random numeric sampling.
