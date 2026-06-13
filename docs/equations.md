# Baseline Equations

All equations are idealized starting points. Their output evidence class is
`theoretical_limit` unless empirical derating factors are supplied from cited
measurements.

## Theoretical Specific Capacity

For a reaction transferring \(n_e\) electrons per reaction basis:

\[
Q_{\mathrm{th}} = \frac{n_e F}{3.6 M}
\]

where \(F = 96485.33212\ \mathrm{C\,mol^{-1}}\), \(M\) is the molar mass in
grams per mole, and \(Q_{\mathrm{th}}\) is numerically in mAh/g (equivalently
Ah/kg).

The mass basis must include every active reactant whose mass is counted. A
cathode-only value must never be labeled as complete-cell specific capacity.

For a declared reaction, the implemented reaction mass basis is:

\[
M_{\mathrm{basis}} =
\sum_{i \in \mathrm{included\ reactants}} \nu_i M_i
\]

The software also compares total reactant and product mass and rejects reference
fixtures outside their declared mass-balance tolerance.

## Theoretical Specific Energy

\[
E_{\mathrm{th}} = Q_{\mathrm{th}} V_{\mathrm{avg}}
\]

where \(V_{\mathrm{avg}}\) is the average discharge voltage. The result is Wh/kg
on the same mass basis as capacity.

For a piecewise voltage profile:

\[
V_{\mathrm{avg}} = \sum_i f_i V_i,
\qquad \sum_i f_i = 1
\]

where \(f_i\) is the fraction of delivered capacity in segment \(i\).

## Gravimetric-to-Volumetric Conversion

\[
E_{\mathrm{vol}} =
E_{\mathrm{grav}}\rho f_{\mathrm{packing}}
\]

The density and packing fraction must refer to the same physical boundary as
the gravimetric value. This conversion does not create a complete electrode,
cell, or pack volume from a material density.

## Deterministic Uncertainty Intervals

For positive independent bounds:

\[
Q_{\mathrm{lower}} =
\frac{F n_{\mathrm{lower}}}{3.6 M_{\mathrm{upper}}},
\qquad
Q_{\mathrm{upper}} =
\frac{F n_{\mathrm{upper}}}{3.6 M_{\mathrm{lower}}}
\]

Positive products use lower-by-lower and upper-by-upper interval bounds. These
are deterministic sensitivity envelopes, not probabilistic confidence intervals.

## Bill-of-Materials Boundaries

\[
E_{\mathrm{cell}} =
E_{\mathrm{active}}
m_{\mathrm{active}}
u_Q
\eta_V
\eta_{\mathrm{cell}}
\]

\[
e_{\mathrm{cell}} =
\frac{E_{\mathrm{cell}}}{m_{\mathrm{cell,total}}}
\]

\[
E_{\mathrm{pack}} =
e_{\mathrm{cell}}
m_{\mathrm{cells}}
\eta_{\mathrm{pack}},
\qquad
e_{\mathrm{pack}} =
\frac{E_{\mathrm{pack}}}{m_{\mathrm{pack,total}}}
\]

Every inactive component remains visible in the mass-fraction output.

## Boundary Derating

\[
E_{\mathrm{cell}} =
E_{\mathrm{active}}
f_{\mathrm{active}}
u_{\mathrm{active}}
\eta_V
\]

\[
E_{\mathrm{pack}} =
E_{\mathrm{cell}}
f_{\mathrm{cell/pack}}
\eta_{\mathrm{pack}}
\]

\[
E_{\mathrm{aircraft,useful}} =
E_{\mathrm{pack}}
f_{\mathrm{pack/installed}}
\mathrm{DoD}
\mathrm{SoH}
f_T
(1-r)
\eta_{\mathrm{powertrain}}
\]

Each factor is dimensionless and constrained to `[0, 1]`. The factors are
reported separately to prevent hidden or double-counted penalties.

## Cruise Energy Lower-Order Model

For steady level flight:

\[
D = \frac{mg}{L/D}
\]

\[
E_{\mathrm{cruise,mech}} = D R
\]

\[
E_{\mathrm{nominal,battery}} =
\frac{E_{\mathrm{cruise,mech}}(1+p_{\mathrm{noncruise}})}
{3600\,\eta_{\mathrm{prop}}\,\mathrm{DoD}\,\mathrm{SoH}\,f_T\,(1-r)}
\]

This is not a certified aircraft-performance model. It omits aerodynamic
variation, climb trajectory, winds, loiter, power limits, thermal transients,
and structural feedback unless represented by explicit factors.

## Phase 3 Segmented Mission Model

For each constant-condition segment:

\[
E_{\mathrm{electrical},i} =
\left(
\frac{P_{\mathrm{mechanical},i}}{\eta_{\mathrm{prop}}}
+ P_{\mathrm{aux}}
\right)t_i
\]

Climb mechanical power includes drag and potential-energy rate:

\[
P_{\mathrm{climb}} =
\frac{mgV}{L/D} + mg\dot{h}
\]

Cruise and reserve-loiter power use steady level drag:

\[
P_{\mathrm{level}} = \frac{mgV}{L/D}
\]

Descent uses a declared fraction of level-flight drag power and gives no credit
for recovered potential energy.

The nominal battery energy required by all mission segments is:

\[
E_{\mathrm{battery,nominal}} =
\frac{\sum_i E_{\mathrm{electrical},i}}
{\mathrm{DoD}\,\mathrm{SoH}\,f_T}
\]

Battery mass is sized by the maximum of three independent constraints:

\[
m_b =
\max\left(
\frac{E_{\mathrm{battery,nominal}}}{e_{\mathrm{pack}}},
\frac{P_{\mathrm{peak}}}{p_{\mathrm{pack}}\mathrm{SoH}f_T},
\frac{P_{\mathrm{peak}}}
{e_{\mathrm{pack}}C_{\max}\mathrm{SoH}f_T}
\right)
\]

Because aircraft mass includes battery mass, the solver iterates:

\[
m_{\mathrm{aircraft}} =
m_{\mathrm{empty,no\ battery}} + m_{\mathrm{payload}} + m_b
\]

Failure to converge, exceedance of maximum takeoff mass, or exceedance of the
configured battery fraction is reported as infeasible rather than suppressed.
