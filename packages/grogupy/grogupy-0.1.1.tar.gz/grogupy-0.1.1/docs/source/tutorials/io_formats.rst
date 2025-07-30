.. _io_formats:

Input/Output formats
====================

Input formats
-------------

The **grogupy_run** command line tool accepts input in the  *.py* and *.fdf* 
format. See and compare the following examples.

.. tabs:: Input formats

    .. tab:: Python

        .. code-block:: python

            ###############################################################################
            #                                 Input files
            ###############################################################################


            infolder = "./benchmarks/CrI3"
            infile = "CrI3.fdf"


            ###############################################################################
            #                            Convergence parameters
            ###############################################################################


            # kset should be at leas 100x100 for 2D diatomic systems
            kset = [100, 100, 1]
            # eset should be 100 for insulators and 1000 for metals
            eset = 100
            # esetp should be 600 for insulators and 10000 for metals
            esetp = 10000
            # emin None sets the minimum energy to the minimum energy in the eigfile
            emin = None
            # emax is at the Fermi level at 0
            emax = 0
            # the bottom of the energy contour should be shifted by -5 eV
            emin_shift = -5
            # the top of the energy contour can be shifted to the middle of the gap for
            # insulators
            emax_shift = 0


            ###############################################################################
            #                                 Orientations
            ###############################################################################


            # usually the DFT calculation axis is [0, 0, 1]
            scf_xcf_orientation = [0, 0, 1]
            # the reference directions for the energy derivations
            ref_xcf_orientations = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


            ###############################################################################
            #                      Magnetic entity and pair definitions
            ###############################################################################


            # magnetic entities and pairs can be defined automatically from the cutoff
            # radius and magnetic atoms
            setup_from_range = True
            radius = 20
            atomic_subset = "Cr"
            kwargs_for_mag_ent = dict(l=2)


            ###############################################################################
            #                                Memory management
            ###############################################################################


            # maximum number of pairs per loop, reduce it to avoid memory overflow
            max_pairs_per_loop = 10000
            # in low memory mode we discard some temporary data that could be useful for
            # interactive work
            low_memory_mode = True
            # sequential solver is better for large systems
            greens_function_solver = "Parallel"
            # maximum number of greens function samples per loop, when 
            # greens_function_solver is set to "Sequential", reduce it to avoid memory 
            # overflow on GPU for large systems
            max_g_per_loop = 20


            ###############################################################################
            #                                 Solution methods
            ###############################################################################


            # the spin model solvers solvers can be turned off, in this case only the 
            # energies upon rotations are meaningful
            apply_spin_model = True
            # the calculation of J and K from the energy derivations, either 
            # "generalised-fit", "generalised-grogu" or "isotropic-only"
            spin_model = "generalised-grogu"
            # parallelization should be turned on for efficiency
            parallel_mode = "K"


            ###############################################################################
            #                                   Output files
            ###############################################################################


            # either total or local, which controls if only the magnetic
            # entity's magnetic monent or the whole atom's magnetic moment is printed
            # used by all output modes
            out_magnetic_moment = "Total"

            # save the magnopy file
            save_magnopy = True
            # precision of numerical values in the magnopy file
            magnopy_precision = None
            # add the simulation parameters to the magnopy file as comments
            magnopy_comments = True

            # save the Uppsala Atomistic Spin Dynamics software input files
            # uses the outfolder and out_magentic_moment
            save_UppASD = True
            # add the simulation parameters to the cell.tmp.txt file as 
            # comments
            uppasd_comments = True

            # save the pickle file
            save_pickle = True
            """
            The compression level can be set to 0,1,2. Every other value defaults to 2.
            0. This means that there is no compression at all.

            1. This means, that the keys "_dh" and "_ds" are set
            to None, because othervise the loading would be dependent
            on the sisl version

            2. This contains compression 1, but sets the keys "Gii",
            "Gij", "Gji", "Vu1" and "Vu2" to [], to save space
            """
            pickle_compress_level = 2

            # output folder, for example the current folder
            outfolder = "./src/grogupy/cli/tests/"
            # outfile name
            outfile = "test"


            ###############################################################################
            ###############################################################################

    .. tab:: fdf

        .. code-block::

            ###############################################################################
            #                                 Input files
            ###############################################################################


            InFolder        ./benchmarks/CrI3
            Infile          CrI3.fdf


            ###############################################################################
            #                            Convergence parameters
            ###############################################################################


            # kset should be at leas 100x100 for 2D diatomic systems
            Kset        100 100 1
            # eset should be 100 for insulators and 1000 for metals
            Eset        100
            # esetp should be 600 for insulators and 10000 for metals
            Esetp       10000
            # emin None sets the minimum energy to the minimum energy in the eigfile
            Emin        None
            # emax is at the Fermi level at 0
            Emax        0
            # the bottom of the energy contour should be shifted by -5 eV
            EminShift   -5
            # the top of the energy contour can be shifted to the middle of the gap for 
            # insulators
            EmaxShift   0

            
            ###############################################################################
            #                                 Orientations
            ###############################################################################


            # usually the DFT calculation axis is [0, 0, 1]
            ScfXcfOrientation   0   0   1
            # the reference directions for the energy derivations
            %block RefXcfOrientations
                1   0   0
                0   1   0
                0   0   1
            %endblock RefXcfOrientations

            
            ###############################################################################
            #                      Magnetic entity and pair definitions
            ###############################################################################


            # magnetic entities and pairs can be defined automatically from the cutoff
            SetupFromRange          True
            Radius                  20                      # radius and magnetic atoms
            AtomicSubset            Cr
            %block KwargsForMagEnt
                l                   2
            %endblock KwargsForMagEnt


            ###############################################################################
            #                                Memory management
            ###############################################################################


            # maximum number of pairs per loop, reduce it to avoid memory overflow
            MaxPairsPerLoop         10000
            # in low memory mode we discard some temporary data that could be useful for 
            # interactive work
            low_memory_mode         True
            # sequential solver is better for large systems
            GreensFunctionSolver    Parallel
            # maximum number of greens function samples per loop, when 
            greens_function_solver is set to "Sequential", reduce it to avoid memory 
            # overflow on GPU for large systems
            MaxGPerLoop             20


            ###############################################################################
            #                                 Solution methods
            ###############################################################################


            # the spin model solvers solvers can be turned off, in this case only the 
            # energies upon rotations are meaningful
            ApplySpinModel  True
            # the calculation of J and K from the energy derivations, either 
            # "generalised-fit", "generalised-grogu" or "isotropic-only"
            SpinModel       generalised-grogu
            # parallelization should be turned on for efficiency
            ParallelMode = "K"


            ###############################################################################
            #                                   Output files
            ###############################################################################


            # either total or local, which controls if only the magnetic
            # entity's magnetic monent or the whole atom's magnetic moment is printed
            # used by all output modes
            OutMagneticMoment           Total

            # save the magnopy file
            SaveMagnopy                 True
            # precision of numerical values in the magnopy file
            MagnopyPrecision            None
            # add the simulation parameters to the magnopy file as comments
            MagnopyComments             True
            
            # save the Uppsala Atomistic Spin Dynamics software input files
            SaveUppASD                  True
            # add the simulation parameters to the cell.tmp.txt file as 
            # comments
            UppASDComments = True

            
            # save the pickle file
            SavePickle                  True
            # The compression level can be set to 0,1,2. Every other value defaults to 2.
            # 0. This means that there is no compression at all.
            # 
            # 1. This means, that the keys "_dh" and "_ds" are set
            #    to None, because othervise the loading would be dependent
            #    on the sisl version
            # 
            # 2. This contains compression 1, but sets the keys "Gii",
            #    "Gij", "Gji", "Vu1" and "Vu2" to [], to save space
            PickleCompressLevel         2

            # output folder, for example the input folder
            OutFolder                   ./src/grogupy/cli/tests/
            # outfile name, default name
            OutFile                     test


            ###############################################################################
            ###############################################################################


Input parameters
----------------

The above examples contained a generally acceptable setup for a simulation, 
but in this section you can find all the recognised input parameters by 
**grogupy_run**. The parameter names are case insensitive and for better 
readability and formatting the underlines and dots are stripped. Furthermore 
most of the parameters have  some sensible default values for ease of use.

infolder, *by default ./*
    The base folder of the DFT calculation.

infile
    The configuration file of the DFT calculation that can be read by sisl, 
    for example *.fdf* in case if Siesta. It has no default value.

kset
    The number of k points for the Brillouin-zone integration. The meshgrid is 
    created by a Monkhorst-Pack like sample generation. For 2D diatomic systems 
    it should be in the order of (100, 100, 1), but convergence tests should be 
    made. It is desirable to keep this as low as possible to reduce 
    computational time and resources.

eset, *by default 1000*
    The number of energy points for the Green's function sampling. For 
    insulators it should be in the order of 100 if the Fermi level is choosen 
    carefully and for metals it should be in the order of 1000 for convergence, 
    but convergence tests should be made. It is desirable to keep this as low 
    as possible to reduce computational time and resources.

esetp, *by default 10000*
    This parameter changes the distribution of sample points along the energy 
    contour. For insulators this should be around 100, but for metals to 
    accurately evaluate the integral near the Fermi level, we need a dense 
    sampling so it should be set to 10000, which puts most of the samples near 
    the Fermi level.

emin, *by default None*
    The bottom of the energy integration. Should be reasonably lower, than the 
    lowest energy level in the system, but **eminshift** also tweaks this 
    value. It is set up like this, because the default value (*None*) tries to 
    read the DFT files and find the enrgy minimum automatically.

eminshift, *by default -5 eV*
    It is added to the **emin** parameter.

emax, *by default 0 eV*
    The top of the energy integration. It is not set automatically, because in 
    case of metals it should be precisely at the Fermi level, **which is 
    always set to zero**. In case of insulators better convergence can be 
    achieved for the number of energy samples if the top of the contour avoids 
    the energy levels, so it should be set to the middle of the gap either by 
    this or by the **emaxshift** parameter.

emaxshift, *by default 0 eV*
    It is added to the **emax** parameter. When we try to set the top of the 
    contour to avoid the energy levels the shift is done in a way that the 
    bands are staying in the same position and Fermi level is shifted, so a 
    positive shift will put the top closer to the conduction band.

scfxcforientation, *by default [0, 0, 1]*
    The direction of the exchange field in the original DFT calculation. 
    Usually the system is set up in a way that the magnetic moments are 
    parallel to the Z direction.

refxcforientations, *by default [[1, 0, 0], [0, 1, 0], [0, 0, 1]]*
    The orientations of the reference directions, where we rotate the 
    exchange field and where we perturb the system. The perpendicular 
    directions are generated automatically. It is advised to choose these 
    directions in a way that they represent the symmetries of the system and 
    use the fitting methods for the calculation of the exchange and anisotropy 
    tensor. These orientations depend on the specific unit cell and atomic 
    postions so it is hard to determine them automatically. For special cases 
    the perpendicular directions can be defined as well, if the reference 
    directions is a list of dictionaries, with keys 'o', 'vw', where 'o' is 
    the reference direction and 'vw' is any number of perpendicular directions.

magneticentities
    Explicit magnetic entity definition for comlicated systems.

pairs
    Explicit pair definition for comlicated systems.

setupfromrange
    If False, then grogupy will try to read from the **magneticentities** and 
    **pairs** parameters, but if True, then it will try to automatically find 
    all the pairs in a given range. It only works if the magnetic entities are 
    atoms.

radius, *by default 20 Ang*
    The cutoff range for the **setupfromrange** parameter, othervise it is 
    ignored. It iterates over the magentic entities in the unit cell, then 
    finds the corresponding pairs for each of them in the given .
    radius.

atomicsubset
    Generally we have many kind of atoms in the system, and this parameter can 
    use sisl tags to choose the ones that are magnetic. For example in 
    Fe3GeTe2 it can be set to *Fe*.

kwargsformagent, *by default dict(l=None)*
    Even if the magnetic entity is confined to a single atom there are many 
    ways to tweak its definition. See the :ref:`setting magnetic entities 
    <setting_up_magnetic_entities>` tutorial. This parameter passes a 
    dictionary to each magnetic entity definition. Furthermore you can specify
    dictionaries for each magnetic entity, by using their tags as keys. Then the 
    corresponding values will be used for that specific magnetic entity.

maxpairsperloop, *by default 1000*
    Maximum number of pairs in a single simulation. This can be set to avoid 
    memory overflow in RAM. If the total number of pairs are larger than this 
    value, then the simulation will be split up into smaller batches, which 
    are ran sequentially.

maxgperloop, *by default 1*
    The maxmum number of parallel matrix inversions. It can be useful, when 
    there is a memory overflow in RAM or in GPU memory. It is only used when 
    **greensfunctionsolver** is "Sequential", otherwise grogupy uses full 
    parallelization of matrix inversions on all energy levels.

lowmemorymode, *by default False*
    Discards some temporary data that can be useful in interactive mode or for 
    some post processing. Reduces RAM usage so it is useful for memory bound 
    systems.
            
greensfunctionsolver, *by default Parallel*
    It can be parallel or sequential and determines the parallelization over 
    the energy levels for the matrix inversions. Useful of the system is memory 
    bound. If it is set to sequential, then **maxgperloop** is used to try some 
    less aggresive parallelization.

applyspinmodel, *by default True*
    The spin model solvers can be turned off, in this case only the 
    energies upon rotations are meaningful. This can be useful if we want to 
    apply some custom spin model in post processing, however it turns off many 
    functions in grogupy. For example some output options are not available, but 
    the **savepickle** is mandatory, because it contains the energies that we 
    need. 

spinmodel, *by default generalised-grogu*
    It describes the spin model used for the calculation of the physical 
    interaction parameters from the energies upon rotations. It can be 
    'generalised-fit', 'generalised-grogu' or 'isotropic-only'. 'generalised-grogu' 
    describes the method in the original paper, but can only be used for the x,y,z 
    reference directions, which is enforced. Fit can be used for any number of 
    reference directions, which can follow the symmetry of the system. 
    'isotropic-only' only calculates the isotropic exchange, which requires one 
    reference direction and one perpendicular direction, which  is also enforced 
    and it greatly reduces runtime.

    .. warning::
        The 'generalised-fit' method does not work for the anisotropy tensors yet.

parallelmode, *by default None*
    Parallelization can be turned on over the Brillouin-zone sampling by 
    setting parallelmode to "K". It should be turned on for efficiency.

outmagneticmoment, *by default total*
    It can be total or local and determines wether to use the total magnetic 
    moment from the atom or just magnetic moment of the selected shells or 
    orbitals. It is used for the Uppsala input file.

savemagnopy, *by default False*
    If True the magnopy input file is saved.

magnopyprecision, *by default None*
    It sets the numerical precision in the magnopy input file by rounding. 
    None means that there is no rounding at all.

magnopycomments, *by default True*
    If it is True, then the system and simulaton information is prepended in 
    the magnopy input file as comments.

saveuppasd, *by default False*
    If True the UppASD spin dynamics input file is saved.

uppasdcomments, *by default True*
    If it is True, then the system and simulaton information is prepended in 
    the UppASD *cell.tmp.txt* file as comments.

savepickle, *by default False*
    If True the Builder object is saved in the *.pkl* file as dictionary. The 
    choise to first convert the object to a dictionary was made so the data 
    can remain version and object definition independent.

picklecompresslevel, *by default 2*
    It determines the compression level in the *.pkl* output file, Of course 
    if **lowmemorymode** is used a large part of the data is already discarded. 
    Otherwise the compression level can be set to 0,1,2. Every other value 
    defaults to 2. 0 means that there is no compression at all. 1 means, that 
    the keys "_dh" and "_ds" are set to None, because othervise the loading of 
    the object would depend on the sisl version. And finally 2 contains 
    compression 1, but furthermore sets the keys "Gii", "Gij", "Gji", "Vu1" 
    and "Vu2" to [], to save space.

outfolder, *by default infolder*
    The output folder of all the requested output formats. If not specified 
    everything will be saved in the input folder.

outfile, *by default <infile>_kset_<kset>_eset_<eset>_<anisotropysolver>*
    The base name of the output files. The different output formats may 
    concatenate some information or filename extension to this. For example 
    the UppASD output format is a directory of multiple input files.
    

Output formats
--------------

For the specific output formats see the table below.

.. toctree::
   :maxdepth: 1
   
   magnopy_input.rst
   uppsala_input.rst
