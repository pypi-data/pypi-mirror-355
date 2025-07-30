# grogupy: Relativistic magnetic interactions from non-orthogonal basis sets

[![PyPI version](https://badge.fury.io/py/grogupy.svg)](https://badge.fury.io/py/grogupy)
[![DOI](https://zenodo.org/badge/950552693.svg)](https://doi.org/10.5281/zenodo.15449541)
![Static Badge](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C-blue)
![Static Badge](https://img.shields.io/badge/License-MIT-blue)
![Static Badge](https://img.shields.io/badge/Code%20style-Black-black)

grogupy is an open-source package created to easily extract magnetic interaction 
parameters from density functional theory (DFT) calculations. It can also handle 
very large systems, with hundreds of atoms in the unit cell using GPU 
acceleration. Because the underlying theory focuses on non-orthogonal, LCAO, 
basis sets, the most straightforward software, and our recommendation to use for 
the DFT part is [Siesta](https://siesta-project.org/siesta). In principle any 
plane wave based DFT software could be used with Wannierization, but the magnetic 
parameters are very sensitive to the atomic positions and Wannier orbitals might 
be off centered. grogupy can extract magnetic parameters from different levels 
of theoretical complexity, for example it can use as input collinear, 
non-collinear and spin-orbit Hamiltonians using 
[sisl](https://sisl.readthedocs.io/en/latest/index.html). More on the 
theoretical background can be found on [arXiv](https://arxiv.org/abs/2309.02558). 
grogupy was created by the [TRILMAX Consortium](https://trilmax.elte.hu).

## Features ##

- Flexible API to set up more complicated systems with complex magnetic entities
- Command line interface to extract and visualize the magnetic parameters
- Multiple output formats for atomistic spin dynamics softwares
- Interactive visualizations for system exploration

## Tutorials and examples ##

You can start with the 
[Quick start guides](https://grogupy.readthedocs.io/en/latest/quickstart/index.html) 
or learn more about the best practices in the 
[Tutorials](https://grogupy.readthedocs.io/en/latest/tutorials/index.html) section.

## Documentation ##

The documentation can be found 
[here](https://grogupy.readthedocs.io/), and the API reference is 
[here](https://grogupy.readthedocs.io/en/latest/API/index.html).

## Installation ##

grogupy can be installed using `pip`:

```bash
pip install grogupy
```

Or you can install optional dependecies, like visualization packages or packages 
for MPI or GPU acceleration:

```bash
pip install grogupy[viz,mpi,gpu]
```
