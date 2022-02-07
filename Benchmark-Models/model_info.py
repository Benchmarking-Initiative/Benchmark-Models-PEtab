#!/usr/bin/env python3
"""Print some stats for each benchmark problem"""

import os
from typing import Dict, List

import libsbml
import numpy as np
import pandas as pd
import petab

markdown_columns = {
    'conditions': 'Conditions',
    'estimated_parameters': 'Estimated Parameters',
    'events': 'Events',
    'measurements': 'Measurements',
    'name': 'Model ID',
    'observables': 'Observables',
    'species': 'Species',
    'described_by': 'References',
}

index_column = 'name'


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
            len(problem.sbml_model.getListOfEvents()),
        'measurements':
            len(problem.measurement_df.index),
        'name':
            problem_name,
        'observables':
            len(problem.measurement_df[petab.OBSERVABLE_ID].unique()),
        'species':
            len(problem.sbml_model.getListOfSpecies()),
        'described_by':
            get_described_by(problem.sbml_model),
    }


def get_described_by(sbml_model: libsbml.Model) -> List[str]:
    """Get publication URIs from SBML is-described-by annotatation"""
    cv_terms = sbml_model.getCVTerms()
    reference_uris = []
    for anno in cv_terms:
        if anno.getBiologicalQualifierType() != libsbml.BQB_IS_DESCRIBED_BY:
            continue
        resources = anno.getResources()
        for i in range(resources.getNumAttributes()):
            uri = resources.getValue(i)
            reference_uris.append(uri)
    return reference_uris


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
        # directory as markdown link
        df.rename(index=lambda x: f"[{x}](Benchmark-Models/{x}/)",
                  inplace=True)
        # references to markdown links
        df['described_by'] = df['described_by'].apply(
            lambda x: " ".join([f"[\\[{i + 1}\\]]({uri})"
                               for i, uri in enumerate(x)])
        )
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
