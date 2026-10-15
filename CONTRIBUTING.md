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
parameters as `v1/`, up to the reparametrization described below.

PEtab v2 has no `parameterScale`: priors and the objective are always expressed in terms of the
parameter itself. To preserve the v1 optimization problem (and, for maximum a posteriori problems,
the v1 prior distribution), estimated `log`/`log10`-scaled v1 parameters are reparametrized in
`v2/`: an estimated `log10_<id>` (or `log_<id>`) replaces `<id>`, and `10^log10_<id>`
(or `exp(log_<id>)`) is substituted everywhere `<id>` appeared (model, observable and noise
formulas, condition and measurement table overrides). A v1 `parameterScale*` prior becomes the
corresponding prior on the new parameter; the v1 default prior (uniform on parameter scale)
becomes the v2 default prior (uniform within the transformed bounds).
Parameters with a prior on linear scale (e.g. a v1 `objectivePriorType` of `normal`, `laplace`,
...) are not reparametrized; their prior is already the same in both encodings.

Measurement table overrides cannot be expressions. Therefore, for a reparametrized parameter
used as an override, the placeholder is transformed instead (`<placeholder>` becomes
`10^<placeholder>` in the observable or noise formula), and all overrides of that placeholder are
log-transformed. If the same placeholder also receives non-positive numbers or parameters that
stay on linear scale, the observable is split, so that each copy's placeholder only receives
overrides that can be log-transformed, or none at all.

See [#333](https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab/issues/333) for
the rationale (option C there).
