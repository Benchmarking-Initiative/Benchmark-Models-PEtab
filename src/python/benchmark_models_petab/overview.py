"""Print some stats for each benchmark PEtab problem"""

from pathlib import Path
from typing import Dict, List
import argparse

import libsbml
import numpy as np
import pandas as pd
import petab.v1 as petab
from petab.yaml import load_yaml
from sbmlmath import sbml_math_to_sympy
from sbmlmath.csymbol import TimeSymbol
from . import MODELS, get_problem, get_problem_yaml_path
import sympy as sp
from sympy.core.relational import Relational

REPO_URL = "https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab/"

readme_md = Path(__file__).resolve().parent.parent / "README.md"

markdown_columns = {
    "conditions": "Conditions",
    "estimated_parameters": "Estimated Parameters",
    "events": "Events",
    "preequilibration": "Preequilibration",
    "postequilibration": "Postequilibration",
    "measurements": "Measurements",
    "petab_problem_id": "PEtab Problem ID",
    "observables": "Observables",
    "species": "Species",
    "noise_distributions": "Noise distribution(s)",
    "objective_prior_distributions": "Objective prior distribution(s)",
    "reference_uris": "References",
    "sbml4humans_urls": "SBML4Humans",
    "possible_discontinuities": "Possible Discontinuities",
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
    repo_root = "https://raw.githubusercontent.com/Benchmarking-Initiative/Benchmark-Models-PEtab/master"
    urls = []
    for problem_dict in yaml_dict[petab.PROBLEMS]:
        for model_filename in problem_dict[petab.SBML_FILES]:
            gh_raw_url = f"{repo_root}/Benchmark-Models/{petab_problem_id}/{model_filename}"
            urls.append(f"https://sbml4humans.de/model_url?url={gh_raw_url}")
    return urls


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
    model: libsbml.Model = petab_problem.sbml_model

    for event in model.getListOfEvents():
        for ea in event.getListOfEventAssignments():
            if ea.getMath():
                return True

    # convert reactions to rate rules
    sbml_doc = petab_problem.sbml_model.getSBMLDocument().clone()
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
    for petab_problem_id in MODELS:
        petab_problem = get_problem(petab_problem_id)
        summary = get_summary(petab_problem, petab_problem_id)
        data.append(summary)
    df = pd.DataFrame(data)
    df.set_index([index_column], inplace=True)
    return df


start_overview_table = "\n<!-- START OVERVIEW TABLE -->\n"
end_overview_table = "\n<!-- END OVERVIEW TABLE -->\n"


def show_overview_table(
    markdown: bool = False,
    update_readme: bool = False,
):
    df = get_overview_df()
    pd.options.display.width = 0

    if markdown or update_readme:
        # directory as markdown link
        df.rename(
            index=lambda x: f"[{x}](Benchmark-Models/{x}/)", inplace=True
        )
        # references to markdown links
        for field in "reference_uris", "sbml4humans_urls":
            df[field] = df[field].apply(
                lambda x: " ".join(
                    [f"[\\[{i + 1}\\]]({uri})" for i, uri in enumerate(x)]
                )
            )
        df["possible_discontinuities"] = df["possible_discontinuities"].apply(
            lambda x: "✓" if x else ""
        )
        df.index.rename(markdown_columns[index_column], inplace=True)
        df.rename(columns=markdown_columns, inplace=True)
        markdown_overview = df.to_markdown()
        if update_readme:
            with open(readme_md, "r") as f:
                readme_content = f.read()
            before_table = readme_content.split(start_overview_table)[0]
            after_table = readme_content.split(end_overview_table)[1]
            new_readme_content = (
                before_table
                + start_overview_table
                + markdown_overview
                + end_overview_table
                + after_table
            )
            with open(readme_md, "w") as f:
                f.write(new_readme_content)
        else:
            print(markdown_overview)
    else:
        print(df)


def create_html_table(dest: Path) -> None:
    """Create HTML table with stats for all benchmark PEtab problems.

    :param dest: Path to the output HTML file.
    """
    from bokeh.io import output_file, save
    from bokeh.layouts import column
    from bokeh.models import (
        ColumnDataSource,
        DataTable,
        TableColumn,
        Div,
        StringFormatter,
        NumberFormatter,
        HTMLTemplateFormatter,
        InlineStyleSheet,
    )

    dest.parent.mkdir(parents=True, exist_ok=True)

    # get the overview dataframe and prettify it
    df = get_overview_df()
    df["possible_discontinuities"] = df["possible_discontinuities"].apply(
        lambda x: "✓" if x else ""
    )
    df.fillna({"objective_prior_distributions": ""}, inplace=True)

    def get_formatter(col: str):
        """Get the appropriate formatter for the column."""
        if col not in df.columns:
            # index column
            return HTMLTemplateFormatter(
                template=f"""
                <a href="{REPO_URL}tree/master/Benchmark-Models/<%= value %>"><%= value %></a>
                """
            )
        if pd.api.types.is_integer_dtype(df[col].dtype):
            return NumberFormatter(text_align="right")
        if col in ("reference_uris", "sbml4humans_urls"):
            icon = "📚" if col == "reference_uris" else "🌠"
            return HTMLTemplateFormatter(
                template="""
                <%
                    if (Array.isArray(value)) {
                        urls = value;
                    } else {
                        const sanitizedValue = value.replace(/'/g, '"');
                        const urls = JSON.parse(sanitizedValue);
                        console.log('Parsed JSON:', urls);
                    }
                    for (let i = 0; i < urls.length; i++) {
                %>
                    <a href="<%= urls[i] %>" target="_blank">LINK_TEXT</a>
                <% } %>
                """.replace("LINK_TEXT", icon)
            )

        return StringFormatter()

    columns = [
        TableColumn(
            field=col,
            title=markdown_columns.get(col, col),
            formatter=get_formatter(col),
            width=len(col),
        )
        for col in df.reset_index().columns
    ]

    source = ColumnDataSource(df)

    css = InlineStyleSheet(
        css="""
            .slick-header-column {
            background-color: #f4f4f4;
            font-weight: bold;
    }
    """
    )

    data_table = DataTable(
        source=source,
        columns=columns,
        sortable=True,
        sizing_mode="stretch_both",
    )
    data_table.stylesheets.append(css)

    heading = Div(text="<h1>Benchmark Problems</h1>")
    preamble = Div(
        text=f"""
        <p>
        This table provides an overview of the benchmark problems
        available in the <a href="{REPO_URL}">Benchmark-Models-PEtab</a>
        repository.
        </p>
        """
    )
    layout = column(heading, preamble, data_table, sizing_mode="stretch_both")
    output_file(dest, title="Benchmark Problems")
    save(layout)


def main():
    parser = argparse.ArgumentParser(
        description="Show overview table for benchmark PEtab problems"
    )
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument(
        "--markdown", action="store_true", help="Output in markdown format"
    )
    group1.add_argument(
        "--update",
        action="store_true",
        help="Update the README.md file with the overview table",
    )

    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument(
        "--html-file", help="Output the overview table to an HTML file"
    )

    args = parser.parse_args()

    if args.html_file:
        create_html_table(dest=Path(args.html_file))
    else:
        show_overview_table(markdown=args.markdown, update_readme=args.update)
