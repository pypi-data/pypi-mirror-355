Environment Variables
=====================

Environment variables are key-value pairs that can
affect the way running processes will behave on a computer. If 
you are running in a HPC environment using Slurm workload manager, 
then you can set these in the job description file.

Setting Environment Variables
------------------------------
1. **GROGUPY_ARCHITECTURE**: This variable sets the architecture
   for the grogupy project. By default, the architecture is set to
   CPU. To change it to GPU, you can set the `GROGUPY_ARCHITECTURE`
   environment variable:

   .. code-block:: bash

         export GROGUPY_ARCHITECTURE=GPU

2. **GROGUPY_TQDM**: With this variable you can request ``tqdm`` for 
   a nice progress bar. It can be set to true of false.

   .. code-block:: bash

         export GROGUPY_TQDM=TRUE

3. **CUDA** and **CuPy**: If you have a problem with GPU acceleration, 
   then you might have to set the appropriate variables to link CuPy
   with CUDA. For more information see :ref:`Fixing problems with GPU 
   <fix_gpu_linking>`.