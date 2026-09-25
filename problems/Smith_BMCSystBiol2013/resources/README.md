# Implementation details of the Smith_BMCSystBiol2013 benchmark problem

## Description
This benchmark problem was implemented using information from the original publication [[1]], 
the respective supplementary material as well as the accompanying github repository [[2]]. All
processing that was necessary to obtain the benchmark problem was performed using the `generate_petab.py`
script contained in this folder, which provides a detailed description of all processing steps.

## Shortcomings
The resulting PEtab implementation does not capture all steps of the original work, for example 
tuning of parameters to obtain stable cycles under certain physiological conditions was omitted 
as this cannot be faithfully represented in PEtab. However, essential features of the model and 
training data are captured, so it is fair to claim this actually recapitulates a biological problem.

## Validation
The implementation was validated by comparing the results to original simulation results using the
test problem provided in the folder `sim_test`, which uses simulation files provided in the GitHub
directory [[2]] as "measurements". Results were validated using AMICI, which yielded overall 
satisfactory agreement (rtol=1e-1/1e-2, atol=1e-3). Only notable differences are in simulations for 
figure 2H, in species related to SOD2/InR transcription. It looks like transcription rates are off 
by a factor 0.8 and 0.4 resepectively (can be tested by setting `ATTEMPT_FIX_FIGURE_2H` to `True` 
in `generate_petab.py`) and translation/degradation rate is off by a factor 0.9 for InR. 
The source of these discrepancies is unclear and are likely due to undocumented changes to the model
(some of the other parameters reported in the simulation files also vary, but transcription/translation
specific rates are not reported as they are implemented as local parameters. So this information is lost.).
However, the impact on remainder of model seems negligible.

[1]: https://doi.org/10.1186/1752-0509-7-41
[2]: https://github.com/graham1034/Smith2012_insulin_signalling