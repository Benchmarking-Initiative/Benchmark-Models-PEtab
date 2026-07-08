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

These two points are included in the PEtab measurement table (experiment
`exp_Wnt_1_8`, dataset ids `RoserPage2014_*`) so the validation figure can be
reproduced. Unlike the Bennett fitting data (fixed unit noise), the validation
points carry their **reported standard deviations** (19.2, 40.6) as
`noiseParameters`. Because these SDs are large relative to the unit-noise
Bennett residuals, the validation points contribute negligibly to the objective
and the fit (see below) is still effectively determined by the Bennett data
alone, matching the original study where Roser-Page was held out for
validation.

## PEtab problem

PEtab v2 (`format_version: 2.0.0`). The files are:

* **Conditions** (`conditions_Cook_AIChE2022.tsv`): the Wnt-10b dose conditions
  `Wnt_m1`, `Wnt_5`, `Wnt_50`, `Wnt_1_8` (each sets the `Wnt` parameter) and the
  `cycle_reset` condition that performs the cycle-boundary state reset (below).
* **Experiments** (`experiments_Cook_AIChE2022.tsv`): one timecourse per Wnt-10b
  dose (`exp_Wnt_m1`, `exp_Wnt_5`, `exp_Wnt_50`, `exp_Wnt_1_8`). Each starts at
  `t = 0` with the dose condition and then applies `cycle_reset` at every 100-day
  boundary (`t = 100, 200, ...`) up to the number of cycles required by that
  experiment's measurements.
* **Observable** (`observables`): `obs_BV = Bone_volume__z - 100`, the relative
  BV/TV change. The paper fits with unweighted least squares; this is
  reproduced with a fixed unit noise (`normal`), so the objective equals the
  residual sum of squares up to a constant.
* **Estimated parameters** (`parameters`): the four Wnt-10b-related parameters
  `beta1adj`, `alpha3adj`, `beta2adj`, `K`. (PEtab v2 has no `parameterScale`
  column; the bounds are given on linear scale.)

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
at the measurement times. This period-wise formulation is numerically identical
(to solver tolerance) to the earlier SBML-event encoding.

> Earlier revisions of this problem (PEtab v1) encoded the same reset as 11
> time-triggered SBML events at `t = 100, ..., 1100`. Moving it into the
> experiment/condition tables is the PEtab v2 idiom and keeps the model itself
> a plain, reusable ODE system.

## Nominal parameters

Taken from the publication's final fit (the parameter set used to generate the
paper figures in `GraphsforPaper.m`, "after the 4th data point was added"):

| parameter | nominal | note |
|-----------|--------:|------|
| `beta1adj`  | 0.177617716487146    | `= k1` |
| `alpha3adj` | 0.260931032760533    | `= k1 + k2` |
| `beta2adj`  | 0.000709650034656732 | `= k3` |
| `K`         | 6.26349707992014     | `= k4` |

## Differences from the original publication

* **Reparameterization.** The MATLAB code estimates `k1..k4` with
  `alpha3adj = k1 + k2`. Here `beta1adj, alpha3adj, beta2adj, K` are estimated
  directly (they are already SBML parameters); this is an equivalent
  parameterization of the same 4-parameter space.
* **Multiple cycles via PEtab experiments** (see above): the cycle-boundary
  reset is applied through the experiment/condition tables rather than the
  sequential re-initialized integrations of the MATLAB code.
* The `parameters` values in the shipped SBML export are corrected: its
  `beta1adj = 0.0833` is in fact the value of `k2`; the nominal values here use
  the published `k1..k4`.
* The reaction kinetics match the shipped SBML export, which omits the
  `max(1 - S/K_S, 0)` clamp present in the MATLAB code; the two agree because
  `S < K_S` throughout the simulated trajectories.

## Fitting notes

The nominal fit was obtained in the original study with MATLAB `lsqcurvefit`
(Levenberg-Marquardt) from Latin-hypercube / normally-distributed multistarts.
It is a least-squares compromise across the four data points rather than an
exact interpolation (residual sum of squares ~278 in BV/TV-% units). The
`Wnt_50 / 12-cycle` point is reproduced almost exactly.

## Reproducing the figures

`make_figures.py` reads the PEtab v2 problem and simulates the event-free model
cycle-by-cycle with libroadrunner, applying the `cycle_reset` condition at each
100-day boundary exactly as the experiment table prescribes:

```bash
python make_figures.py   # requires petab (v2), libroadrunner, matplotlib, numpy
```

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
with the 1.2–2.4 fold-change envelope shaded, compared with the two independent
Roser-Page BV/TV endpoints (held out from the fit). Both data points lie on the
simulated trajectory.

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
ratios over a single remodeling cycle as a function of the Wnt-10b fold change;
both ratios decrease with increasing Wnt-10b.

![AUC ratios](fig6_auc_ratios.png)
