# Model selection problem for `Blasi_CellSystems2016`
This is a fresh implementation of the model from `Blasi_CellSystems2016`, to faciliate model selection with PEtab and PEtab Select. The implementation can be found in the `output/` directory.

Specifically, this model contains parameters to enable model selection with motif-specific acetylation rates. These additional parameters are implemented as multipliers of the basal acetylation rate `a_b`.
Note that this means any motif-specific parameter `a_*` (except the basal acetylation rate `a_b`) can be fixed to 1 to "turn off" the motif-specific acetylation rate, or estimated to "turn on" the motif-specific acetylation rate.

The nominal values in the parameter table (`output/petab/parameters.tsv`) are taken from the original MATLAB implementation and match the values reported in the supplementary of the original paper. However, they have been divided by the nominal value for `a_b`, because the motif-specific parameters are multipliers in this implementation.

The only thing taken from the main PEtab problem are the measurements, the remaining PEtab (Select) files and the model were generated with the provided scripts.

# Python requirements
The following should be sufficient to run the provided scripts. If using a system that doesn't support the bash `*.sh` script, then simply create the folders manually.
- a Python 3 virtual environment with PEtab Select (`pip install petab-select`) installed.
