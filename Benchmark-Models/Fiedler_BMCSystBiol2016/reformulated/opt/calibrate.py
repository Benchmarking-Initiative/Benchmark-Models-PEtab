import petab
import amici
import pypesto
import pypesto.petab
import pypesto.optimize
import pypesto.store
from pathlib import Path

model_name = "Fiedler_BMCSystBiol2016"
petab_problem = petab.Problem.from_yaml(f"../{model_name}.yaml")
petab_problem_flat = petab.Problem.from_yaml(f"../{model_name}.yaml")
petab.flatten_timepoint_specific_output_overrides(petab_problem_flat)
petab_problem_flat.visualization_df = None

pypesto_importer = pypesto.petab.PetabImporter(petab_problem_flat)
pypesto_problem = pypesto_importer.create_problem()

result = pypesto.optimize.minimize(
    pypesto_problem, 
    optimizer=pypesto.optimize.FidesOptimizer(),
    n_starts=1000,
)

# Save result object in hdf5 file
pypesto.store.save_to_hdf5.write_result(result, 'result.hdf5', overwrite= True)

# Visualization
import pypesto.visualize as vis
import matplotlib.pyplot as plt

vis.waterfall(result, size=(8, 4))
plt.savefig('waterfall.png')
plt.close()

from pypesto.visualize.model_fit import visualize_optimized_model_fit
visualize_optimized_model_fit(
    petab_problem=petab_problem_flat,
    result=result,
    pypesto_problem=pypesto_problem,
    return_dict=False,
    start_index=0,
    unflattened_petab_problem=petab_problem,
)
plt.savefig("fit.png")
plt.close()

FITS_PATH = Path(__file__).resolve().parent / "fits"
FITS_PATH.mkdir(exist_ok=True)
for n in range(1, 20):
    visualize_optimized_model_fit(
        petab_problem=petab_problem_flat,
        result=result,
        pypesto_problem=pypesto_problem,
        return_dict=False,
        start_index=n,
        unflattened_petab_problem=petab_problem,
    )
    plt.savefig(FITS_PATH / f"fit_{str(n).rjust(2, '0')}.png")
    plt.close()
