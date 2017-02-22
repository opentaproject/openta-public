.. _intro:

Introduction
============

Content in OpenTA consists of exercises with one or many questions. An exercise and its questions are created using a custom `XML <https://en.wikipedia.org/wiki/XML>`_ format. For example,

.. code-block:: xml

  <exercise>
    <exercisename>Kinetic energy</exercisename>
    <text>
      What is the kinetic energy of a particle with mass $m$ 
      moving with velocity $v$?
    </text>
    <question key="1" type="compareNumeric">
      <variables>
        m = kg; v = meter / second;
      </variables>
      <expression>
        m*v^2/2
      </expression>
    </question>
  </exercise>

In this example the question type compareNumeric is used which compares the student answer with the correct answer by random sampling.
