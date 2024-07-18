from pathlib import Path


benchmark_path = Path(__file__).resolve().parent.parent / 'Benchmark-Models'
petab_yamls = {
    petab_path.name: benchmark_path / petab_path.name / (petab_path.name + '.yaml')
    for petab_path in benchmark_path.glob('*')
    if petab_path.name != '.DS_Store'
}
petab_yamls = {k: petab_yamls[k] for k in sorted(petab_yamls)}

for problem_id, petab_yaml in petab_yamls.items():
    if not petab_yaml.exists():
        petab_yamls[problem_id] = petab_yaml.parent / "problem.yaml"
        if not petab_yamls[problem_id].exists():
            raise FileNotFoundError(
                f"Could not find the YAML for problem `{problem_id}`."
            )

readme_md = Path(__file__).resolve().parent.parent / "README.md"
