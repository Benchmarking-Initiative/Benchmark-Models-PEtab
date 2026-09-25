The paper describes a model selection problem with four hypotheses. Each hypothesis involves adding a set of parameters to the model -- these sets of parameters are annotated in the `model_selection_group` column of the parameters table. The paper shows a result where the model with the first hypothesis alone (H1) was accepted as the best by AIC.

This benchmark problem is the parameter estimation problem for the H1-only model. The parameters for the other hypotheses are specified in `parameters_Isensee_JCB2018_model_selection.tsv`. For example, this Python code will create the PEtab problem for the H2+H3 model.
```python
import pandas as pd
import petab

petab_problem = petab.Problem.from_yaml("Isensee_JCB2018.yaml")
model_selection_parameter_df = petab.get_parameter_df("parameters_Isensee_JCB2018_model_selection.tsv")

petab_problem.parameter_df = petab.get_parameter_df(pd.concat([
    # Remove the H1 parameters
    petab_problem.parameter_df.query("model_selection_group != 'H1: different KD'"),
    # Add the H2 and H3 parameters
    model_selection_parameter_df.query("model_selection_group in ['H2: AC inhibition', 'H3: incomplete import']")
]))
```
