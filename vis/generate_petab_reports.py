import argparse
import base64
import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import petab.v1
import petab.v1.visualize.plotter
from jinja2 import Environment, FileSystemLoader
from petab.visualize import plot_problem

import benchmark_models_petab as bmp

# plot simulation line without markers
petab.v1.visualize.plotter.simulation_line_kwargs["marker"] = ""
# plot measurements with markers only
petab.v1.visualize.plotter.measurement_line_kwargs["linestyle"] = "None"


def _plot_problem(problem: petab.v1.Problem, sim_df: pd.DataFrame) -> str:
    """Plot measurement points and simulation line for one observable and return base64 png."""
    plot_problem(problem, simulations_df=sim_df)
    fig = plt.gcf()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("ascii")
    return img_b64


def generate_report_for_model(problem_id: str, template_env: Environment, out_dir: Path):
    problem = bmp.get_problem(problem_id)
    if problem is None:
        return

    sim_df = bmp.get_simulation_df(problem_id)

    images: list[dict[str, str]] = []
    img = _plot_problem(problem, sim_df)
    images.append({"id": problem_id, "img": img})

    template = template_env.get_template("problem_report.html.jinja")
    rendered = template.render(model_name=problem_id, images=images)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{problem_id}.html"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(rendered)
    print(f"Wrote {out_path}")


def generate_index(problem_id_list: list[str], template_env: Environment, out_dir: Path):
    """Render an index page with links to per-problem reports."""
    template = template_env.get_template("index.html.jinja")
    rendered = template.render(models=problem_id_list, count=len(problem_id_list))

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(rendered)
    print(f"Wrote {out_path}")


def main(output_dir: Path = None):
    if output_dir is None:
        output_dir = Path(__file__).parent / "reports"
    templates_dir = Path(__file__).parent / "templates"

    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    problem_id_list = list(bmp.MODELS)

    for problem_id in problem_id_list:
        try:
            generate_report_for_model(problem_id, env, output_dir)
        except Exception as e:
            print(f"Skipping {problem_id} due to error: {e}")

    try:
        generate_index(problem_id_list, env, output_dir)
    except Exception as e:
        print(f"Failed to write index: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PETab problem reports")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Directory to write reports to (default: vis/reports)",
    )
    args = parser.parse_args()

    main(args.output_dir)
