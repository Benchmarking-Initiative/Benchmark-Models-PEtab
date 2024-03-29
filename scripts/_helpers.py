from pathlib import Path


benchmark_path = Path(__file__).parent.parent / 'Benchmark-Models'
petab_yamls = {
    petab_path.name: benchmark_path / petab_path.name / (petab_path.name + '.yaml')
    for petab_path in benchmark_path.glob('*')
    if petab_path.name != '.DS_Store'
}
petab_yamls = {k: petab_yamls[k] for k in sorted(petab_yamls)}
