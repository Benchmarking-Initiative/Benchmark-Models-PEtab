# Install

There are various ways of installing or downloading the benchmark models:

## Git clone

The repository containing the benchmark models can be cloned from GitHub via:

    git clone git@github.com:Benchmarking-Initiative/Benchmark-Models-PEtab.git

## Download source files

The Benchmark files can be downloaded from GitHub as a
[ZIP file](https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab/archive/refs/heads/master.zip).

## Python package

We provide a Python utility package that simplifies the installation and
provides access functionality at [src/python](src/python).

It can be installed directly from GitHub via:

    pip install git+https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab.git@master#subdirectory=src/python

Alternatively, when the whole repository has been cloned (see above),
the python package can be installed via

    cd src/python

followed by either an in-place develop mode installation:

    pip install -e .

or a packaged installation:

    ./build.sh
    pip install build/dist/*

Note that when the repository models are updated, also the python package needs
to be updated, as it does not actively synchronize.

Once installed, the python package can be used via:

    import benchmark_models_petab as models
    
    # print models base folder
    print(models.MODELS_DIR)
    # print all model names
    print(models.MODELS)
    # generate petab problem
    petab_problem = models.get_problem('Zheng_PNAS2012')
    
For provided functionality, see the
[source code documentation](src/python/benchmark_models_petab).
