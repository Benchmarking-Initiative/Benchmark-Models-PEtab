```python

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm

def plot_measurements_vs_simulation(simulation_df, measurement_df, output_file=None):
    """
    Generates a logarithmic scatter plot comparing measurements and simulations.

    Parameters:
        simulation_df (pd.DataFrame): DataFrame containing simulation data.
        measurement_df (pd.DataFrame): DataFrame containing measurement data.
        output_file (str, optional): If provided, saves the plot to this file. Defaults to None.

    Returns:
        None
    """
    # Merge the dataframes on relevant columns
    df_merged = pd.merge(
        pd.DataFrame(simulation_df),
        pd.DataFrame(measurement_df),
        on=['observableId', 'simulationConditionId', 'time', 'datasetId']
    )
    
    # Modify datasetID
    df_merged['datasetId'] = df_merged['datasetId'].str.extract(r'^[^_]*_([^_]*)_')[0]
    
    # Map unique colors to each datasetId
    unique_datasets = df_merged['datasetId'].unique()
    colors = cm.get_cmap('tab10', len(unique_datasets))  # Using 'tab10' color map
    
    # Initialize the plot
    plt.figure(figsize=(8, 8))
    plt.xscale('log')
    plt.yscale('log')
    
    # Scatter plot with color mapping for each datasetId
    for i, dataset in enumerate(unique_datasets):
        subset = df_merged[df_merged['datasetId'] == dataset]
        plt.scatter(subset['measurement'], subset['simulation'], color=colors(i), label=dataset)
        
    # Add bisectrix (y=x line)
    x_min, x_max = df_merged['measurement'].min(), df_merged['measurement'].max()
    plt.plot([x_min, x_max], [x_min, x_max], 'k--')
    
    # Labels, title, and legend
    plt.xlabel("Measurement (log scale)")
    plt.ylabel("Simulation (log scale)")
    plt.title("Logarithmic Measurement vs Simulation by Dataset")
    plt.legend(title="Dataset ID")
    
    # Show or save the plot
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    else:
        plt.show()
        
# Assuming `simulation_df` and `measurement_df` are predefined dataframes
plot_measurements_vs_simulation(simulation_df, measurement_df)

# To save the plot instead of showing it
plot_measurements_vs_simulation(simulation_df, measurement_df, output_file="measurements_vs_simulation.png")


```
