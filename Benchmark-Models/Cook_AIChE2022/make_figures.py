#!/usr/bin/env python3
"""Reproduce figures from Cook et al. (2022) from the PEtab v2 problem.

Every trajectory here is obtained by simulating the PEtab v2 problem itself
with AMICI, reusing the collection's simulation code
(``src/python/simulate.py``:``create_v2_simulator``, which encodes the
experiment periods as events). Each experiment is simulated with dense output
timepoints so that AMICI applies the ``cycle_reset`` condition at every 100-day
boundary. All figures are derived from the four dose experiments
(``exp_Wnt_m1``, ``exp_Wnt_5``, ``exp_Wnt_50``, ``exp_Wnt_1_8``).

Because only these four Wnt-10b fold changes exist in the problem, some figures
are necessarily reduced relative to the publication:

* Figure 4 shows the fold-change-1.8 trajectory and the Roser-Page data, but
  not the 1.2-2.4 envelope (those fold changes are not part of the problem).
* Figure 6 shows the AUC ratios at the four available fold changes as discrete
  points rather than a continuous sweep.

The cycle-boundary state change makes the system stiff, so the AMICI absolute
tolerance is loosened from its very tight default (1e-16) to 1e-12; these
solver settings are passed explicitly to the simulator (see ``COOK_SOLVER``).

Requirements: petab (v2), amici, matplotlib, numpy>=2 (a C++ compiler is needed
the first time, to build the AMICI model).
Run from anywhere: ``python make_figures.py`` (figures are written next to it).
"""
import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import amici.sim.sundials as ass
import petab.v2 as petab

HERE = Path(__file__).resolve().parent
PID = "Cook_AIChE2022"
CYCLE = 100.0
# the cycle-reset state change makes the system stiff; loosen AMICI's very
# tight default absolute tolerance (see the module docstring).
COOK_SOLVER = dict(rtol=1e-10, atol=1e-12, max_steps=10**6)

# reuse the collection's AMICI PEtab simulation code
sys.path.insert(0, str(HERE.parents[1] / "src" / "python"))
from simulate import create_v2_simulator  # noqa: E402

# experiment id -> (Wnt-10b fold change, number of remodeling cycles)
EXP = {"exp_Wnt_m1": (-1.0, 6), "exp_Wnt_5": (5.0, 6),
       "exp_Wnt_50": (50.0, 12), "exp_Wnt_1_8": (1.8, 12)}

problem = petab.Problem.from_yaml(str(HERE / f"{PID}.yaml"))
nominal = problem.get_x_nominal_dict()
meas_df = problem.measurement_df  # Bennett fitting data (in the problem YAML)
# Roser-Page validation data, held out of the fit (separate table, not in YAML)
val_df = pd.read_csv(HERE / f"measurementData_validation_{PID}.tsv", sep="\t")

# --- import & compile the PEtab problem with AMICI -------------------------
_sim = create_v2_simulator(problem, verbose=logging.WARNING,
                           solver_settings=COOK_SOLVER)
_model, _em, _solver = _sim.model, _sim.exp_man, _sim.solver
# states are needed for the trajectory figures
_solver.set_return_data_reporting_mode(ass.RDataReporting.full)
STATES = list(_model.get_state_ids())  # S, P, B, C, z
Z = STATES.index("Bone_volume__z")


def trajectory(exp_id, n_per_cycle=401):
    """Dense state trajectory of a PEtab experiment simulated with AMICI.

    Returns ``(t, Y)`` with the state columns ordered as ``STATES``. AMICI
    applies the ``cycle_reset`` condition at each 100-day period boundary."""
    _, ncyc = EXP[exp_id]
    edata = _em.create_edata(exp_id, problem_parameters=nominal)
    edata.set_timepoints(np.linspace(0, ncyc * CYCLE, ncyc * (n_per_cycle - 1) + 1))
    rdata = ass.run_simulation(_model, _solver, edata)
    assert rdata.status == 0, f"{exp_id} failed with status {rdata.status}"
    return np.asarray(rdata.ts), np.asarray(rdata.x)


TRAJ = {exp_id: trajectory(exp_id) for exp_id in EXP}


def first_cycle(exp_id):
    """The first remodeling cycle (t < 100, before the first reset)."""
    t, y = TRAJ[exp_id]
    m = t < CYCLE
    return t[m], y[m]


def save(name):
    plt.tight_layout()
    plt.savefig(HERE / name, dpi=120, bbox_inches="tight")
    plt.close("all")
    print("wrote", name)


# --- Figure 1: dose-response, simulation vs data ----------------------------
# Simulated observables at the measurement timepoints, straight from the PEtab
# simulator.
_res = _sim.simulate()
print("total llh:", _res.llh)
sim_obs = {}
for rd in _res.rdatas:
    if rd.y is None or np.asarray(rd.y).size == 0:
        continue  # e.g. the validation experiment, which has no measurements
    for t, y in zip(np.atleast_1d(np.asarray(rd.ts)),
                    np.atleast_1d(np.asarray(rd.y).ravel())):
        sim_obs[(rd.id, round(float(t)))] = float(y)


def _sim_obs(exp_id, time):
    """Simulated observable (z - 100) for an experiment at a given time.

    Fitting experiments come straight from the PEtab simulator; the held-out
    validation experiment is not in the fitted problem, so its value is taken
    from the dense trajectory (z is continuous across the cycle resets)."""
    key = (exp_id, round(float(time)))
    if key in sim_obs:
        return sim_obs[key]
    t, y = TRAJ[exp_id]
    return float(np.interp(float(time), t, y[:, Z])) - 100.0


fig, ax = plt.subplots(figsize=(7, 6))
colors = plt.cm.tab10.colors
i = 0
for _, row in pd.concat([meas_df, val_df], ignore_index=True).iterrows():
    wnt = EXP[row["experimentId"]][0]
    ax.plot(wnt, row["measurement"], "x", color=colors[i % 10], ms=9, mew=2)
    ax.plot(wnt, _sim_obs(row["experimentId"], row["time"]), "o",
            color=colors[i % 10], ms=9, label=str(row["datasetId"]).replace("_", " "))
    i += 1
ax.set_xlabel("Wnt-10b (fold change)")
ax.set_ylabel("BV/TV (% change from normal)")
ax.set_title("Cook et al. 2022 - BV/TV change vs Wnt-10b (x: data, o: simulation)")
ax.legend(loc="best", fontsize=8)
save("fig1_validation_doseresponse.png")

# --- Figure 2: relative bone volume over remodeling cycles ------------------
data_points = {  # relative bone volume = 100 + BV/TV % change
    "exp_Wnt_m1": [(400, 100 - 29.7), (600, 100 - 41.9)],
    "exp_Wnt_5": [(600, 100 + 69.2)],
    "exp_Wnt_50": [(1200, 100 + 339)],
}
fig, ax = plt.subplots(figsize=(8, 6))
for i, exp_id in enumerate(["exp_Wnt_m1", "exp_Wnt_5", "exp_Wnt_50"]):
    t, y = TRAJ[exp_id]
    ax.plot(t, y[:, Z], lw=1.6, color=f"C{i}",
            label=f"Wnt-10b fold change {EXP[exp_id][0]:g}")
    for tt, zz in data_points[exp_id]:
        ax.plot(tt, zz, "x", color=f"C{i}", ms=9, mew=2)
ax.set_xlabel("time (days)")
ax.set_ylabel("relative bone volume (%)")
ax.set_title("Relative bone volume over remodeling cycles")
ax.legend(loc="best")
save("fig2_bone_volume_vs_time.png")

# --- Figure 3: cell-population dynamics for Wnt-10b fold change 50 ----------
t, y = TRAJ["exp_Wnt_50"]
labels = ["osteocytes (S)", "pre-osteoblasts (P)", "osteoblasts (B)",
          "osteoclasts (C)"]
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
for ax, idx, lbl in zip(axes.flat, range(4), labels):
    ax.plot(t, y[:, idx], color="C0", lw=1.2)
    ax.set_xlabel("time (days)")
    ax.set_ylabel(lbl + " (cells)")
    ax.set_title(lbl)
fig.suptitle("Cell-population dynamics (Wnt-10b fold change 50)")
save("fig3_cell_populations_Wnt50.png")

# --- Figure 4 (paper): model validation against Roser-Page 2014 data --------
# The 1.2-2.4 envelope of the publication is omitted: those fold changes are
# not experiments in the PEtab problem.
t, y = TRAJ["exp_Wnt_1_8"]
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(t, y[:, Z], color="C0", lw=1.8,
        label="simulation (Wnt-10b fold change 1.8)")
# validation points and their reported SDs come from the validation table;
# measurements are BV/TV % change, plotted as relative bone volume (100 + %).
val_styles = {600: ("o", "C1"), 1200: ("s", "C3")}
for _, row in val_df.iterrows():
    tt = float(row["time"])
    fmt, col = val_styles.get(round(tt), ("o", "C1"))
    ax.errorbar(tt, 100 + row["measurement"], row["noiseParameters"],
                fmt=fmt, color=col, capsize=4, lw=2,
                label=f"Roser-Page 2014 ({round(tt / CYCLE)} remodeling cycles)")
ax.set_xlabel("time (days)")
ax.set_ylabel("relative bone volume (%)")
ax.set_xlim(-10, 1210)
ax.set_title("Cook et al. 2022 Fig. 4 - validation vs Roser-Page data")
ax.legend(loc="best")
save("fig4_validation_roserpage.png")

# --- Figure 5 (paper): activated cell-population dynamics, single cycle ------
panels = [(0, "osteocytes (S)", "A"), (1, "pre-osteoblasts (P)", "B"),
          (2, "osteoblasts (B)", "C"), (3, "osteoclasts (C)", "D")]
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
for ax, (idx, lbl, ttl) in zip(axes.flat, panels):
    for exp_id in ["exp_Wnt_m1", "exp_Wnt_5", "exp_Wnt_50"]:
        tc, yc = first_cycle(exp_id)
        ax.plot(tc, yc[:, idx], lw=2, label=f"Wnt-10b fold change {EXP[exp_id][0]:g}")
    ax.set_xlabel("time (days)")
    ax.set_ylabel(lbl + " (cells)")
    ax.set_title(ttl)
axes.flat[0].legend(loc="best", fontsize=8)
fig.suptitle("Cook et al. 2022 Fig. 5 - cell-population dynamics over a single cycle")
save("fig5_cell_dynamics_single_cycle.png")

# --- Figure 6 (paper): AUC ratios vs Wnt-10b (at the available fold changes) -
# A continuous sweep is not available from the problem; the ratios are shown at
# the four experiment fold changes.
rows = []
for exp_id, (wnt, _) in EXP.items():
    tc, yc = first_cycle(exp_id)
    a_po, a_ob, a_oc = (np.trapezoid(yc[:, k], tc) for k in (1, 2, 3))
    rows.append((wnt, a_po / a_ob, a_oc / a_ob))
rows.sort()
wnts = [r[0] for r in rows]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].plot(wnts, [r[1] for r in rows], "o-", color="C0", lw=1.5)
axes[0].set_ylabel("pre-osteoblast : osteoblast AUC")
axes[0].set_title("A")
axes[1].plot(wnts, [r[2] for r in rows], "o-", color="C3", lw=1.5)
axes[1].set_ylabel("osteoclast : osteoblast AUC")
axes[1].set_title("B")
for ax in axes:
    ax.set_xlabel("Wnt-10b (fold change)")
fig.suptitle("Cook et al. 2022 Fig. 6 - cell-population AUC ratios vs Wnt-10b")
save("fig6_auc_ratios.png")
