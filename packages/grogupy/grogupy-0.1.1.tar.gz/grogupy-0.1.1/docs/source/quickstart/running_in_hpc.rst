.. _running_in_hpc:

Running grogupy in HPC
======================
This section provides instructions on how to configure and run grogupy on a 
High-Performance Computing (HPC) system using SLURM. Below is an example of a 
bash script for submitting a job to the SLURM scheduler.

Example SLURM batch script
---------------------------

The following is an example SLURM batch script (`sbatch`) for running grogupy 
on an HPC system, in this case on `Komondor 
<https://hpc.kifu.hu/hu/komondor.html>`_:

.. code-block:: bash

    #!/bin/bash
    #SBATCH --job-name=grogupy
    #SBATCH --nodes=1
    #SBATCH --ntasks=1
    #SBATCH --ntasks-per-node=1
    #SBATCH --cpus-per-task=128
    #SBATCH --time=01:00:00
    #SBATCH --gres=gpu:8
    #SBATCH --partition=ai
    #SBATCH --exclusive
    #SBATCH --mem-per-cpu 4000

    ulimit -s unlimited

    source ~/.bashrc
    yes | module clear
    module purge
    module load PrgEnv-gnu cray-pals cray-python cuda/12.3

    export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
    export OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK
    export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK
    export VECLIB_MAXIMUM_THREADS=$SLURM_CPUS_PER_TASK
    export NUMEXPR_NUM_THREADS=$SLURM_CPUS_PER_TASK

    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/software/packages/cuda/12.3/targets/x86_64-linux/lib
    export grogupy_ARCHITECTURE=GPU

    time srun grogupy_run ./grogupy_input.py

Explanation of the script
-------------------------

- `#SBATCH --job-name=grogupy`: Sets the name of the job.
- `#SBATCH --nodes=1`: Requests one node.
- `#SBATCH --ntasks=1`: Requests one task.
- `#SBATCH --ntasks-per-node=1`: Specifies one task per node.
- `#SBATCH --cpus-per-task=128`: Allocates 128 CPUs per task.
- `#SBATCH --time=01:00:00`: Sets a time limit of 1 hours for the job.
- `#SBATCH --gres=gpu:8`: Requests 8 GPUs.
- `#SBATCH --partition=ai`: Specifies the partition to submit the job to.
- `#SBATCH --exclusive`: Ensures exclusive access to the node.
- `#SBATCH --mem-per-cpu 4000`: Allocates 4000 MB of memory per CPU.

The script also sets up the environment by loading necessary
modules and setting environment variables for optimal
performance. Exportin the LD_LIBRARY_PATH variable is necessary
to ensure that the CUDA library is accessible for cupy. The
script also sets the `grogupy_ARCHITECTURE` environment
variable to `GPU` to enable GPU acceleration in grogupy.
Finally, it runs the grogupy application using `srun` and the
`grogupy` command line script.

Make sure to adjust the script parameters according to
your HPC system's configuration and your specific requirements.


Example input file format
-------------------------

For the corresponding input file for the above script, `grogupy_input.py`,
which contains the parameters for the grogupy simulation see the 
:ref:`Input/Output formats <io_formats>` tutorial.