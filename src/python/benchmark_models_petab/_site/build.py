"""Build the overview page of the GitHub Pages site."""

import json
from pathlib import Path

import pandas as pd

from .. import overview, overview_v2, v1, v2
from ..C import MODELS
from ..C import (
    GITHUB_DEFAULT_BRANCH,
    GITHUB_REPO,
    PROBLEMS_DIRNAME,
    V1_DIRNAME,
    V2_DIRNAME,
)
from ..metadata import get_metadata

REPO_URL = f"https://github.com/{GITHUB_REPO}"
LOGO_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_REPO}"
    f"/{GITHUB_DEFAULT_BRANCH}/gfx/logo.svg"
)
CONTRIBUTING_URL = f"{REPO_URL}/blob/{GITHUB_DEFAULT_BRANCH}/CONTRIBUTING.md"

#: Rendering of the columns that are not plain text, by column name.
#:  Other columns of integer dtype are rendered as numbers.
column_kinds = {
    "petab_problem_id": "id",
    "short_description": "description",
    "possible_discontinuities": "bool",
    "noise_distributions": "tags",
    "objective_prior_distributions": "tags",
    "prior_distributions": "tags",
    "reference_uris": "links",
    "sbml4humans_urls": "links",
}

#: Column groups, in display order, with their columns.
#:  Columns without a group are shown first.
column_groups = {
    "Links": ["reference_uris", "sbml4humans_urls"],
    "Size": [
        "conditions",
        "experiments",
        "estimated_parameters",
        "measurements",
        "observables",
        "species",
    ],
    "Features": [
        "events",
        "preequilibration",
        "postequilibration",
        "possible_discontinuities",
    ],
    "Distributions": [
        "noise_distributions",
        "objective_prior_distributions",
        "prior_distributions",
    ],
}

column_group = {
    col: group for group, cols in column_groups.items() for col in cols
}

#: Statistics shown as summary tiles, as (v1 column, v2 column, label).
summary_columns = [
    ("conditions", "experiments", "simulation conditions"),
    ("estimated_parameters", "estimated_parameters", "estimated parameters"),
    ("measurements", "measurements", "measurements"),
    ("observables", "observables", "observables"),
]


def get_table(
    df: pd.DataFrame,
    labels: dict[str, str],
    descriptions: dict[str, str],
    version_dirname: str,
) -> dict:
    """Get the data and column specification for one overview table.

    :param df: Overview table as returned by `get_overview_df`.
    :param labels: Column labels, by column name.
    :param descriptions: Column descriptions, by column name.
    :param version_dirname: The encoding's directory (`v1`, `v2`).
    """
    df = df.reset_index()
    df.insert(
        1,
        "short_description",
        [get_metadata(id_).short_description for id_ in df.petab_problem_id],
    )
    labels = {"short_description": "Description"} | labels
    descriptions = {
        "short_description": (
            "Model type, biological system, and, where informative, the data."
        )
    } | descriptions
    # ungrouped columns first, in their original order, then the groups
    ungrouped = [col for col in df.columns if col not in column_group]
    ordered_columns = ungrouped + [
        col for cols in column_groups.values() for col in cols if col in df
    ]
    columns = [
        {
            "field": col,
            "title": labels.get(col, col),
            "tooltip": descriptions.get(col),
            "group": column_group.get(col),
            "kind": column_kinds.get(
                col,
                "int" if pd.api.types.is_integer_dtype(df[col]) else "text",
            ),
        }
        for col in ordered_columns
    ]
    return {
        "columns": columns,
        "rows": json.loads(df[ordered_columns].to_json(orient="records")),
        "tree_url": (
            f"{REPO_URL}/tree/{GITHUB_DEFAULT_BRANCH}/{PROBLEMS_DIRNAME}"
            f"/{{id}}/{version_dirname}"
        ),
    }


def get_summary_tiles(v1_df: pd.DataFrame, v2_df: pd.DataFrame) -> list:
    """Get the summary statistics shown above the tables.

    The ranges are computed from the v1 statistics, and from the v2
    statistics for problems without a v1 encoding.

    :param v1_df: v1 overview table.
    :param v2_df: v2 overview table.
    :return: List of ``(value, label, tooltip)`` tuples.
    """
    tiles = [
        (
            f"{len(MODELS)}",
            "problems in total",
            "Number of benchmark problems, in any PEtab version.",
        ),
        (
            f"{len(v1.MODELS)}",
            "in PEtab v1",
            "Number of problems with a PEtab v1 encoding.",
        ),
        (
            f"{len(v2.MODELS)}",
            "in PEtab v2",
            "Number of problems with a PEtab v2 encoding.",
        ),
    ]
    v2_only = ~v2_df.index.isin(v1_df.index)
    for v1_col, v2_col, label in summary_columns:
        values = pd.concat([v1_df[v1_col], v2_df.loc[v2_only, v2_col]])
        tooltip = f"Smallest and largest number of {label} per problem."
        if v1_col != v2_col:
            tooltip += (
                f" For problems without a PEtab v1 encoding, the number of "
                f"{overview_v2.columns[v2_col].lower()}."
            )
        tiles.append((f"{values.min():,}–{values.max():,}", label, tooltip))
    return tiles


def create_overview_page(dest: Path) -> None:
    """Create the HTML page with the v1 and v2 overview tables.

    :param dest: Path to the output HTML file.
    """
    from jinja2 import Environment, PackageLoader, select_autoescape

    env = Environment(
        loader=PackageLoader(__package__),
        autoescape=select_autoescape(["html", "j2"]),
    )
    v1_df = overview.get_overview_df()
    v2_df = overview_v2.get_overview_df()
    html = env.get_template("index.html.j2").render(
        repo_url=REPO_URL,
        logo_url=LOGO_URL,
        contributing_url=CONTRIBUTING_URL,
        summary_tiles=get_summary_tiles(v1_df, v2_df),
        tables={
            "v2": get_table(
                v2_df,
                overview_v2.columns,
                overview_v2.column_descriptions,
                V2_DIRNAME,
            ),
            "v1": get_table(
                v1_df,
                overview.columns,
                overview.column_descriptions,
                V1_DIRNAME,
            ),
        },
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
