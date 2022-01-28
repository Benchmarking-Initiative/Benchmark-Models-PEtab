#!/usr/bin/env python3
"""Print some stats for each benchmark problem"""

import os
from typing import Dict

import numpy as np
import pandas as pd
import petab


markdown_columns = {
    'conditions': 'Conditions',
    'estimated_parameters': 'Estimated Parameters',
    'events': 'Events',
    'preequilibration': 'Preequilibration',
    'postequilibration': 'Postequilibration',
    'measurements': 'Measurements',
    'name': 'Model ID',
    'observables': 'Observables',
    'species': 'Species',
}

index_column = 'name'


def check_events(petab_problem: petab.Problem) -> int:
    """Check for events in the model"""
    n_events = len(petab_problem.sbml_model.getListOfEvents())

    parameter_ids = [p.getId() for p in
                     petab_problem.sbml_model.getListOfParameters()]
    for p_id in parameter_ids:
        assignment_rule = petab_problem.sbml_model.getAssignmentRule(p_id)
        if assignment_rule and 'piecewise' in assignment_rule.getFormula():
            n_events += 1
    return n_events


def get_problem_info(
        problem: petab.Problem,
        problem_name: str = None
) -> Dict:
    """Get dictionary with stats for the given PEtab problem"""
    return {
        'conditions':
            problem.get_simulation_conditions_from_measurement_df().shape[0],
        'estimated_parameters':
            np.sum(problem.parameter_df[petab.ESTIMATE]),
        'events':
            check_events(problem),
        'preequilibration':
            'No' if 'preequilibrationConditionId' not in
                    problem.measurement_df.columns or
                    all(pd.isnull(problem.measurement_df[
                              'preequilibrationConditionId'].values))
            else 'Yes',
        'postequilibration':
            'Yes' if np.inf in problem.measurement_df['time'].values else 'No',
        'measurements':
            len(problem.measurement_df.index),
        'name':
            problem_name,
        'observables':
            len(problem.measurement_df[petab.OBSERVABLE_ID].unique()),
        'species':
            len(problem.sbml_model.getListOfSpecies()),
    }


def get_overview_table(path: str = None) -> pd.DataFrame:
    """Get overview table with stats for all benchmark problems"""
    model_list = os.scandir(path=path)
    model_list = sorted(f.name for f in model_list if f.is_dir())
    dict_list = []

    for benchmark_model in model_list:
        yaml_file = f"{benchmark_model}/{benchmark_model}.yaml"
        problem = petab.Problem.from_yaml(yaml_file)
        d = get_problem_info(problem, benchmark_model)
        dict_list.append(d)

    df = pd.DataFrame(dict_list)
    df.set_index([index_column], inplace=True)
    return df


def main(
    markdown: bool = False,
):
    df = get_overview_table()

    pd.options.display.width = 0

    if markdown:
        df.index.rename(markdown_columns[index_column], inplace=True)
        df.rename(columns=markdown_columns, inplace=True)
        print(df.to_markdown())
    else:
        print(df)


if __name__ == '__main__':
    import sys
    markdown = False
    if '--markdown' in sys.argv:
        markdown = True
    main(markdown)
