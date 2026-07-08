#!/usr/bin/env python3
"""Reproduce figures from Cook et al. (2022) from the PEtab v2 problem.

The remodeling cycles are encoded in the PEtab **experiment**/**condition**
tables, not in the SBML model. The four dose experiments are simulated with
AMICI through the regular PEtab route in ``simulate.py``/``simulatedData``; for
the figures we additionally need trajectories at Wnt-10b fold changes that are
*not* part of the problem (the 1.2-2.4 validation envelope and the fold-change
sweep of Figure 6). We therefore compile the event-free SBML model with AMICI
and integrate it cycle-by-cycle, applying the ``cycle_reset`` state change
(``S -> S - 20``; ``P``, ``B``, ``C`` set to 0 once they fall below 1) at each
100-day boundary -- i.e. AMICI is the integrator and the reset is exactly the
one defined by the PEtab ``cycle_reset`` condition.

Because the cycle-boundary state change makes the system stiff, the AMICI
absolute tolerance is loosened from its very tight default (1e-16) to 1e-12.

Figures (using the numbering of the original publication where applicable):

1. ``fig1_validation_doseresponse.png`` -- BV/TV change vs Wnt-10b fold change,
   simulation vs the Bennett 2005/2007 fitting data and the Roser-Page 2014
   validation data.
2. ``fig2_bone_volume_vs_time.png`` -- relative bone volume over the cycles for
   Wnt-10b fold changes -1, 5 and 50.
3. ``fig3_cell_populations_Wnt50.png`` -- cell dynamics for fold change 50.
4. ``fig4_validation_roserpage.png`` -- Figure 4: validation vs Roser-Page 2014
   (fold change 1.8, 1.2-2.4 envelope shaded).
5. ``fig5_cell_dynamics_single_cycle.png`` -- Figure 5: cell dynamics over a
   single cycle for fold changes -1, 5 and 50.
6. ``fig6_auc_ratios.png`` -- Figure 6: pre-osteoblast:osteoblast and
   osteoclast:osteoblast AUC ratios over a single cycle vs Wnt-10b fold change.

Requirements: petab (v2), amici, matplotlib, numpy (a C++ compiler is needed
the first time, to build the AMICI model).
Run from anywhere: ``python make_figures.py`` (figures are written next to it).
"""
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import amici
import amici.sim.sundials as ass
import petab.v2 as petab

HERE = Path(__file__).resolve().parent
PID = "Cook_AIChE2022"
CYCLE = 100.0  # days per remodeling cycle
trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy>=2 renamed trapz

problem = petab.Problem.from_yaml(str(HERE / f"{PID}.yaml"))
nominal = {p.id: p.nominal_value for p in problem.parameters}
meas_df = problem.measurement_df

# experiment id -> Wnt-10b fold change (from the condition table)
EXP_WNT = {"exp_Wnt_m1": -1.0, "exp_Wnt_5": 5.0, "exp_Wnt_50": 50.0,
           "exp_Wnt_1_8": 1.8}
DOSES = [(-1.0, 6, "Wnt-10b fold change -1"),
         (5.0, 6, "Wnt-10b fold change 5"),
         (50.0, 12, "Wnt-10b fold change 50")]

# --- compile the event-free SBML model with AMICI --------------------------
_build_dir = Path(tempfile.mkdtemp(prefix="cook_amici_"))
amici.SbmlImporter(str(HERE / f"model_{PID}.xml")).sbml2amici(
    model_name="cook_plain", output_dir=str(_build_dir),
    generate_sensitivity_code=False, verbose=False,
)
_model = amici.import_model_module("cook_plain", str(_build_dir)).get_model()
_solver = _model.create_solver()
_solver.set_relative_tolerance(1e-10)
_solver.set_absolute_tolerance(1e-12)  # default 1e-16 is too tight for the reset
_solver.set_max_steps(10 ** 6)
STATES = list(_model.get_state_ids())  # S, P, B, C, z
Z = STATES.index("Bone_volume__z")


def _cycle_reset(x):
    """The PEtab ``cycle_reset`` condition applied at a 100-day boundary."""
    s, p, b, c, z = x
    return np.array([s - 20.0,
                     0.0 if p < 1 else p,
                     0.0 if b < 1 else b,
                     0.0 if c < 1 else c,
                     z])


def simulate_cycles(wnt, ncyc, n_per_cycle=401):
    """Integrate the event-free model over ``ncyc`` cycles with AMICI, applying
    ``cycle_reset`` at each boundary. Returns dense ``(t, Y)`` with the state
    columns ordered as ``STATES``."""
    for pid, val in nominal.items():
        _model.set_free_parameter_by_id(pid, float(val))
    _model.set_free_parameter_by_id("Wnt", float(wnt))
    x = np.array([180.0, 0.0, 0.0, 0.0, 100.0])
    t_all, y_all = [], []
    for cyc in range(ncyc):
        _model.set_initial_state(x)
        _model.set_timepoints(np.linspace(0, CYCLE, n_per_cycle))
        rdata = ass.run_simulation(_model, _solver)
        t = np.asarray(rdata.ts) + cyc * CYCLE
        y = np.asarray(rdata.x)
        if cyc > 0:  # drop duplicated boundary sample
            t, y = t[1:], y[1:]
        t_all.append(t)
        y_all.append(y)
        x = y[-1].copy()
        if cyc < ncyc - 1:
            x = _cycle_reset(x)
    return np.concatenate(t_all), np.concatenate(y_all)


def obs_bv(wnt, ncyc):
    """Simulated relative BV/TV change (z - 100) after ``ncyc`` cycles."""
    _, y = simulate_cycles(wnt, ncyc)
    return y[-1, Z] - 100.0


def save(name):
    plt.tight_layout()
    plt.savefig(HERE / name, dpi=120, bbox_inches="tight")
    plt.close("all")
    print("wrote", name)


# --- Figure 1: dose-response, simulation vs data ----------------------------
fig, ax = plt.subplots(figsize=(7, 6))
colors = plt.cm.tab10.colors
for i, (_, row) in enumerate(meas_df.iterrows()):
    wnt = EXP_WNT[row["experimentId"]]
    ncyc = int(round(row["time"] / CYCLE))
    ax.plot(wnt, row["measurement"], "x", color=colors[i % 10], ms=9, mew=2)
    ax.plot(wnt, obs_bv(wnt, ncyc), "o", color=colors[i % 10], ms=9,
            label=str(row["datasetId"]).replace("_", " "))
ax.set_xlabel("Wnt-10b (fold change)")
ax.set_ylabel("BV/TV (% change from normal)")
ax.set_title("Cook et al. 2022 - BV/TV change vs Wnt-10b (x: data, o: simulation)")
ax.legend(loc="best", fontsize=8)
save("fig1_validation_doseresponse.png")

# --- Figure 2: relative bone volume over remodeling cycles ------------------
data_points = {  # relative bone volume = 100 + BV/TV % change
    -1.0: [(400, 100 - 29.7), (600, 100 - 41.9)],
    5.0: [(600, 100 + 69.2)],
    50.0: [(1200, 100 + 339)],
}
fig, ax = plt.subplots(figsize=(8, 6))
for i, (wnt, ncyc, name) in enumerate(DOSES):
    t, y = simulate_cycles(wnt, ncyc)
    ax.plot(t, y[:, Z], lw=1.6, color=f"C{i}", label=name)
    for tt, zz in data_points[wnt]:
        ax.plot(tt, zz, "x", color=f"C{i}", ms=9, mew=2)
ax.set_xlabel("time (days)")
ax.set_ylabel("relative bone volume (%)")
ax.set_title("Relative bone volume over remodeling cycles")
ax.legend(loc="best")
save("fig2_bone_volume_vs_time.png")

# --- Figure 3: cell-population dynamics for Wnt-10b fold change 50 ----------
t, y = simulate_cycles(50.0, 12)
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
tt, y_c = simulate_cycles(1.8, 12)
_, y_lo = simulate_cycles(1.2, 12)
_, y_hi = simulate_cycles(2.4, 12)
fig, ax = plt.subplots(figsize=(8, 6))
ax.fill_between(tt, y_lo[:, Z], y_hi[:, Z], color="0.8",
                label="Wnt-10b fold change 1.2-2.4")
ax.plot(tt, y_c[:, Z], color="C0", lw=1.8,
        label="simulation (Wnt-10b fold change 1.8)")
ax.errorbar(600, 126.6, 19.2, fmt="o", color="C1", capsize=4, lw=2,
            label="Roser-Page 2014 (6 remodeling cycles)")
ax.errorbar(1200, 136.6, 40.6, fmt="s", color="C3", capsize=4, lw=2,
            label="Roser-Page 2014 (12 remodeling cycles)")
ax.set_xlabel("time (days)")
ax.set_ylabel("relative bone volume (%)")
ax.set_xlim(-10, 1210)
ax.set_title("Cook et al. 2022 Fig. 4 - validation vs Roser-Page data")
ax.legend(loc="best")
save("fig4_validation_roserpage.png")

# --- Figure 5 (paper): activated cell-population dynamics, single cycle ------
panels = [(0, "osteocytes (S)", "A"), (1, "pre-osteoblasts (P)", "B"),
          (2, "osteoblasts (B)", "C"), (3, "osteoclasts (C)", "D")]
single = {wnt: simulate_cycles(wnt, 1) for wnt, _, _ in DOSES}
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
for ax, (idx, lbl, ttl) in zip(axes.flat, panels):
    for wnt, _, _ in DOSES:
        t, y = single[wnt]
        ax.plot(t, y[:, idx], lw=2, label=f"Wnt-10b fold change {wnt:g}")
    ax.set_xlabel("time (days)")
    ax.set_ylabel(lbl + " (cells)")
    ax.set_title(ttl)
axes.flat[0].legend(loc="best", fontsize=8)
fig.suptitle("Cook et al. 2022 Fig. 5 - cell-population dynamics over a single cycle")
save("fig5_cell_dynamics_single_cycle.png")

# --- Figure 6 (paper): area-under-curve ratios vs Wnt-10b -------------------
wnts = np.linspace(-1, 50, 100)
ratio_po_ob, ratio_oc_ob = [], []
for w in wnts:
    t, y = simulate_cycles(w, 1)
    a_po = trapz(y[:, 1], t)
    a_ob = trapz(y[:, 2], t)
    a_oc = trapz(y[:, 3], t)
    ratio_po_ob.append(a_po / a_ob)
    ratio_oc_ob.append(a_oc / a_ob)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].plot(wnts, ratio_po_ob, color="C0", lw=2)
axes[0].set_ylabel("pre-osteoblast : osteoblast AUC")
axes[0].set_title("A")
axes[1].plot(wnts, ratio_oc_ob, color="C3", lw=2)
axes[1].set_ylabel("osteoclast : osteoblast AUC")
axes[1].set_title("B")
for ax in axes:
    ax.set_xlabel("Wnt-10b (fold change)")
fig.suptitle("Cook et al. 2022 Fig. 6 - cell-population AUC ratios vs Wnt-10b")
save("fig6_auc_ratios.png")
