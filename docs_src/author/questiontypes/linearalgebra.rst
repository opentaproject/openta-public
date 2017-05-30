.. role:: xml(code)
   :language: xml

.. _linearAlgebra:

linearAlgebra
==============

.. code-block:: xml

  <question type="linearAlgebra">
   ...
  </question>

Can be used when the answer is a symbolic or numeric expression in a set of variables, possibly vector or matrix-valued. Student answers are graded by comparing them with the correct expression, optionally by random sampling. This questiontype should be thought of as a superset of compareNumeric, containing the same functionality but with greater flexibility, including vector and matrix support.

Vectors and matrices are defined using square brackets and can be unitful. For example a 3-vector can be written as **[1,2,3]**. A matrix is similarly entered as **[[1,0], [0,1]]**, where the inner vectors corresponds to the rows of the matrix. There are a number of vector operators available (see the help button for a linearAlgebra question for the full list) such as **cross(v1,v2)**, **dot(v1,v2)** and **norm(v)**.

Scalar variables can be defined as random sampled using the function `sample(value1, value2, ...)`. The answer will be compared using random sampling in a neighbourhood around each value. **Note that this is not automatic as with compareNumeric**. For example to correctly grade an answer containing the absolute value function,

.. code-block:: xml

  <question type="linearAlgebra">
    <variables>
      x = sample(1, -1)
    </variables>
    <text>
     What is $\sqrt(x^2)$?
    </text>
    <expression>abs(x)</expression>
  </question>

The following tags can be used inside a **linearAlgebra** block.

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
  * - :xml:`<blacklist>`
    - 
    - List of subtags `<token></token>` containing tokens (variables, functions or operators) that are not allowed in the answer. 

Examples
--------

Basic
^^^^^

.. code-block:: xml

  <question type="linearAlgebra">
    <text>What is 1+1?</text>
    <expression>2</expression>
  </question>

Variables
^^^^^^^^^

.. code-block:: xml

  <question type="linearAlgebra">
    <variables>
      omega=[1,0,0]; r=[0,1,0];
    </variables>
    <text>
      What is the velocity of a particle at a point $\vec{r}$ rotating around the origin with angular velocity $\vec{omega}$?
    </text>
    <expression>cross(omega, r)</expression>
  </question>

Global variables, multiple questions, latex, units
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: xml

  <exercise>
    <exercisename>Momentum and energy</exercisename>
    <text>
      A particle with mass $m$ is moving with velocity $\vec{v}$.
    </text>

    <global type="linearAlgebra">
      x = sample(1)
      m = kg; v = [x, 0, 0] meter / second;
    </global>

    <question type="linearAlgebra">
      <text>
        What is the linear momentum of the particle?
      </text>
      <expression>m*v</expression>
    </question>

    <question type="linearAlgebra">
      <text>
        What is the kinetic energy of the particle?
      </text>
      <expression>m*dot(v, v)/2</expression>
    </question>
  </exercise>
