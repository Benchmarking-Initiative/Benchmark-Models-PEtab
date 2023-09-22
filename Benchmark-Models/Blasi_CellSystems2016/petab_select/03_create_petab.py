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
    TIME_STEADY_STATE,
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
measurements0_grouped = {k: v for k, v in petab_problem0.measurement_df.groupby(OBSERVABLE_ID)}

condition_id = 'condition'
noise = 'sigma_'


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
observable_ids0 = sorted(set(measurements0_grouped))
for observable_id0 in observable_ids0:
    observable_dict = convert_observable_id(observable_id0)
    observable_id_mapping[observable_dict[OBSERVABLE_ID]] = observable_id0
    observable_dicts.append(observable_dict)

# Create measurements
measurement_dicts = []
for observable_id in sorted(observable_id_mapping):
    measurements0 = measurements0_grouped[observable_id_mapping[observable_id]]
    for _, row0 in measurements0.iterrows():
        measurement_dict = {
            OBSERVABLE_ID: observable_id,
            SIMULATION_CONDITION_ID: condition_id,
            TIME: TIME_STEADY_STATE,
            MEASUREMENT: row0.measurement,
        }
        measurement_dicts.append(measurement_dict)

# Create parameters
## Optimal parameters, reported in paper, taken from MATLAB implementation
published_optimal_parameters = {
    'a_b': 0.0667579590703576,
    'a_0ac_k08': 0.0272712553008379,
    'a_k05_k05k12': 2.06203333647699,
    'a_k12_k05k12': 0.551940805482671,
    'a_k16_k12k16': 0.695938574109670,
    'a_k05k12_k05k08k12': 0.325297000106462,
    'a_k12k16_k08k12k16': 2.20553079904637,
    'a_k08k12k16_4ac': 3.59169549625268,
}

parameter_dicts = []
## Motif-specific
for parameter_dict0 in motif_specific_parameters.values():
    parameter_dict = {
        PARAMETER_ID: parameter_dict0['id'],
        PARAMETER_NAME: parameter_dict0['name'],
        PARAMETER_SCALE: LOG10,
        LOWER_BOUND: '1e-3',
        UPPER_BOUND: '1e3',
        NOMINAL_VALUE: (
            published_optimal_parameters[parameter_dict0['id']] / published_optimal_parameters['a_b']
            if parameter_dict0['id'] in published_optimal_parameters
            else 1
        ),
        ESTIMATE: (
            1
            if parameter_dict0['id'] in published_optimal_parameters
            else 0
        ),
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
            LOWER_BOUND: '1e-3',
            UPPER_BOUND: '1e3',
            NOMINAL_VALUE: published_optimal_parameters['a_b'],
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
        LOWER_BOUND: '1e-3',
        UPPER_BOUND: '1e3',
        NOMINAL_VALUE: 1,
        ESTIMATE: 0,
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
