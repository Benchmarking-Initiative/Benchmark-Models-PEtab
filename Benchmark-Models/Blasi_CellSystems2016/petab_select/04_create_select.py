from model_info import (
    acetylation_reactions,
    get_parameter_id,
)
import shutil
import pandas as pd


import petab_select
from petab_select.constants import (
    MODEL_SUBSPACE_ID,
    PETAB_YAML,
    ESTIMATE,
    PARAMETER_VALUE_DELIMITER,
)


parameter_ids = [get_parameter_id(*reaction) for reaction in acetylation_reactions]

# The value to "turn off" the parameter. Since it's a multiplier, `1` is the identity.
default_motif_value = '1.0'

model_subspace = {
    MODEL_SUBSPACE_ID: 'M',
    PETAB_YAML: '../petab/petab_problem.yaml',
    **{
        parameter_id: PARAMETER_VALUE_DELIMITER.join([default_motif_value, ESTIMATE])
        for parameter_id in parameter_ids
    }
}

df = petab_select.get_model_space_df(pd.DataFrame([model_subspace]))

petab_select.write_model_space_df(df, filename='output/select/model_space.tsv')
shutil.copy('input/petab_select_problem.yaml', 'output/select/petab_select_problem.yaml')
