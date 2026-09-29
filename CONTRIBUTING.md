New submissions are very welcome! Please check our [pull request template](.github/pull_request_template.md) for guidelines.

Simply create a new branch and open a pull request with your files. We will then check your model and merge it into the collection.

Each problem lives under `problems/<ProblemID>/`, with at least one of `v1/`/`v2/` present:
- `v1/` holds the problem in PEtab v1 format: `problem.yaml`, `model.xml`,
  `conditions.tsv`, `measurements.tsv`, `observables.tsv`, `parameters.tsv`, and optionally
  `simulations.tsv` and `visualizations.tsv`.
- `v2/` holds the same problem in PEtab v2 format.
- `resources/` (optional) holds anything else related to the problem that isn't part of the
  PEtab files themselves (e.g. raw data, scripts, notebooks, figures). There's no prescribed
  structure — organize it however fits your problem.

## v1/v2 equivalence

A problem's `v1/` and `v2/` encodings must represent *exactly* the same mathematical problem:
same model, same data, same objective.

This is a constraint on the math, not the encoding: `v2/` files may (and often should) look
structurally different from a mechanical v1-to-v2 port to make idiomatic use of v2 features
(experiments table, v2 prior/distribution syntax, mapping tables, ...) where they fit better.
They just have to evaluate to the same log-likelihood / log-posterior / gradient at nominal
parameters as `v1/`.
