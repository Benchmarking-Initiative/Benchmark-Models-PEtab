New submissions are very welcome! Please check our [pull request template](.github/pull_request_template.md) for guidelines.

Simply create a new branch and open a pull request with your files. We will then check your model and merge it into the collection.

Each problem lives under `problems/<ProblemID>/`:
- `v1/` contains the PEtab problem itself: `problem.yaml`, `model.xml`, `conditions.tsv`,
  `measurements.tsv`, `observables.tsv`, `parameters.tsv`, and optionally `simulations.tsv`
  and `visualizations.tsv`.
- `resources/` (optional) holds anything else related to the problem that isn't part of the
  PEtab files themselves (e.g. raw data, scripts, notebooks, figures). There's no prescribed
  structure — organize it however fits your problem.
