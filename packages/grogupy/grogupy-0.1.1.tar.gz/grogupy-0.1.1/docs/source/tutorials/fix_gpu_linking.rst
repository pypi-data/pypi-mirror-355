.. _fix_gpu_linking:


Fixing problems with GPU
========================

If you use GPU acceleration with CuPy you should be somewhat 
aware of the CUDA installation on the HPC that you are using. 
If you have some linking issues, then a quick fix can be to 
set **LD_LIBRARY_PATH**. This is not the most elegant method, 
but usually it is the easiest to set up. For example if CuPy 
cannot find **libnvrtc.so.11.2** on the HPC that we use you 
can set:

.. code-block:: bash

    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/software/packages/cuda/12.3/targets/x86_64-linux/lib

If you have no idea where to find the libraries that CuPy tries 
to access, then you should read `this 
<https://docs.nvidia.com/cuda/cuda-quick-start-guide/>`_ page of 
the documentation of CUDA. Here is a quick summary for the 
recommended way to set up for Linux users:

1. If you are using HPC, then usually you can load CUDA by first 
    finding the module that you need:

    .. code-block:: bash

        module spider cuda

    grogupy uses CuPy for GPU acceleration, you can read more about 
    which CUDA version CuPy supports `here 
    <https://docs.cupy.dev/en/stable/install.html>`_, but currently it 
    can work with every major CUDA version, so you should choose the 
    default for simplicity. Then you can load the CUDA that you choose:

    .. code-block:: bash

        module load <cuda-module>

    If you are using your own machine then you can get your CUDA version 
    by running

    .. code-block:: bash

        nvcc --version

2. Then you should choose a Python module, which should be the same that 
    you will use in the sbatch script and load it as well in a similar way.

3. At this point the CUDA and Python version should be resolved, now you 
    should install grogupy with GPU acceleration:

    .. code-block:: bash

        python -m pip install grogupy[gpu]

    You should use ``python -m``, so you do not use another install of pip 
    by accident.

4. Now you can install the nvidia index, where you can get the missing 
    libraries:

    .. code-block:: bash

        python3 -m pip install --upgrade setuptools pip wheel
        python3 -m pip install nvidia-pyindex

5. Finally you have to find out which nvidia package contain the missing 
    library. You should take a look at the Metapackages chapter in the 
    documentation of CUDA above. The names are quite descriptive if you 
    are missing **libnvrtc.so.11.2**, then you should install 
    **nvidia-cuda-nvrtc-cu11**, if you use CUDA 12, then change the 
    version number to 12. Now install the choosen library:

    .. code-block:: bash

        python3 -m pip install <nvidia-library>

6. If you did everything as advised, then the missing CUDA library should 
    be in the **nvidia** folder in the **site-packages** of the used 
    Python version. Usually it is in 
    **/home/<user-name>/.local/lib/python3.9/site-packages/nvidia**. If you 
    used a different Python, for example one that was installed by Conda, 
    then you can find the folder by running:

    .. code-block:: bash

        which python3

    The **site-packages** will be one level up, next to **bin**.

7. Finally you can link the appropriate library to CuPy:

    .. code-block:: bash

        export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/<user-name>/.local/lib/python3.9/site-packages/nvidia/<nvidia-library>/lib
