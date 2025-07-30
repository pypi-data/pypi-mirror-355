.. module:: grogupy
   :no-index:

.. title:: grogupy: Relativistic magnetic interactions from non-orthogonal basis sets
.. meta::
   :description: Relativistic magnetic interactions from non-orthogonal basis sets.
   :keywords: DFT, physics, grogupy, magnetic interactions, Siesta


grogupy: Relativistic magnetic interactions from non-orthogonal basis sets
==========================================================================


.. image:: https://badge.fury.io/py/grogupy.svg
  :target: https://badge.fury.io/py/grogupy

.. image:: https://zenodo.org/badge/950552693.svg
  :target: https://doi.org/10.5281/zenodo.15449541
  
.. image:: https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C-blue
  :target: https://www.python.org

.. image:: https://img.shields.io/badge/License-MIT-blue
  :target: https://tlo.mit.edu/understand-ip/exploring-mit-open-source-license-comprehensive-guide

.. image:: https://img.shields.io/badge/Code%20style-Black-black
  :target: https://github.com/psf/black/

grogupy is an open-source package created to easily extract magnetic interaction 
parameters from density functional theory (DFT) calculations. It can also handle 
very large systems, with hundreds of atoms in the unit cell using GPU 
acceleration. Because the underlying theory focuses on non-orthogonal, LCAO, 
basis sets, the most straightforward software, and our recommendation to use 
for the DFT part is `Siesta <https://siesta-project.org/siesta/>`_. In principle 
any plane wave based DFT software could be used with Wannierization, but the 
magnetic parameters are very sensitive to the atomic positions and Wannier 
orbitals might be off centered. grogupy can extract magnetic parameters from 
different levels of theoretical complexity, for example it can use as input 
collinear, non-collinear and spin-orbit Hamiltonians using `sisl 
<https://sisl.readthedocs.io/en/latest/index.html>`_. More on the theoretical 
background can be found on `arXiv <https://arxiv.org/abs/2309.02558>`_. 
grogupy was created by the `TRILMAX Consortium <https://trilmax.elte.hu>`_ and 
the source code is available on `github <https://github.com/danielpozsar/grogupy>`_.

.. grid:: 1 1 2 2
    :gutter: 2

    .. grid-item-card:: -- Quick-start guides
        :link: quickstart/index
        :link-type: doc

        Simple tutorial to introduce the grogupy package.

    .. grid-item-card:: -- Tutorials
        :link: tutorials/index
        :link-type: doc

        In depth tutorials to explore all the possibilities
        with grogupy.

    .. grid-item-card::  -- API reference
        :link: API/index
        :link-type: doc

        Detailed description of the implementation for advanced users.


    .. grid-item-card::  -- Contributing to grogupy
        :link: development/index
        :link-type: doc

        Guides for developers.

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Getting started

   introduction
   quickstart/index
   citing

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: User Guide

   tutorials/index

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Advanced usage

   API/index
   environment/index

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Development

   development/index

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Extras

   changelog/index
   bibliography
