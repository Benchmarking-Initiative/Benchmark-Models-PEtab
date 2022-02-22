import pandas as pd
import petab
import shutil

from petab import (
    CONDITION_ID,
    OBSERVABLE_ID,
    MEASUREMENT,
    OBSERVABLE_NAME,
    OBSERVABLE_FORMULA,
    NOISE_FORMULA,
    OBSERVABLE_TRANSFORMATION,
    NOISE_DISTRIBUTION,
    LOG,
    LOG10,
    NORMAL,
    SIMULATION_CONDITION_ID,
    TIME,
    PARAMETER_ID,
    PARAMETER_NAME,
    LIN,
    PARAMETER_SCALE,
    LOWER_BOUND,
    UPPER_BOUND,
    NOMINAL_VALUE,
    ESTIMATE,
)


from model_info import (
    get_ac_state,
    get_motif,
    get_species_id,
    lysines,
    motif_specific_parameters,
    # switch_parameters,
    common_parameters,
)


petab_problem0 = petab.Problem.from_yaml('../Blasi_CellSystems2016.yaml')
measurements0 = dict(zip(petab_problem0.measurement_df[OBSERVABLE_ID], petab_problem0.measurement_df[MEASUREMENT]))

condition_id = 'condition'
noise = 'sigma'


def convert_observable_id(id0: str) -> str:
    motif0 = id0[len('observable_'):]
    if motif0 == '0ac':
        ac_state = tuple()
    elif motif0 == '4ac':
        ac_state = get_ac_state(lysines)
    else:
        ac_state = get_ac_state([f'k{i:0>2}' for i in motif0.split('k') if i])
    species_id = get_species_id(ac_state)
    observable_id = 'observable_' + species_id
    observable_dict = {
        OBSERVABLE_ID: 'observable_' + species_id,
        OBSERVABLE_NAME: 'y_{' + get_motif(ac_state) + '}',
        OBSERVABLE_FORMULA: species_id,
        OBSERVABLE_TRANSFORMATION: LOG,
        NOISE_FORMULA: noise,
        NOISE_DISTRIBUTION: NORMAL,
    }
    return observable_dict


# Create observables
observable_dicts = []
observable_id_mapping = {}
observable_ids0 = set(measurements0)
for observable_id0 in observable_ids0:
    observable_dict = convert_observable_id(observable_id0)
    observable_id_mapping[observable_id0] = observable_dict[OBSERVABLE_ID]
    observable_dicts.append(observable_dict)

# Create measurements
measurement_dicts = []
for observable_id0, value0 in measurements0.items():
    observable_id = observable_id_mapping[observable_id0]
    measurement_dict = {
        OBSERVABLE_ID: observable_id,
        SIMULATION_CONDITION_ID: condition_id,
        TIME: 'inf',
        MEASUREMENT: value0,
    }
    measurement_dicts.append(measurement_dict)

# Create parameters
parameter_dicts = []
## Motif-specific
for parameter_dict0 in motif_specific_parameters.values():
    parameter_dict = {
        PARAMETER_ID: parameter_dict0['id'],
        PARAMETER_NAME: parameter_dict0['name'],
        PARAMETER_SCALE: LOG10,
        LOWER_BOUND: '1e-12',
        UPPER_BOUND: '1e3',
        NOMINAL_VALUE: 1,
        ESTIMATE: 0,
    }
    parameter_dicts.append(parameter_dict)
# ## Switch
# for parameter_dict0 in switch_parameters.values():
#     parameter_dict = {
#         PARAMETER_ID: parameter_dict0['id'],
#         PARAMETER_NAME: parameter_dict0['name'],
#         PARAMETER_SCALE: LIN,
#         NOMINAL_VALUE: 0,
#         ESTIMATE: 0,
#     }
#     parameter_dicts.append(parameter_dict)
## Basal
for parameter_dict0 in common_parameters.values():
    if parameter_dict0['id'] == 'a_b':
        parameter_dict = {
            PARAMETER_ID: parameter_dict0['id'],
            PARAMETER_NAME: parameter_dict0['name'],
            PARAMETER_SCALE: LOG10,
            LOWER_BOUND: '1e-12',
            UPPER_BOUND: '1e3',
            NOMINAL_VALUE: 0,
            ESTIMATE: 1,
        }
    elif parameter_dict0['id'] == 'da_b':
        parameter_dict = {
            PARAMETER_ID: parameter_dict0['id'],
            PARAMETER_NAME: parameter_dict0['name'],
            PARAMETER_SCALE: LIN,
            NOMINAL_VALUE: 1,
            ESTIMATE: 0,
        }
    else:
        raise NotImplementedError(parameter_dict0['id'])
    parameter_dicts.append(parameter_dict)
## Noise
parameter_dicts.append(
    {
        PARAMETER_ID: noise,
        PARAMETER_NAME: noise,
        PARAMETER_SCALE: LOG10,
        LOWER_BOUND: '1e-12',
        UPPER_BOUND: '1e3',
        NOMINAL_VALUE: 0.1,
        ESTIMATE: 1,
    }
)

condition_df = petab.get_condition_df(pd.DataFrame({CONDITION_ID:[condition_id]}))
observable_df = petab.get_observable_df(pd.DataFrame(observable_dicts))
measurement_df = petab.get_measurement_df(pd.DataFrame(measurement_dicts))
parameter_df = petab.get_parameter_df(pd.DataFrame(parameter_dicts))

petab.write_condition_df(condition_df,     'output/petab/conditions.tsv')
petab.write_observable_df(observable_df,   'output/petab/observables.tsv')
petab.write_measurement_df(measurement_df, 'output/petab/measurements.tsv')
petab.write_parameter_df(parameter_df,     'output/petab/parameters.tsv')
shutil.copy('input/petab_problem.yaml',    'output/petab/petab_problem.yaml')
