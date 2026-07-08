#!/usr/bin/env python3
"""Reproduce figures from Cook et al. (2022) using PEtab visualization.

The script simulates the PEtab model in this directory (via libroadrunner)
and plots the results with ``petab.v1.visualize``. It produces:

1. ``fig1_validation_doseresponse.png`` -- BV/TV change vs Wnt-10b fold change,
   model fit vs the Bennett 2005/2007 data (the committed PEtab visualization),
   now also overlaying the Roser-Page 2014 validation points.
2. ``fig2_bone_volume_vs_time.png`` -- relative bone volume over the multiple
   remodeling cycles for Wnt-10b fold changes -1, 5 and 50.
3. ``fig3_cell_populations_Wnt50.png`` -- osteocyte / pre-osteoblast /
   osteoblast / osteoclast dynamics for a Wnt-10b fold change of 50.

It additionally reproduces two figures using the paper's figure numbering:

5. ``fig5_validation_roserpage.png`` -- Figure 5: model validation against the
   Roser-Page (2014) data. Relative bone volume over 12 remodeling cycles at a
   Wnt-10b fold change of 1.8, with the 1.2-2.4 fold-change envelope shaded, vs
   the two Roser-Page BV/TV data points (126.6 +/- 19.2 % at 600 d / 6 cycles
   and 136.6 +/- 40.6 % at 1200 d / 12 cycles).
6. ``fig6_cellpopulations_vs_wnt.png`` -- Figure 6: cell-population response to
   Wnt-10b. Maximum pre-osteoblast, osteoblast and osteoclast counts within a
   remodeling cycle as a function of the Wnt-10b fold change.

Requirements: petab, libroadrunner, matplotlib, numpy, pandas.
Run from anywhere: ``python make_figures.py`` (figures are written next to it).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import roadrunner
import petab.v1 as petab
from petab.v1.visualize import plot_problem, plot_with_vis_spec

HERE = Path(__file__).resolve().parent
PID = "Cook_AIChE2022"
SBML = str(HERE / f"model_{PID}.xml")

problem = petab.Problem.from_yaml(str(HERE / f"{PID}.yaml"))
nominal = dict(zip(problem.parameter_df.index, problem.parameter_df["nominalValue"]))
conditions = problem.condition_df

# state id -> short observable name used for the figures
STATES = {
    "Osteocytes__S": "osteocytes",
    "Pre_Osteoblasts__P": "pre_osteoblasts",
    "Osteoblasts__B": "osteoblasts",
    "Osteoclasts__C": "osteoclasts",
    "Bone_volume__z": "bone_volume",
}
DOSES = [
    ("Wnt_m1", -1, "Wnt-10b fold change -1"),
    ("Wnt_5", 5, "Wnt-10b fold change 5"),
    ("Wnt_50", 50, "Wnt-10b fold change 50"),
]


def simulate(wnt, t_end, n_points=2400):
    """Densely simulate the SBML model for a given Wnt-10b fold change."""
    rr = roadrunner.RoadRunner(SBML)
    for pid, val in nominal.items():
        rr.setValue(pid, float(val))
    rr.setValue("Wnt", float(wnt))
    rr.selections = ["time"] + list(STATES)
    return np.array(rr.simulate(0, t_end, n_points))


def clean_lines(axes_dict):
    """Suppress the per-point markers PEtab draws on dense simulation lines."""
    for ax in axes_dict.values():
        for line in ax.get_lines():
            if len(line.get_xdata()) > 50:
                line.set_marker("None")
                line.set_linewidth(1.6)


def save(name):
    plt.tight_layout()
    plt.savefig(HERE / name, dpi=120, bbox_inches="tight")
    plt.close("all")
    print("wrote", name)


# --- Figure 1: dose-response validation (committed PEtab visualization) -----
plot_problem(problem, simulations_df=petab.get_simulation_df(str(HERE / f"simulatedData_{PID}.tsv")))
plt.gcf().set_size_inches(7, 6)
plt.title("Cook et al. 2022 - BV/TV change vs Wnt-10b (fit vs Bennett data)")
save("fig1_validation_doseresponse.png")

# --- Figure 2: relative bone volume over remodeling cycles ------------------
z_idx = 1 + list(STATES).index("Bone_volume__z")
data_points = {  # relative bone volume = 100 + BV/TV % change
    "Wnt_m1": [(400, 100 - 29.7), (600, 100 - 41.9)],
    "Wnt_5": [(600, 100 + 69.2)],
    "Wnt_50": [(1200, 100 + 339)],
}
sim_rows, meas_rows, vis_rows = [], [], []
for cond_id, wnt, name in DOSES:
    t_end = 1200 if cond_id == "Wnt_50" else 600
    arr = simulate(wnt, t_end)
    ds = f"ds_{cond_id}"
    for ti, zi in zip(arr[:, 0], arr[:, z_idx]):
        sim_rows.append(dict(observableId="bone_volume", simulationConditionId=cond_id,
                             time=ti, simulation=zi, noiseParameters=0, datasetId=ds))
    for ti, zi in data_points[cond_id]:
        meas_rows.append(dict(observableId="bone_volume", simulationConditionId=cond_id,
                              time=ti, measurement=zi, noiseParameters=0, datasetId=ds))
    vis_rows.append(dict(plotId="bone_volume", plotName="Relative bone volume over remodeling cycles",
                         plotTypeSimulation="LinePlot", plotTypeData="provided", datasetId=ds,
                         xValues="time", xLabel="time (days)", yValues="bone_volume",
                         yLabel="relative bone volume (%)", legendEntry=name))
clean_lines(plot_with_vis_spec(pd.DataFrame(vis_rows), conditions,
                               measurements_df=pd.DataFrame(meas_rows),
                               simulations_df=pd.DataFrame(sim_rows)))
plt.gcf().set_size_inches(8, 6)
save("fig2_bone_volume_vs_time.png")

# --- Figure 3: cell-population dynamics for Wnt-10b fold change 50 ----------
arr = simulate(50, 1200)
labels = {
    "Osteocytes__S": "osteocytes (S)",
    "Pre_Osteoblasts__P": "pre-osteoblasts (P)",
    "Osteoblasts__B": "osteoblasts (B)",
    "Osteoclasts__C": "osteoclasts (C)",
}
sim_rows, vis_rows = [], []
for state in labels:
    col = 1 + list(STATES).index(state)
    ds = f"ds_{state}"
    for ti, yi in zip(arr[:, 0], arr[:, col]):
        sim_rows.append(dict(observableId=STATES[state], simulationConditionId="Wnt_50",
                             time=ti, simulation=yi, noiseParameters=0, datasetId=ds))
    vis_rows.append(dict(plotId=STATES[state], plotName=labels[state],
                         plotTypeSimulation="LinePlot", plotTypeData="provided", datasetId=ds,
                         xValues="time", xLabel="time (days)", yValues=STATES[state],
                         yLabel=labels[state] + " (cells)", legendEntry="Wnt-10b fold change 50"))
clean_lines(plot_with_vis_spec(pd.DataFrame(vis_rows), conditions, simulations_df=pd.DataFrame(sim_rows)))
plt.gcf().set_size_inches(10, 7)
save("fig3_cell_populations_Wnt50.png")

# --- Figure 5 (paper): model validation against Roser-Page 2014 data --------
# Relative bone volume over 12 remodeling cycles at Wnt-10b fold change 1.8,
# with the 1.2-2.4 fold-change envelope shaded, vs the Roser-Page BV/TV data.
central = simulate(1.8, 1200)
low = simulate(1.2, 1200)
high = simulate(2.4, 1200)
tt = central[:, 0]
fig, ax = plt.subplots(figsize=(8, 6))
ax.fill_between(tt, low[:, z_idx], high[:, z_idx], color="0.8",
                label="Wnt-10b fold change 1.2-2.4")
ax.plot(tt, central[:, z_idx], color="C0", lw=1.8,
        label="simulation (Wnt-10b fold change 1.8)")
ax.errorbar(600, 126.6, 19.2, fmt="o", color="C1", capsize=4, lw=2,
            label="Roser-Page 2014 (6 remodeling cycles)")
ax.errorbar(1200, 136.6, 40.6, fmt="s", color="C3", capsize=4, lw=2,
            label="Roser-Page 2014 (12 remodeling cycles)")
ax.set_xlabel("time (days)")
ax.set_ylabel("relative bone volume (%)")
ax.set_xlim(-10, 1210)
ax.set_title("Cook et al. 2022 Fig. 5 - validation vs Roser-Page data")
ax.legend(loc="best")
save("fig5_validation_roserpage.png")

# --- Figure 6 (paper): cell-population response to Wnt-10b ------------------
# Maximum cell counts within a single remodeling cycle as a function of the
# Wnt-10b fold change (pre-osteoblasts and osteoblasts increase, osteoclasts
# decrease with increasing Wnt-10b).
c_idx = 1 + list(STATES).index("Osteoclasts__C")
p_idx = 1 + list(STATES).index("Pre_Osteoblasts__P")
b_idx = 1 + list(STATES).index("Osteoblasts__B")
wnts = np.linspace(-1, 50, 60)
max_po, max_ob, max_oc = [], [], []
for w in wnts:
    cyc = simulate(w, 100, n_points=1101)  # first remodeling cycle
    max_po.append(cyc[:, p_idx].max())
    max_ob.append(cyc[:, b_idx].max())
    max_oc.append(cyc[:, c_idx].max())
fig, axes = plt.subplots(1, 3, figsize=(13, 4))
for ax, ys, lbl, ttl, col in zip(
        axes, [max_po, max_ob, max_oc],
        ["max pre-osteoblasts (cells)", "max osteoblasts (cells)",
         "max osteoclasts (cells)"], ["A", "B", "C"], ["C0", "C2", "C3"]):
    ax.plot(wnts, ys, color=col, lw=2)
    ax.set_xlabel("Wnt-10b (fold change)")
    ax.set_ylabel(lbl)
    ax.set_title(ttl)
fig.suptitle("Cook et al. 2022 Fig. 6 - cell-population response to Wnt-10b")
save("fig6_cellpopulations_vs_wnt.png")
