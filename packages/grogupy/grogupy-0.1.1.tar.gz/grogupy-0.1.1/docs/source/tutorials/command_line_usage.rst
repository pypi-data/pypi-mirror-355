.. _command_line_usage:

Command line usage
==================
grogupy currently have three command line tools. The first can run simulations 
based on an input file. 

.. code-block:: console

   grogupy_run input.py
   grogupy_run input.fdf

Furthere information on the input file format is available :ref:`here 
<io_formats>`. The second one can create a summary and figures from the *.pkl* 
output format, which will be stored in a *.html* file. All the important 
physical information is aggregated here and you can do interactive system 
exploration with plotly figures.

.. code-block:: console

   grogupy_analyze out.pkl

The third and final script can help you determine the result of convergence 
tests. It flattens the exchange and anysotropy tensors over all pairs and 
magnetic entities and compares them with different convergence parameters. The 
output is also a *.html* file which contains an interactive plotly figure.

.. code-block:: console

   grogupy_convergence --type kset --files "CrI3_kset_50_50_1_eset_100_Fit.pkl CrI3_kset_100_100_1_eset_100_Fit.pkl"
