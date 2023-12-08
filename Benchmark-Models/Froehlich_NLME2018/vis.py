from petab.visualize import plot_with_vis_spec, plot_without_vis_spec

folder = "./"

data_file_path = folder + "measurementTable.tsv"
condition_file_path = folder + "conditionTable.tsv"
visualization_file_path = folder + "visualizationTable.tsv"
simulation_file_path = None

# ax = plot_with_vis_spec(
#     visualization_file_path,
#     condition_file_path,
#     data_file_path,
#     simulation_file_path,
# )

ax_without_sim = plot_with_vis_spec(
    visualization_file_path,
    condition_file_path,
    data_file_path
)

