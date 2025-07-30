Memory management
=================

If you are working on large systems, with hundreds of atoms in the unit cell, 
then the Hamiltonian of the system can be a very large matrix. In this case 
storing all the intermediate data and keeping enough memory for the matrix 
inversion can be memory consuming. In this special scenario, where the 
bottleneck is not the runtime, but the total memory of the hardware, then you 
should use the memory management part of grogupy. There could be two possible 
problems, the first one is the memory overflow in RAM and the second one is the 
memory overflow on a single GPU in the GPU accelerated case. Usually the 
statistics of a job can be checked by the **jobstats** command and some HPC 
environments like Komondor (https://jobstats.komondor.hpc.einfra.hu) provide a 
more detailed interactive dashboard.

Overflow in RAM
---------------

The first thing to try is to turn on the **low memory mode** , where grogupy 
discards some temporary data that could be useful for interactive work and some 
post processing.

.. code-block:: python

   low_memory_mode = True

If this does not solve the problem and if you are not using GPU acceleration, 
then there are two feasible paths to counter memory allocation errors. The 
first is to change the parameters of the SLURM job, by **increasing the 
allocated memory for each task**. If you already used up all the computation 
and memory resources on the node, then you could try to decrease the number of 
processes and increase the memory allocated to each process. The CPUs that 
were used in different processes for the parallelization can be used to speed 
up the matrix inversions. If runtime is crucial, then you could increase the 
number of nodes instead of dividing resources.

.. code-block:: bash

    #!/bin/bash
    #SBATCH --job-name=grogupy
    #SBATCH --nodes=1               —>  1       ->  2
    #SBATCH --ntasks=128            ->  64      ->  128
    #SBATCH --ntasks-per-node=128   —>  64      —>  128
    #SBATCH --cpus-per-task=1       ->  2       ->  1
    #SBATCH --mem-per-cpu 2000      ->  4000    ->  4000

The second possibility is to set the **maximum number of pairs per loop**. 
This breaks up the list of pairs into smaller, more manageable chunks and 
solves the system for these chunks. However this also means that the 
integration over the Brillouion zone and the energy contour has to be repeated 
for every chunk. **The overhead of this method is much larger than the first 
one.**

.. code-block:: python

   max_pairs_per_loop = 100

A more conservative parallelization in the grogupy code is to do the matrix 
inversions for the Green's function in a for loop. This can be set by the 
Green's function solver parameter. If the number of energy points is large, 
which is true in case of metals, then it is worth to tweak this parallelization 
even more by setting the maximum number of Green's function in a batch.

.. code-block:: python

   greens_function_solver = "Sequential"
   max_g_per_loop = 100


Overflow in GPU memory
----------------------

If the error message comes from CUDA, then the problem is the GPU memory, 
which is usually just a fraction of RAM. grogupy should not store anything in 
GPU memory that is not neccecary so the only possible problem is the too 
aggressive parallelization over the Green's functions. To change this we can 
use the same parameters as before.

.. code-block:: python

   greens_function_solver = "Sequential"
   max_g_per_loop = 100
