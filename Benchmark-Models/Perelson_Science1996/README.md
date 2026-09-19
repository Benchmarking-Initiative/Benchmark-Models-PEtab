# Implementation details of the Perelson_Science1996 benchmark problem

## Model

Linear three-state model of HIV-1 dynamics in vivo under a protease inhibitor
[[1]]. Ritonavir renders newly produced virions non-infectious but does not stop
production by already infected cells, so the plasma virion population splits
into an infectious pool present when the drug took effect and a non-infectious
pool produced afterwards:

```
d(Tstar)/dt = k*T0*V_I  -  delta*Tstar        (Eq. 3)
d(V_I)/dt   = -c*V_I                          (Eq. 4)
d(V_NI)/dt  = N_virions*delta*Tstar  -  c*V_NI        (Eq. 5)
V           = V_I + V_NI
```

The concentration of uninfected target cells is held at its pre-treatment value
`T0`, and the drug is assumed to be 100 % effective.

| id | paper | meaning |
|----|-------|---------|
| `Tstar` | *T\** | productively infected cells |
| `V_I`   | *V_I*  | infectious virions, present when the drug took effect |
| `V_NI`  | *V_NI* | non-infectious virions, produced after the drug took effect |
| `V`     | *V*    | total plasma viral load; the measured quantity |
| `c`     | *c*    | virion clearance rate [1/day] |
| `delta` | *δ*    | loss rate of virus-producing cells [1/day] |
| `V0`    | *V_0*  | viral load when the drug took effect [RNA copies/ml] |
| `N_virions` | *N* | virions produced per infected cell over its lifetime |
| `T0`    | *T_0*  | pre-treatment concentration of uninfected target cells |
| `k`     | *k*    | infection rate constant |

`Tstar` is spelled without an asterisk because SBML identifiers cannot contain
one. The burst size is `N_virions` rather than `N` because `N` is the name of
SymPy's numeric-evaluation function, and AMICI parses SBML initial assignments
through SymPy — a parameter called `N` makes the model fail to import.

## The estimation problem

A single condition, `condition1`, no pre-equilibration, and one observable,
`patient_105`, which is `V` with a `log10` transformation and normally
distributed noise — that is, residuals are normal in `log10` space. The
measurement table holds 13 plasma HIV-1 RNA concentrations over 6.75 days.

Three parameters are estimated, all on a `log10` scale: `c`, `delta` and `V0`.
These are exactly the three that [[1]] states were estimated simultaneously, and
their nominal values are the ones published for this patient. `N_virions = 480`
and `T0 = 11000` are fixed.

There is no noise parameter: the observable table gives `noiseFormula` as the
literal `1`, so the objective is the unweighted sum of squared `log10`
residuals — the nonlinear least squares problem solved in [[1]]. That 1 is a
weighting convention rather than an estimate of the measurement noise; since
the observable is `log10`-transformed it would be a residual width in `log10`
units, and the root mean square `log10` residual at the optimum is 0.117.
Weighting the residuals equally does not bias the estimates: with a single
observable and one shared noise level, estimating that level instead would
profile out to a strictly monotone function of the same sum of squares, giving
the same optimum in `c`, `delta` and `V0`.

## Data

The measurements are the raw plasma HIV-1 RNA concentrations (copies/ml) of
**patient 105** of [[1]], taken from Hulin Wu's *Early intensive viral dynamic
data* release [[2]], where this patient carries `ID = 4`.

Table 1 of [[1]] reports base-line plasma **virions**/ml and states that each
virion carries two RNA copies, whereas the release reports RNA copies/ml.
Halving the day-0 release values reproduces the Table 1 base lines for all five
patients, in ascending order of ID, which is how the release IDs map onto the
patient numbers used in the publication:

| release ID | RNA/ml at day 0 | → virions/ml | patient | Table 1 base line | ratio |
|-----------:|----------------:|-------------:|--------:|------------------:|------:|
| 1 |   610,000 | 305,000 | 102 | 294,000 | 1.04 |
| 2 |    19,000 |   9,500 | 103 |  12,000 | 0.79 |
| 3 |   100,000 |  50,000 | 104 |  52,000 | 0.96 |
| 4 | 1,022,000 | 511,000 | 105 | 643,000 | 0.80 |
| 5 |   160,000 |  80,000 | 107 |  77,000 | 1.04 |

The residual spread is expected: the Table 1 base lines are averages over days
−7, −4, −1 and 0, while the release starts at day 0. Three of the five
assignments are confirmed independently by Fig. 1 of [[1]], which plots the
released series point for point: Fig. 1A upper is patient 104, Fig. 1A lower is
patient 107, and Fig. 1B is patient 105.

## Time base

Time is measured **from the onset of the drug effect, not from dosing**. The
two differ by a pharmacologic delay, 6 h = 0.25 d for patient 105, measured for
this patient from the first drop in plasma infectivity (Table 1 of [[1]] and its
legend). The model has no validity before that onset, so the three measurements
taken earlier — released days 0, 0.083 and 0.166 — are not part of the problem,
and 0.25 d has been subtracted from the sampling times of the remaining 13.

## Initial conditions

Only `V0` is free; the other initial values follow from the pre-treatment quasi
steady state assumed in [[1]] and are encoded as SBML initial assignments, so
they track `V0`, `c` and `delta` as those are estimated:

| state | initial value | origin |
|-------|---------------|--------|
| `V_I`   | `V0`               | Eq. 4, `V_I(0) = V0` |
| `V_NI`  | `0`                | Eq. 5, no virions produced under the drug yet |
| `V`     | `V0`               | `V = V_I + V_NI` |
| `Tstar` | `c*V0/(N_virions*delta)`   | `dV/dt = 0` at steady state (Eqs. 1–2) |

The same steady state fixes the infection rate constant, `c = N_virions*k*T0`,
so `k` is likewise an initial assignment, `c/(N_virions*T0)`, and not a free
parameter. This matters because `c` is estimated: holding `k` at a literal value
would let the model drift away from Eq. 6 of [[1]] as `c` moves — by up to 13 %
at `c = 1.5` — whereas with `k` coupled the model reproduces Eq. 6 at any
parameter value.

`T0` cancels out of the dynamics under that coupling (`k*T0 = c/N_virions`). It
is kept as a fixed parameter because [[1]] reports it and because the coupling is
clearer written with it.

## Validation

`simulate_Perelson_Science1996.py` in this directory simulates the problem with
AMICI at the nominal parameter values and writes
`simulatedData_Perelson_Science1996.tsv`, so the simulated-data table can be
regenerated rather than taken on trust. Those simulations agree with the
closed-form solution, Eq. 6 of [[1]], to a relative 2e-8 at AMICI's default
tolerances.

Re-estimating `c`, `delta` and `V0` from the measurement table recovers the
values published for patient 105:

| | `c` | `delta` | `V0` |
|---|---|---|---|
| published (Table 1) | 2.06 | 0.53 | 1.86e6 |
| re-estimated here | 2.062 | 0.525 | 1.832e6 |

The nominal parameters therefore sit essentially at the optimum: the sum of
squared `log10` residuals is 0.1775 at the nominal values and 0.1771 at the
optimum.

## Deviations from the publication

- [[1]] eliminated one outlying data point per patient by a jackknife procedure
  before fitting. That step is not reproduced here; it is not needed to recover
  the published parameter values.

[1]: https://doi.org/10.1126/science.271.5255.1582
[2]: https://sph.uth.edu/dept/bads/faculty-home/hulinwu/datasets/early-intensive-viral-dynamic-data
