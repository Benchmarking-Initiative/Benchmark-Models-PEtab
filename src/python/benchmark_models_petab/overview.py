"""Print some stats for each benchmark PEtab problem"""

from pathlib import Path
from typing import Dict, List
import argparse

import libsbml
import numpy as np
import pandas as pd
import petab.v1 as petab
from petab.v1.yaml import load_yaml
from sbmlmath import sbml_math_to_sympy
from sbmlmath.csymbol import TimeSymbol
from . import MODELS, get_problem, get_problem_yaml_path, v1, v2
from .C import (
    GITHUB_DEFAULT_BRANCH,
    GITHUB_REPO,
    PROBLEMS_DIRNAME,
    V1_DIRNAME,
    V2_DIRNAME,
)
from .metadata import get_metadata
import sympy as sp
from sympy.core.relational import Relational

readme_md = Path(__file__).resolve().parent.parent / "README.md"

#: Column labels for the overview table.
columns = {
    "conditions": "Conditions",
    "estimated_parameters": "Estimated Parameters",
    "events": "Events",
    "preequilibration": "Preequilibration",
    "postequilibration": "Postequilibration",
    "measurements": "Measurements",
    "petab_problem_id": "ID",
    "observables": "Observables",
    "species": "Species",
    "noise_distributions": "Noise distribution(s)",
    "objective_prior_distributions": "Objective prior distribution(s)",
    "reference_uris": "References",
    "sbml4humans_urls": "SBML4Humans",
    "possible_discontinuities": "Possible Discontinuities",
}

#: Column descriptions for the overview table.
#:  Shown as HTML on the site, so they must not contain markup characters.
column_descriptions = {
    "petab_problem_id": (
        "Problem ID: first author, journal, and year of the publication."
    ),
    "conditions": (
        "Number of simulation conditions (combinations of preequilibration "
        "and simulation condition) in the measurement table."
    ),
    "estimated_parameters": "Number of estimated parameters.",
    "events": "Number of SBML events.",
    "preequilibration": "Number of distinct preequilibration conditions.",
    "postequilibration": (
        "Number of simulation conditions with steady-state measurements "
        "(time = inf)."
    ),
    "measurements": "Number of measurements (data points).",
    "observables": "Number of observables with measurements.",
    "species": "Number of species in the SBML model.",
    "noise_distributions": (
        "Noise distributions, including the observable transformation."
    ),
    "objective_prior_distributions": (
        "Prior distributions of estimated parameters that enter the "
        "objective function."
    ),
    "reference_uris": "Publications, from the SBML model annotation.",
    "sbml4humans_urls": "The SBML model rendered by SBML4Humans.",
    "possible_discontinuities": (
        "Heuristic: events with assignments, or discontinuous functions "
        "(piecewise, min, max, ...) with time-dependent arguments in the "
        "model."
    ),
}

index_column = "petab_problem_id"


def get_summary(
    petab_problem: petab.Problem,
    petab_problem_id: str = None,
) -> Dict:
    """Get dictionary with stats for the given PEtab problem"""
    print(petab_problem_id)
    return {
        "petab_problem_id": petab_problem_id,
        "conditions": petab_problem.get_simulation_conditions_from_measurement_df().shape[
            0
        ],
        "estimated_parameters": np.sum(
            petab_problem.parameter_df[petab.ESTIMATE]
        ),
        "events": len(petab_problem.sbml_model.getListOfEvents()),
        "possible_discontinuities": guess_discontinuities(petab_problem),
        "preequilibration": 0
        if petab.PREEQUILIBRATION_CONDITION_ID
        not in petab_problem.measurement_df.columns
        or pd.isnull(
            petab_problem.measurement_df[petab.PREEQUILIBRATION_CONDITION_ID]
        ).all()
        else (
            ~pd.isnull(
                petab_problem.measurement_df[
                    petab.PREEQUILIBRATION_CONDITION_ID
                ].unique()
            )
        ).sum(),
        "postequilibration": petab.measurements.get_simulation_conditions(
            petab_problem.measurement_df[
                petab_problem.measurement_df[petab.TIME] == np.inf
            ]
        ).shape[0]
        if np.isinf(petab_problem.measurement_df[petab.TIME]).any()
        else 0,
        "measurements": len(petab_problem.measurement_df.index),
        "observables": len(
            petab_problem.measurement_df[petab.OBSERVABLE_ID].unique()
        ),
        "noise_distributions": get_noise_distributions(
            petab_problem.observable_df
        ),
        "objective_prior_distributions": get_prior_distributions(
            petab_problem.parameter_df
        ),
        "species": len(petab_problem.sbml_model.getListOfSpecies()),
        "reference_uris": get_reference_uris(petab_problem.sbml_model),
        "sbml4humans_urls": get_sbml4humans_urls(petab_problem_id),
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


def get_sbml4humans_urls(petab_problem_id: str) -> List[str]:
    """Get URL to SBML4humans model"""
    yaml_file = get_problem_yaml_path(petab_problem_id)
    yaml_dict = load_yaml(yaml_file)
    model_filenames = [
        model_filename
        for problem_dict in yaml_dict[petab.PROBLEMS]
        for model_filename in problem_dict[petab.SBML_FILES]
    ]
    return make_sbml4humans_urls(petab_problem_id, V1_DIRNAME, model_filenames)


def make_sbml4humans_urls(
    petab_problem_id: str, version_dirname: str, model_filenames: list[str]
) -> list[str]:
    """Get SBML4humans URLs for the given model files of a problem.

    :param petab_problem_id: Problem ID.
    :param version_dirname: The encoding's directory (`v1`, `v2`).
    :param model_filenames: Model file paths relative to that directory.
    """
    repo_root = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_DEFAULT_BRANCH}"
    return [
        f"https://sbml4humans.de/report?url={repo_root}/{PROBLEMS_DIRNAME}"
        f"/{petab_problem_id}/{version_dirname}/{model_filename}"
        for model_filename in model_filenames
    ]


def get_noise_distributions(observable_df):
    if petab.NOISE_DISTRIBUTION in observable_df.columns:
        observable_df = observable_df.fillna(
            value={petab.NOISE_DISTRIBUTION: petab.NORMAL}
        )
        if petab.OBSERVABLE_TRANSFORMATION in observable_df.columns:
            observable_df = observable_df.fillna(
                value={petab.OBSERVABLE_TRANSFORMATION: petab.LIN}
            )
            noise_distrs = [
                tuple(e.values)
                for _, e in observable_df[
                    [petab.OBSERVABLE_TRANSFORMATION, petab.NOISE_DISTRIBUTION]
                ].iterrows()
            ]
        else:
            noise_distrs = [
                (petab.LIN, e) for e in observable_df[petab.NOISE_DISTRIBUTION]
            ]

    else:
        if petab.OBSERVABLE_TRANSFORMATION in observable_df.columns:
            observable_df = observable_df.fillna(
                value={petab.OBSERVABLE_TRANSFORMATION: petab.LIN}
            )
            noise_distrs = [
                (e, petab.NORMAL)
                for e in observable_df[petab.OBSERVABLE_TRANSFORMATION]
            ]
        else:
            noise_distrs = {(petab.LIN, petab.NORMAL)}

    noise_distrs = sorted(set(noise_distrs))
    noise_distrs = [
        "-".join(nd) if nd[0] != petab.LIN else nd[1] for nd in noise_distrs
    ]
    return "; ".join(noise_distrs)


def get_prior_distributions(parameter_df: pd.DataFrame) -> str:
    """Get the list of prior distributions entering the objective function."""
    df = parameter_df.loc[parameter_df[petab.ESTIMATE] == 1]
    if (
        petab.OBJECTIVE_PRIOR_TYPE not in df
        or df.get(petab.OBJECTIVE_PRIOR_TYPE).isna().all()
        or petab.OBJECTIVE_PRIOR_PARAMETERS not in df
        or df.get(petab.OBJECTIVE_PRIOR_PARAMETERS).isna().all()
    ):
        # nothing to do
        return ""
    unique = map(str, df[petab.OBJECTIVE_PRIOR_TYPE].fillna("").unique())
    return "; ".join(filter(None, unique))


def guess_discontinuities(petab_problem: petab.Problem) -> bool:
    """Guess whether the model has discontinuities.

    Potential discontinuities in the model state or its derivative:

    * SBML events with event assignments
    * SBML kinetic laws or rules with discontinuous math
      (piecewise, min, max, floor, ceiling, abs, logical operators, ...
      with time-dependent arguments)

    This is just an educated guess. The current list may be incomplete;
    not all piecewise functions are necessarily discontinuous; not all
    discontinuities might play a role in the simulation; the presence of
    discontinuities might be parameter-dependent; ... .
    """
    return sbml_model_has_discontinuities(petab_problem.sbml_model)


def sbml_model_has_discontinuities(model: libsbml.Model) -> bool:
    """Guess whether the SBML model has discontinuities.

    See :func:`guess_discontinuities`.
    """
    for event in model.getListOfEvents():
        for ea in event.getListOfEventAssignments():
            if ea.getMath():
                return True

    # convert reactions to rate rules
    sbml_doc = model.getSBMLDocument().clone()
    model = sbml_doc.getModel()
    conversion_config = libsbml.ConversionProperties()
    conversion_config.addOption("replaceReactions")
    sbml_doc.convert(conversion_config)
    conversion_config = libsbml.ConversionProperties()
    conversion_config.addOption("expandFunctionDefinitions")
    sbml_doc.convert(conversion_config)
    if model.getNumReactions() != 0 or model.getNumFunctionDefinitions() != 0:
        raise AssertionError(
            "Conversion to rate rules and function definitions failed"
        )

    # check whether any math contains discontinuous functions
    disc_math = (
        sp.Piecewise,
        sp.Min,
        sp.Max,
        sp.floor,
        sp.ceiling,
        sp.Abs,
        sp.factorial,
        sp.Mod,
        sp.And,
        sp.Or,
        sp.Xor,
        sp.Not,
        sp.Implies,
        Relational,
        sp.tan,
        sp.sec,
        sp.csc,
        sp.cot,
        sp.asec,
        sp.acsc,
        sp.acot,
        sp.asech,
        sp.acsch,
        sp.acoth,
    )

    def expr_maybe_time_dependent(expr: sp.Expr) -> bool:
        """Check if an expression might be time-dependent."""
        for free_symbol in expr.free_symbols:
            # explicitly time-dependent
            if free_symbol == TimeSymbol("t"):
                return True
            if (ele := model.getElementBySId(free_symbol.name)) and not (
                hasattr(ele, "getConstant") and ele.getConstant() is True
            ):
                # not explicitly constant – *might* be time-dependent
                return True
        return False

    # after the conversion, the only relevant entities are the rules
    for rule in model.getListOfRules():
        expr = sbml_math_to_sympy(rule)
        if not expr.has(*disc_math):
            continue
        # check whether the discontinuous function has time-dependent
        #  arguments; otherwise it's not a discontinuity
        for func in disc_math:
            for occurrence in expr.find(func):
                for arg in occurrence.args:
                    if expr_maybe_time_dependent(arg):
                        return True
    return False


def get_overview_df() -> pd.DataFrame:
    """Get overview table with stats for all benchmark PEtab problems"""
    data = []
    for petab_problem_id in v1.MODELS:
        petab_problem = get_problem(petab_problem_id)
        summary = get_summary(petab_problem, petab_problem_id)
        data.append(summary)
    df = pd.DataFrame(data)
    df.set_index([index_column], inplace=True)
    return df


start_overview_table = "\n<!-- START OVERVIEW TABLE -->\n"
end_overview_table = "\n<!-- END OVERVIEW TABLE -->\n"


def get_readme_table() -> str:
    """Get the version-independent overview table for the README.

    Lists each problem's short description, links to its PEtab v1 and
    v2 encodings, where available, and the DOI of its main publication.
    """
    rows = []
    for petab_problem_id in MODELS:
        problem_dir = f"{PROBLEMS_DIRNAME}/{petab_problem_id}"
        row = {"ID": f"[{petab_problem_id}]({problem_dir}/)"}
        for label, version, dirname in (
            ("PEtab v1", v1, V1_DIRNAME),
            ("PEtab v2", v2, V2_DIRNAME),
        ):
            row[label] = (
                f"[{dirname}]({problem_dir}/{dirname}/)"
                if petab_problem_id in version.MODELS
                else ""
            )
        metadata = get_metadata(petab_problem_id)
        doi = metadata.references[0].doi
        row["Reference"] = f"[{doi}](https://doi.org/{doi})"
        row["Description"] = metadata.short_description
        rows.append(row)
    return pd.DataFrame(rows).to_markdown(index=False)


def show_overview_table(
    markdown: bool = False,
    update_readme: bool = False,
):
    """Print the overview table or write the README table.

    :param markdown: Print the README table instead of the v1 statistics.
    :param update_readme: Write the README table to `README.md`.
    """
    if update_readme:
        with open(readme_md) as f:
            readme_content = f.read()
        before_table = readme_content.split(start_overview_table)[0]
        after_table = readme_content.split(end_overview_table)[1]
        new_readme_content = (
            before_table
            + start_overview_table
            + get_readme_table()
            + end_overview_table
            + after_table
        )
        with open(readme_md, "w") as f:
            f.write(new_readme_content)
    elif markdown:
        print(get_readme_table())
    else:
        pd.options.display.width = 0
        print(get_overview_df())


def main():
    parser = argparse.ArgumentParser(
        description="Show overview table for benchmark PEtab problems"
    )
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument(
        "--markdown",
        action="store_true",
        help="Print the README overview table (markdown)",
    )
    group1.add_argument(
        "--update",
        action="store_true",
        help="Update the README.md file with the overview table",
    )

    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument(
        "--html-file",
        help="Write the v1 and v2 overview tables to an HTML file",
    )

    args = parser.parse_args()

    if args.html_file:
        from ._site import create_overview_page

        create_overview_page(dest=Path(args.html_file))
    else:
        show_overview_table(markdown=args.markdown, update_readme=args.update)
