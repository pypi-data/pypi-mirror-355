.. _citing:

.. image:: https://zenodo.org/badge/950552693.svg
  :target: https://doi.org/10.5281/zenodo.15449541

Citing grogupy
==============
grogupy is a completely open-source software package released under the 
MIT license. You should always cite the underlying paper *Relativistic 
magnetic interactions from nonorthogonal basis sets*.

|version|

.. code-block:: bibtex

    @article{martinez2023relativistic,
        title={Relativistic magnetic interactions from nonorthogonal basis sets},
        author={Mart{\'\i}nez-Carracedo, Gabriel and Oroszl{\'a}ny, L{\'a}szl{\'o} and Garc{\'\i}a-Fuente, Amador and Ny{\'a}ri, Bendeg{\'u}z and Udvardi, L{\'a}szl{\'o} and Szunyogh, L{\'a}szl{\'o} and Ferrer, Jaime},
        journal={Physical Review B},
        volume={108},
        number={21},
        pages={214418},
        year={2023},
        publisher={APS}
    }

If you want to make grogupy available for more researchers and support 
the development of grogupy you can cite it through zenodo.

.. code-block:: bibtex
    :substitutions:

    @software{zerothi_grogupy,
        author={Daniel, Pozsar},
        title={grogupy: v|release|},
        year={2025},
        doi={10.5281/zenodo.15449541},
        url={https://doi.org/10.5281/zenodo.15449541}
    }

grogupy builds on the sisl package as well, which should also be cited.

.. code-block:: bibtex
    :substitutions:

    @software{zerothi_sisl,
        author={Papior, Nick},
        title={sisl: v|sisl_version|},
        year={2024},
        doi={10.5281/zenodo.597181},
        url={https://doi.org/10.5281/zenodo.597181}
    }

All the command line scripts and the ``grogupy`` package can print out the 
citation in **bibtex** format.

.. code-block:: python3
    :substitutions:

    >>> import grogupy
    >>> print(grogupy.cite)
        @article{martinez2023relativistic,
            title={Relativistic magnetic interactions from nonorthogonal basis sets},
            author={Mart{\'\i}nez-Carracedo, Gabriel and Oroszl{\'a}ny, L{\'a}szl{\'o} and Garc{\'\i}a-Fuente, Amador and Ny{\'a}ri, Bendeg{\'u}z and Udvardi, L{\'a}szl{\'o} and Szunyogh, L{\'a}szl{\'o} and Ferrer, Jaime},
            journal={Physical Review B},
            volume={108},
            number={21},
            pages={214418},
            year={2023},
            publisher={APS}
        }

        @software{zerothi_grogupy,
            author={Daniel, Pozsar},
            title={grogupy: v|release|},
            year={2025},
            doi={10.5281/zenodo.15449541},
            url={https://doi.org/10.5281/zenodo.15449541}
        }

        @software{zerothi_sisl,
            author={Papior, Nick},
            title={sisl: v|sisl_version|},
            year={2024},
            doi={10.5281/zenodo.597181},
            url={https://doi.org/10.5281/zenodo.597181}
        }


.. code-block:: console
    :substitutions:

    grogupy_run --cite
    
    @article{martinez2023relativistic,
        title={Relativistic magnetic interactions from nonorthogonal basis sets},
        author={Mart{\'\i}nez-Carracedo, Gabriel and Oroszl{\'a}ny, L{\'a}szl{\'o} and Garc{\'\i}a-Fuente, Amador and Ny{\'a}ri, Bendeg{\'u}z and Udvardi, L{\'a}szl{\'o} and Szunyogh, L{\'a}szl{\'o} and Ferrer, Jaime},
        journal={Physical Review B},
        volume={108},
        number={21},
        pages={214418},
        year={2023},
        publisher={APS}
    }

    @software{zerothi_grogupy,
        author={Daniel, Pozsar},
        title={grogupy: v|release|},
        year={2025},
        doi={10.5281/zenodo.15449541},
        url={https://doi.org/10.5281/zenodo.15449541}
    }

    @software{zerothi_sisl,
        author={Papior, Nick},
        title={sisl: v|sisl_version|},
        year={2024},
        doi={10.5281/zenodo.597181},
        url={https://doi.org/10.5281/zenodo.597181}
    }

