#!/usr/bin/env python3
"""Print some stats for each benchmark PEtab problem"""

import os
from typing import Dict, List

import libsbml
import numpy as np
import pandas as pd
import petab

from _helpers import petab_yamls


markdown_columns = {
    'conditions': 'Conditions',
    'estimated_parameters': 'Estimated Parameters',
    'events': 'Events',
    'preequilibration': 'Preequilibration',
    'postequilibration': 'Postequilibration',
    'measurements': 'Measurements',
    'petab_problem_id': 'PEtab Problem ID',
    'observables': 'Observables',
    'species': 'Species',
    'noise_distributions': 'Noise distribution(s)',
    'reference_uris': 'References',
}

index_column = 'petab_problem_id'


def get_summary(
        petab_problem: petab.Problem,
        petab_problem_id: str = None,
) -> Dict:
    """Get dictionary with stats for the given PEtab problem"""
    return {
        'petab_problem_id':
            petab_problem_id,
        'conditions':
            petab_problem.get_simulation_conditions_from_measurement_df().shape[0],
        'estimated_parameters':
            np.sum(petab_problem.parameter_df[petab.ESTIMATE]),
        'events':
            len(petab_problem.sbml_model.getListOfEvents()),
        'preequilibration':
            0 if petab.PREEQUILIBRATION_CONDITION_ID not in
            petab_problem.measurement_df.columns or
            pd.isnull(petab_problem.measurement_df[
                          petab.PREEQUILIBRATION_CONDITION_ID]).all()
            else (pd.isnull(petab_problem.measurement_df[
                  petab.PREEQUILIBRATION_CONDITION_ID].unique() == False
                 ).sum(),
        'postequilibration':
            petab.measurements.get_simulation_conditions(
                petab_problem.measurement_df[
                    petab_problem.measurement_df[petab.TIME] == np.inf]).shape[
                0] if
            np.isinf(petab_problem.measurement_df[petab.TIME]).any()
            else 0,
        'measurements':
            len(petab_problem.measurement_df.index),
        'observables':
            len(petab_problem.measurement_df[petab.OBSERVABLE_ID].unique()),
        'noise_distributions':
            get_noise_distributions(petab_problem.observable_df),
        'species':
            len(petab_problem.sbml_model.getListOfSpecies()),
        'reference_uris':
            get_reference_uris(petab_problem.sbml_model),
    }


def get_reference_uris(sbml_model: libsbml.Model) -> List[str]:
    """Get publication URIs from SBML is-described-by annotation"""
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


def get_noise_distributions(observable_df):
    if petab.NOISE_DISTRIBUTION in observable_df.columns:
        noise_distrs = ['normal' if dist is np.nan else dist for dist in
                        observable_df[petab.NOISE_DISTRIBUTION]]
        noise_distrs = set(noise_distrs)
    else:
        noise_distrs = {'normal'}
    return "; ".join(noise_distrs)


def get_overview_table() -> pd.DataFrame:
    """Get overview table with stats for all benchmark PEtab problems"""
    data = []
    for petab_problem_id, petab_yaml in petab_yamls.items():
        petab_problem = petab.Problem.from_yaml(petab_yaml)
        summary = get_summary(petab_problem, petab_problem_id)
        data.append(summary)
    df = pd.DataFrame(data)
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
        df['reference_uris'] = df['reference_uris'].apply(
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
