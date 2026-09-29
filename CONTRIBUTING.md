New submissions are very welcome! Please check our [pull request template](.github/pull_request_template.md) for guidelines.

Simply create a new branch and open a pull request with your files. We will then check your model and merge it into the collection.

Each problem lives under `problems/<ProblemID>/`, with at least one of `v1/`/`v2/` present:
- `v1/` holds the problem in PEtab v1 format: `problem.yaml`, `model.xml`,
  `conditions.tsv`, `measurements.tsv`, `observables.tsv`, `parameters.tsv`, and optionally
  `simulations.tsv` and `visualizations.tsv`.
- `v2/` holds the same problem in PEtab v2 format.
- `metadata.yaml` contains version-independent metadata. Currently, this is a single-sentence
  `short_description` of the problem, stating the type of model (e.g., biochemical reaction network,
  compartmental epidemiological model), the biological system, and, where informative, the data.
  For example:
  ```yaml
  short_description: Reaction network model of Epo-induced STAT5A/STAT5B phosphorylation and homo- and heterodimerization, fitted to quantitative mass spectrometry data.
  ```
  The file is validated against the `ProblemMetadata` model in
  [`metadata.py`](src/python/benchmark_models_petab/metadata.py)
  (check with `bmp-check-metadata`); the corresponding JSON schema is
  [`metadata.schema.json`](src/python/benchmark_models_petab/schemas/metadata.schema.json).
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

For problems with priors (maximum a posteriori estimation), the policy is not decided yet:
v1 priors on log-scaled parameters cannot, in general, be expressed as v2 priors without
changing either the optimum or the prior distribution. See
[#333](https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab/issues/333).
