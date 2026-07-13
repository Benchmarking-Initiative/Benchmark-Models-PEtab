# Cook_AIChE2022

PEtab implementation of the bone-remodeling model of

> C. V. Cook, M. A. Islam, B. J. Smith, A. N. Ford Versypt.
> *Mathematical Modeling of the Effects of Wnt-10b on Bone Metabolism.*
> AIChE Journal, 2022, 68(12), e17809. doi:[10.1002/aic.17809](https://doi.org/10.1002/aic.17809)

Original model, data and MATLAB code: https://github.com/ashleefv/Wnt10bBoneCompartment
Additional background: C. V. Cook, *Mathematical Modeling to Connect Bone
Responses to Systemic Mechanisms* (PhD thesis).

This is a **PEtab v2** problem (`format_version: 2.0.0`). The repeated
remodeling cycles are encoded in the PEtab experiment/condition tables rather
than in the SBML model (see below).

## Model

A compartmental ODE model of a bone multicellular unit over repeated
remodeling cycles. Five species are tracked: osteocytes (`S`),
pre-osteoblasts (`P`), osteoblasts (`B`), osteoclasts (`C`) and relative
bone volume (`z`, in % of the normal value, starting at 100). Wnt-10b enters
the system through a Hill-type factor `piwnta = Wnt / (Wnt + K)` that modulates
pre-osteoblast proliferation, pre-osteoblast-to-osteoblast differentiation and
osteoblast apoptosis.

## Data

Four bone-volume-fraction (BV/TV) measurements compiled in the paper from
Wnt-10b transgenic / knockout mouse experiments (Bennett et al. 2005, 2007),
expressed as percentage change relative to normal Wnt-10b:

| condition | Wnt-10b fold change | remodeling cycles | time [d] | BV/TV change [%] | source |
|-----------|--------------------:|------------------:|---------:|-----------------:|--------|
| `Wnt_m1`  | -1  | 4  | 400  | -29.7 | Bennett 2005 |
| `Wnt_m1`  | -1  | 6  | 600  | -41.9 | Bennett 2007 |
| `Wnt_5`   | 5   | 6  | 600  |  69.2 | Bennett 2007 |
| `Wnt_50`  | 50  | 12 | 1200 | 339.0 | Bennett 2005 |

### Validation data (Roser-Page 2014)

The paper additionally *validates* the fitted model against an independent
dataset that was **not** used for parameter estimation: the CTLA-4Ig
(abatacept) mouse experiments of Roser-Page et al. 2014, which correspond to a
Wnt-10b fold change of ~1.8 (with a 1.2–2.4 range). The two BV/TV endpoints are
reproduced here from the paper's validation figure (`ValidationResults` in the
original `GraphsforPaper.m`):

| condition | Wnt-10b fold change | remodeling cycles | time [d] | BV/TV change [%] | SD  | source |
|-----------|--------------------:|------------------:|---------:|-----------------:|----:|--------|
| `Wnt_1_8` | 1.8 | 6  | 600  | 26.6 | 19.2 | Roser-Page 2014 |
| `Wnt_1_8` | 1.8 | 12 | 1200 | 36.6 | 40.6 | Roser-Page 2014 |

> Reference: S. Roser-Page et al., *CTLA-4Ig-induced T cell anergy promotes
> Wnt-10b production and bone formation in a mouse model*, Arthritis &
> Rheumatology, 2014, 66(4), 990–999. doi:[10.1002/art.38319](https://doi.org/10.1002/art.38319)

These two points are kept in a **separate** measurement table
(`measurementData_validation_Cook_AIChE2022.tsv`, experiment `exp_Wnt_1_8`,
dataset ids `RoserPage2014_*`) that is **not** referenced by the problem YAML,
so they are held out of parameter estimation — matching the original study,
where Roser-Page was used only for validation. Their reported standard
deviations (19.2, 40.6) are carried in that table purely as error bars for the
validation figure; they are not used as PEtab noise.

## PEtab problem

PEtab v2 (`format_version: 2.0.0`). The files are:

* **Conditions** (`conditions_Cook_AIChE2022.tsv`): the Wnt-10b dose conditions
  `Wnt_m1`, `Wnt_5`, `Wnt_50`, `Wnt_1_8` (each sets the `Wnt` parameter and
  `alpha3adj = beta1adj + k2adj`, see *Differences* below) and the `cycle_reset`
  condition that performs the cycle-boundary state reset (below).
* **Experiments** (`experiments_Cook_AIChE2022.tsv`): one timecourse per Wnt-10b
  dose (`exp_Wnt_m1`, `exp_Wnt_5`, `exp_Wnt_50`, `exp_Wnt_1_8`). Each starts at
  `t = 0` with the dose condition and then applies `cycle_reset` at every 100-day
  boundary (`t = 100, 200, ...`) up to the number of cycles required by that
  experiment's measurements.
* **Observable** (`observables`): `obs_BV = Bone_volume__z - 100`, the relative
  BV/TV change. The paper fits with unweighted least squares; this is
  reproduced with a fixed unit noise (`noiseFormula = 1`, `normal`), so the
  objective equals the residual sum of squares up to a constant.
* **Estimated parameters** (`parameters`): the four Wnt-10b-related parameters
  `beta1adj`, `k2adj`, `beta2adj`, `K`, with `alpha3adj = beta1adj + k2adj`
  derived via the condition table so that `alpha3adj > beta1adj` holds during
  fitting (see *Differences from the original publication*). (PEtab v2 has no
  `parameterScale` column; the bounds are given on linear scale.)

### Multiple remodeling cycles as PEtab experiments

The number of remodeling cycles is the key feature of the original model, and
the SBML export shipped with the paper explicitly *does not* support it. In the
MATLAB code each 100-day cycle is integrated separately and the state is reset
at the cycle boundary: cell populations that have decayed below 1 are set to 0
and the osteocyte count is reduced by 20 to initiate the next cycle.

Here this reset is expressed as the PEtab `cycle_reset` **condition**

```
cycle_reset  Osteocytes__S      Osteocytes__S - 20
cycle_reset  Pre_Osteoblasts__P piecewise(0, Pre_Osteoblasts__P < 1, Pre_Osteoblasts__P)
cycle_reset  Osteoblasts__B     piecewise(0, Osteoblasts__B < 1, Osteoblasts__B)
cycle_reset  Osteoclasts__C     piecewise(0, Osteoclasts__C < 1, Osteoclasts__C)
```

which each experiment applies at `t = 100, 200, ...` via the experiment table.
The SBML model contains **no events**; the periods of the experiment define the
cycle boundaries. Crucially, bone volume `z` is **not** reset, so it is
continuous across cycle boundaries and the `z`-based observable is unambiguous
at the measurement times. Keeping the reset in the experiment/condition tables
leaves the model itself a plain, reusable ODE system.

### Simulation

The problem imports and simulates with AMICI (`src/python/simulate.py`); AMICI
encodes the experiment periods as events internally. The cycle-boundary state
change makes the system stiff, so the AMICI **absolute tolerance must be
loosened from its very tight default (`1e-16`) to about `1e-12`** — with the
default `atol` the solver reports a too-small step after the reset. The
`simulatedData` table was generated with AMICI at `rtol = 1e-10`, `atol = 1e-12`
(total log-likelihood ≈ -143.38 over the four fitting measurements at the
nominal parameters).

## Nominal parameters

Taken from the publication's final fit (the parameter set used to generate the
paper figures in `GraphsforPaper.m`, "after the 4th data point was added"):

| parameter | nominal | note |
|-----------|--------:|------|
| `beta1adj`  | 0.177617716487146    | `= k1` |
| `k2adj`     | 0.083313316273387    | `= k2`; `alpha3adj = beta1adj + k2adj = k1 + k2` |
| `beta2adj`  | 0.000709650034656732 | `= k3` |
| `K`         | 6.26349707992014     | `= k4` |

## Differences from the original publication

* **Estimated parameters and the `alpha3adj > beta1adj` constraint.** The MATLAB
  code estimates `k1..k4` with `beta1adj = k1`, `beta2adj = k3`, `K = k4` and
  `alpha3adj = k1 + k2`, so `alpha3adj > beta1adj` (because `k2 > 0`). To keep
  that constraint during fitting, the estimated parameters here are `beta1adj`,
  `k2adj` (`= k2`, lower bound > 0), `beta2adj` and `K`, and `alpha3adj` is
  derived as `alpha3adj = beta1adj + k2adj` via the condition table rather than
  estimated independently. This also corrects the shipped SBML export, whose
  `beta1adj = 0.0833` is in fact the value of `k2` (the nominal `k2adj` here).
* **Multiple remodeling cycles** are applied through the experiment/condition
  tables rather than the MATLAB code's sequential re-initialized integrations
  (see *Multiple remodeling cycles as PEtab experiments* above).
* The reaction kinetics match the shipped SBML export, which omits the
  `max(1 - S/K_S, 0)` clamp present in the MATLAB code. It has no effect on the
  nominal trajectories (`S` stays below `K_S`); whether it matters under fitting,
  where the parameters vary and `S` could exceed `K_S`, remains to be verified.

## Fitting notes

The nominal fit was obtained in the original study with MATLAB `lsqcurvefit`
(Levenberg-Marquardt) from Latin-hypercube / normally-distributed multistarts.
It is a least-squares compromise across the four data points (residual sum of
squares ~279 in BV/TV-% units); the `Wnt_50 / 12-cycle` point is reproduced
almost exactly.

## Reproducing the figures

`make_figures.py` simulates the PEtab problem itself with **AMICI**: the problem
is imported with AMICI's PEtab importer (which encodes the experiment periods as
events) and each of the four dose experiments is simulated with dense output so
that AMICI applies the `cycle_reset` condition at every 100-day boundary. Every
figure is derived from those four experiments.

```bash
python make_figures.py   # requires petab (v2), amici, matplotlib, numpy>=2
```

Because the problem only contains the four fold changes -1, 1.8, 5 and 50, two
figures are reduced relative to the publication: Figure 4 omits the 1.2–2.4
envelope, and Figure 6 shows the AUC ratios at the four available fold changes
as discrete points rather than a continuous sweep.

### Figure 1 — dose-response
Simulation (filled circles) vs Bennett 2005/2007 fitting data and Roser-Page
2014 validation data (crosses).

![dose-response validation](fig1_validation_doseresponse.png)

### Figure 2 — relative bone volume over remodeling cycles
The sawtooth trajectory (resorption dip then formation rebound each cycle) for
Wnt-10b fold changes -1, 5 and 50, with the literature endpoints overlaid.

![bone volume vs time](fig2_bone_volume_vs_time.png)

### Figure 3 — cell-population dynamics (Wnt-10b fold change 50)
Osteocyte, pre-osteoblast, osteoblast and osteoclast counts across the 12 cycles.

![cell populations](fig3_cell_populations_Wnt50.png)

The following three figures use the **numbering of the original publication**.

### Figure 4 — model validation against Roser-Page 2014 data
Relative bone volume over 12 remodeling cycles at a Wnt-10b fold change of 1.8,
compared with the two independent Roser-Page BV/TV endpoints (held out from the
fit). Both data points lie on the simulated trajectory. (The publication's
1.2–2.4 fold-change envelope is omitted: those fold changes are not experiments
in the PEtab problem.)

![validation vs Roser-Page](fig4_validation_roserpage.png)

### Figure 5 — activated cell-population dynamics over a single remodeling cycle
Osteocyte, pre-osteoblast, osteoblast and osteoclast time courses for Wnt-10b
fold changes -1, 5 and 50: (A) osteocytes change little with Wnt-10b, (B)
pre-osteoblasts increase slightly, (C) osteoblasts increase, and (D) osteoclasts
decrease with increasing Wnt-10b. Populations settle well before the 100-day
cycle boundary.

![cell dynamics over a single cycle](fig5_cell_dynamics_single_cycle.png)

### Figure 6 — cell-population AUC ratios vs Wnt-10b
Pre-osteoblast:osteoblast (A) and osteoclast:osteoblast (B) area-under-curve
ratios over a single remodeling cycle, at the four fold changes present in the
problem (-1, 1.8, 5, 50); both ratios decrease with increasing Wnt-10b. (The
publication shows a continuous fold-change sweep, which is not available from
the problem's discrete experiments.)

![AUC ratios](fig6_auc_ratios.png)
