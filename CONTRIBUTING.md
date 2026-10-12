New submissions are very welcome! Please check our [pull request template](.github/pull_request_template.md) for guidelines.

Simply create a new branch and open a pull request with your files. We will then check your model and merge it into the collection.

Each problem lives under `problems/<ProblemID>/`:
- `v1/` contains the PEtab problem itself: `problem.yaml`, `model.xml`, `conditions.tsv`,
  `measurements.tsv`, `observables.tsv`, `parameters.tsv`, and optionally `simulations.tsv`
  and `visualizations.tsv`.
- `metadata.yaml` contains version-independent metadata. Currently, this is a single-sentence
  `description` of the problem, stating the type of model (e.g., biochemical reaction network,
  compartmental epidemiological model), the biological system, and, where informative, the data.
  For example:
  ```yaml
  description: Reaction network model of Epo-induced STAT5A/STAT5B phosphorylation and homo- and heterodimerization, fitted to quantitative mass spectrometry data.
  ```
  The file is validated against
  [`metadata.schema.json`](src/python/benchmark_models_petab/schemas/metadata.schema.json)
  (check with `bmp-check-metadata`).
- `resources/` (optional) holds anything else related to the problem that isn't part of the
  PEtab files themselves (e.g. raw data, scripts, notebooks, figures). There's no prescribed
  structure — organize it however fits your problem.
