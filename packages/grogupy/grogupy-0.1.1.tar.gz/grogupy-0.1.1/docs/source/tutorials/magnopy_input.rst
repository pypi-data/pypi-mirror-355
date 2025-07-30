.. _magnopy_input_format:

Magnopy input format
====================

Spin Hamiltonian file
---------------------

On this page we describe the format of the spin Hamiltonian file that can be produced by GROGU.
First of all here is the specification of the full file

.. literalinclude:: magnopy-input-specs.txt
    :linenos:
    :language: text 


The file is composed by a number of sections. Sections are separated by approximately 80 "=" symbols.
Some of the sections have subsections, that are separated by approximately 40 "-" symbols.
Next we describe the sections of the file one by one.

.. _user-guide_output-format_comment-section:

Comment section
---------------

.. literalinclude:: magnopy-input-specs.txt
    :linenos:
    :lineno-match:
    :lines: 1-7
    :language: text 

====== =========================================================================
line   Formal description
====== =========================================================================
1      Section separator. Approximately 80 "=" symbols.
2-6    Any amount of lines. Undocumented comments with usefull information.
7      Section separator. Approximately 80 "=" symbols.
====== =========================================================================

This section might list the detatils of the GROGU calculations or of the
underlying DFT calcuation. The amount of lines in this section is arbitrary and
might be different in different versions of GROGU. The content of this section
is not restricted and can be arbitrary as well.

.. _user-guide_output-format_hamiltonian-convention:

Hamiltonian convention
----------------------

.. literalinclude:: magnopy-input-specs.txt
    :linenos:
    :lineno-match:
    :lines: 7-13
    :language: text 


====== =========================================================================
line   Formal description
====== =========================================================================
7      Section separator. Approximately 80 "=" symbols.
8      Keyword ``Hamiltonian convention``.
9      Keyword ``Double counting`` followed by at least one space symbol and the
       value keyword ``true``.
10     Keyword ``Normalized spins`` followed by at least one space symbol and the
       value keyword ``true``.
11     Keyword ``Intra-atomic factor`` followed by at least one space symbol and
       the value ``+1``.
12     Keyword ``Exchange factor`` followed by at least one space symbol and the
       value ``+0.5``.
13     Section separator. Approximately 80 "=" symbols.
====== =========================================================================

This section has a fixed amount of lines. It describes the convention of the
spin Hamiltonian in GROGU. The parameters of the file should be interpreted
together with this convention.

The Hamiltonian in this convention would be written as

.. math::

    \mathcal{H}
    =
    \sum_{i}
    \boldsymbol{e}_{i}
    \cdot
    \boldsymbol{A}_{i}
    \cdot
    \boldsymbol{e}_{i}
    +
    \dfrac{1}{2}
    \sum_{i \ne j}
    \boldsymbol{e}_{i}
    \cdot
    \boldsymbol{J}_{ij}
    \cdot
    \boldsymbol{e}_{j}

where :math:`\boldsymbol{e}_{i} = \boldsymbol{S}_{i}/S_i` is a spin vector operator 
normalised by its value (thus ``Normalized spins true`` in the convention); 
:math:`\boldsymbol{A}_{i}` is an intra-atomic anisotropy tensor; :math:`\boldsymbol{J}_{ij}` 
is a full matrix of the exchange parameter. Both pairs 
:math:`\boldsymbol{e}_{i}\boldsymbol{J}_{ij}\boldsymbol{e}_{j}` and 
:math:`\boldsymbol{e}_{j}\boldsymbol{J}_{ji}\boldsymbol{e}_{i}` are explicitly included in the
sum (hence the ``Double counting true`` in the convention).

.. _user-guide_output-format_cell:

Cell
----

.. literalinclude:: magnopy-input-specs.txt
    :linenos:
    :lineno-match:
    :lines: 13-18
    :language: text 


====== =========================================================================
line   Formal description
====== =========================================================================
13     Section separator. Approximately 80 "=" symbols.
14     Keyword ``Cell (Ang)``.
15     Three numbers separated by at least one space symbol. Components of the 
       first lattice vector :math:`\boldsymbol{a}_1 = (a_1^x, a_1^y, a_1^z)`
       given in Angstroms.
16     Three numbers separated by at least one space symbol. Components of the 
       second lattice vector :math:`\boldsymbol{a}_2 = (a_2^x, a_2^y, a_2^z)`
       given in Angstroms.
17     Three numbers separated by at least one space symbol. Components of the 
       third lattice vector :math:`\boldsymbol{a}_3 = (a_3^x, a_3^y, a_3^z)`
       given in Angstroms.
18     Section separator. Approximately 80 "=" symbols.
====== =========================================================================

This section describes the (unit or super) cell of the underlying periodic lattice on which the
spin Hamiltonian is defined. 

.. _user-guide_output-format_magnetic-sites:

Magnetic sites
--------------

.. literalinclude:: magnopy-input-specs.txt
    :linenos:
    :lineno-match:
    :lines: 18-25
    :language: text

====== =========================================================================
line   Formal description
====== =========================================================================
18     Section separator. Approximately 80 "=" symbols.
19     Keyword ``Magnetic sites``.
20     Keyword ``Number of sites`` followed by at least one space symbol and one
       integer number :math:`M`.
21     Line with the headers.
22     Line with the description of the first magnetic site. 8 elements on the
       line, the elements are separated by at least one space symbol.

       *   ``Name`` - a string that do not contain no space symbols. Serves as
           the identifier of the magnetic site. The name of every magnetic site
           should be unique.
       *   ``r1_x r1_y r1_z`` - three numbers. Absolute coordinates of the
           magnetic site given in Angstroms.
       *   ``s1`` - one number. Spin value (or magnitude of spin) of the
           magnetic site. Always positive.
       *   ``s1_x s1_y s1_z``- three numbers. Direction of the spin vector
           operator.
23     Specification of the other :math:`M-2` magnetic sites.
24     Specification of the last magnetic site.
25     Section separator. Approximately 80 "=" symbols.
====== =========================================================================

This section describes the magnetic sites that constitute the basis of the spin Hamlitonian.
Magnetic sites can correspond to the atoms of the underlying crystall or to more complex structures.

.. _user-guide_output-format_intra-atomic-anisotropy:

Intra-atomic anisotropy
-----------------------

.. literalinclude:: magnopy-input-specs.txt
    :linenos:
    :lineno-match:
    :lines: 25-36
    :language: text

====== =========================================================================
line   Formal description
====== =========================================================================
25     Section separator. Approximately 80 "=" symbols.
26     Keyword ``Intra-atomic anisotropy tensor (meV)``.
27     Subsection separator. Approximately 40 "-" symbols.
28     One string that do not contain no spaces. Name of the magnetic site,
       with which the parameter is associated. Should match one of the names
       from the :ref:`user-guide_output-format_magnetic-sites` section.
29     Keyword ``Matrix``.
30-32  Full matrix of the intra-atomic anisotropy parameter. Each line contains
       three numbers. Numbers in each line separated by at least one space
       symbol.   
33     Subsection separator. Approximately 40 "-" symbols.
34     More subsections with other :math:`(M-1)` parameters. Each subsection
       has same format as the first one.
35     Subsection separator. Approximately 40 "-" symbols.
36     Section separator. Approximately 80 "=" symbols.
====== =========================================================================

This section lists parameters of the intra-atomic anisotropy of the spin
Hamiltonian :math:`\boldsymbol{A}_{i}`

.. math::

    \boldsymbol{A}_i
    =
    \begin{pmatrix}
        A_i^{xx} & A_i^{xy} & A_i^{xz} \\
        A_i^{xy} & A_i^{yy} & A_i^{yz} \\
        A_i^{xz} & A_i^{yz} & A_i^{zz} \\
    \end{pmatrix}

.. _user-guide_output-format_exchange-interaction:

Exchange interaction
--------------------
 
.. literalinclude:: magnopy-input-specs.txt
    :linenos:
    :lineno-match:
    :lines: 36-50
    :language: text

====== =========================================================================
line   Formal description
====== =========================================================================
36     Section separator. Approximately 80 "=" symbols.
37     Keyword ``Exchange tensor (meV)``.
38     Keyword ``Number of pairs`` followed by at least one space symbol,
       followed by one number :math:`N`.
39     Subsection separator. Approximately 40 "-" symbols.
40     Line with the header for the pair specification.
41     Subsection separator. Approximately 40 "-" symbols.
42     Specification of the first pair. 5 elements on the
       line, the elements are separated by at least one space symbol.

       *   ``Name1`` - a string that do not contain no space symbols. Serves
           as the identifier of the magnetic site from the :math:`(0, 0, 0)`
           cell. Should match one of the names from the
           :ref:`user-guide_output-format_magnetic-sites` section.
       *   ``Name2`` - a string that do not contain no space symbols. Serves
           as the identifier of the magnetic site from the :math:`(i, j, k)`
           cell. Should match one of the names from the
           :ref:`user-guide_output-format_magnetic-sites` section.
       *   ``i j k`` - three integer numbers. Specify the unit cell for 
           the second magnetic site. the position of the unit cell is 
           defined as 
           :math:`i\cdot\boldsymbol{a}_1 + j\cdot\boldsymbol{a}_2 + k\cdot\boldsymbol{a}_3`
       *   ``d``- one number. A distance between the first magnetic site in
           the unit cell :math:`(0, 0, 0)` and the second magnetic site in 
           the unit cell :math:`(i, j, k)`.
43     Keyword ``Matrix``.
44-46  Full matrix of the exchange parameter. Each line contains three numbers.
       Numbers in each line separated by at least one space symbol.
47     Subsection separator. Approximately 40 "-" symbols.
48     More subsections with other :math:`(N-1)` parameters. Each subsection
       has same format as the first one.
49     Subsection separator. Approximately 40 "-" symbols.
50     Section separator. Approximately 80 "=" symbols.
====== =========================================================================

The last section list full matrix of the biliniar exchange parameters :math:`\boldsymbol{J}_{ij}`.
Full matrix can be decomposed into three primary parts

*   Isotropic exchange

    .. math::
        J_{ij}^{isotropic}
        =
        \text{Tr}(\boldsymbol{J}_{ij})
* Symmetric traceless anisotropy

    .. math::
        \boldsymbol{J}_{ij}^{aniso, symm}
        =
        \dfrac{\boldsymbol{J}_{ij} + \boldsymbol{J}_{ij}^T}{2}
        -
        \dfrac{\text{Tr}(\boldsymbol{J}_{ij})}{3}
        \begin{pmatrix}
            S_i^{xx} & S_i^{xy} & S_i^{xz} \\
            S_i^{xy} & S_i^{yy} & S_i^{yz} \\
            S_i^{xz} & S_i^{yz} & S_i^{zz} \\
        \end{pmatrix}
* Antisymmetric part

    .. math::
        \boldsymbol{J}_{ij}^{dmi}
        =
        \dfrac{\boldsymbol{J}_{ij} - \boldsymbol{J}_{ij}^T}{2}
        =
        \begin{pmatrix}
            0         & D^z_{ij}  & -D^y_{ij} \\
            -D^z_{ij} & 0         & D^x_{ij} \\
            D^y_{ij}  & -D^x_{ij} & 0 
        \end{pmatrix}

Antysymmetric part can be written in a form of the Dzyaloshinskii-Moriya interaction (DMI) as

.. math::

    \mathcal{H}^{dmi}
    =
    \dfrac{1}{2}
    \sum_{i\ne j}
    \boldsymbol{e}_{i}
    \cdot
    \boldsymbol{J}^{dmi}_{ij}
    \cdot
    \boldsymbol{e}_{j}
    =
    \dfrac{1}{2}
    \sum_{i\ne j}
    \boldsymbol{D}_{ij}
    \cdot
    (
    \boldsymbol{e}_{i}
    \times
    \boldsymbol{e}_{j})

where :math:`\boldsymbol{D}_{ij} = (D^x_{ij}, D^y_{ij}, D^z_{ij})`.
