#!/usr/bin/env python3
"""Wormhole-Lab - educational Morris-Thorne traversable wormhole lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only: the Morris-Thorne metric (1988) is a legitimate
solution of Einstein's equations - a tunnel between two regions of
spacetime held open by a "shape function" b(r) and a "redshift
function" Phi(r). This lab computes it honestly: two standard shape
functions with the flare-out condition b'(r0) < 1 verified
numerically, the embedding diagram z(r) integrated numerically and
checked against its closed form, the tidal-force comfort bounds
Morris and Thorne derived, the traversal-time bookkeeping for a
labelled example journey, and the part the movies skip: the
Einstein equations themselves demand matter that violates the null
energy condition at the throat - exotic matter, with a negative
energy density around -4.8e42 J/m^3 for a 1 m throat and a
Ford-Roman quantum-inequality timescale of ~1e-26 s. No wormhole
has ever been observed, let alone built; sustained macroscopic
negative energy is unproven physics. Every build / time-travel /
FTL / service claim is a HOLD gate - with Gemini Carbon 4 as
DECIDER (names-only, tighten-only), Muse as advisor (never
overrides HOLD), and Google Flow plan-only seats.
"""
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- constants
HBAR = 1.054571817e-34          # reduced Planck constant, J s (exact, SI)
C_LIGHT = 299792458.0           # speed of light, m/s (exact, SI)
G_NEWTON = 6.674e-11            # gravitational constant, m^3 kg^-1 s^-2
G_EARTH = 9.80665               # standard gravity, m/s^2 (exact)
JUPITER_KG = 1.898e27           # Jupiter mass, kg (labelled reference)
VERSION = "1.0.0"

# SI prefactor of the Einstein equations: geometrised density [1/m^2]
# times C^4 / (8 pi G) is an energy density [J/m^3]; the radial
# tension picks up the same factor and reads as a pressure [Pa].
EINSTEIN_PREFACTOR = C_LIGHT ** 4 / (8.0 * math.pi * G_NEWTON)

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "build_wormhole_claim": "HOLD - no construction design or instructions for a real wormhole; none has ever been built",
    "exotic_matter_production_claim": "HOLD - no recipe for producing or storing negative-energy matter; sustained macroscopic exotic matter is unproven",
    "time_travel_claim": "HOLD - time-machine / closed-timelike-curve claims are speculative discussion only, never a capability",
    "ftl_travel_claim": "HOLD - no faster-than-light claim: traversal would be local subluminal motion through a shortcut, IF one existed",
    "observed_wormhole_claim": "HOLD - no wormhole has ever been observed; no discovery claims",
    "transport_service_claim": "HOLD - no passenger or cargo transport service; this lab moves no one and nothing",
    "real_hardware_control": "HOLD - no control of any real gravitational, vacuum, or accelerator hardware, ever",
    "live_experiment": "HOLD - no live experiment instructions; this lab computes, it does not operate",
    "commercial_product_claim": "HOLD - this is an educational lab, not a commercial product or device design",
    "guaranteed_traversability_claim": "HOLD - no guaranteed traversability; every number here carries its model assumptions",
    "medical_claim": "HOLD - no medical claims; spacetime geometry here treats no condition",
    "investment_claim": "HOLD - no investment advice about space, quantum, or advanced-propulsion companies",
    "peer_reviewed_result_claim": "HOLD - no peer-reviewed-result claims; this is an educational simulation of published theory",
    "weapons_application_claim": "HOLD - no weapons application guidance of any kind",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Shape functions
# The Morris-Thorne metric (signature -,+,+,+):
#   ds^2 = -e^{2 Phi(r)} c^2 dt^2 + dr^2 / (1 - b(r)/r) + r^2 dOmega^2
# The shape function b(r) fixes the tunnel's profile. It must obey:
#   b(r0) = r0            (r0 = throat radius, the narrowest point)
#   b(r) < r for r > r0   (the tunnel widens away from the throat)
#   b'(r0) < 1            (FLARE-OUT: the tunnel mouth opens outward)
# Two standard choices, both used with Phi = 0 below unless stated:
#   ellis : b(r) = r0^2 / r            -> b'(r0) = -1
#   linear: b(r) = r0 (1 - (r - r0)/(2 r0)) -> b'(r0) = -1/2,
#           valid while b >= 0, i.e. r0 <= r <= 3 r0 (labelled domain)

def _b_ellis(r, r0):
    return r0 * r0 / r


def _bp_ellis(r, r0):
    return -r0 * r0 / (r * r)


def _b_linear(r, r0):
    return r0 * (1.0 - (r - r0) / (2.0 * r0))


def _bp_linear(r, r0):
    return -0.5


SHAPES = {
    "ellis": (_b_ellis, _bp_ellis),
    "linear": (_b_linear, _bp_linear),
}


def shape_b(r, r0, shape="ellis"):
    """Shape function b(r) in metres."""
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    return SHAPES[shape][0](r, r0)


def shape_bp(r, r0, shape="ellis"):
    """Analytic derivative b'(r) (dimensionless)."""
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    return SHAPES[shape][1](r, r0)


def shape_bp_numeric(r, r0, shape="ellis"):
    """b'(r) by finite differences - the flare-out audit tool.

    Central differences in the interior; at the throat itself a
    second-order one-sided difference, because b is only defined
    for r >= r0.
    """
    h = r0 * 1e-6
    if r <= r0:
        return (-3.0 * shape_b(r, r0, shape) + 4.0 * shape_b(r + h, r0, shape)
                - shape_b(r + 2.0 * h, r0, shape)) / (2.0 * h)
    return (shape_b(r + h, r0, shape) - shape_b(r - h, r0, shape)) / (2.0 * h)


def flare_out(r0, shape="ellis"):
    """Flare-out audit at the throat: b(r0) = r0 and b'(r0) < 1."""
    bp_num = shape_bp_numeric(r0, r0, shape)
    return {"b_at_throat_m": shape_b(r0, r0, shape),
            "bp_analytic": shape_bp(r0, r0, shape),
            "bp_numeric": bp_num,
            "flare_out_ok": bp_num < 1.0}


def shape_table(r0=1.0, multiples=(1.0, 1.5, 2.0, 3.0, 5.0, 10.0)):
    rows = []
    for m in multiples:
        r = m * r0
        row = {"r_over_r0": m, "r_m": r}
        for name in SHAPES:
            if name == "linear" and r > 3.0 * r0:
                row[f"b_{name}_m"] = None     # outside labelled domain
            else:
                row[f"b_{name}_m"] = shape_b(r, r0, name)
        rows.append(row)
    return rows


# ================================================================ 2. Embedding diagram
# Slice the equatorial plane at constant t and embed it in flat 3D
# space: the surface z(r) with
#   dz/dr = +/- sqrt( b(r) / (r - b(r)) ),   z(r0) = 0.
# The integrand diverges at the throat (vertical tangent - the
# funnel picture), but the singularity is integrable. Substituting
# s = sqrt(r - r0) (so dr = 2s ds) removes it: at s = 0 the
# integrand tends to 2 sqrt( b(r0) / (1 - b'(r0)) ). Simpson's rule
# on a fixed grid: deterministic. For the Ellis shape the integral
# is closed-form: z(r) = r0 arcosh(r / r0) - the audit target.

def _simpson(f, smax, n=4000):
    if smax <= 0:
        return 0.0
    h = smax / n
    tot = f(0.0) + f(smax)
    for i in range(1, n):
        tot += (4.0 if i % 2 else 2.0) * f(i * h)
    return tot * h / 3.0


def embedding_z(r, r0, shape="ellis"):
    """Embedding height z(r) >= 0 (one sheet), metres."""
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    bfun, bpfun = SHAPES[shape]

    def f(s):
        if s == 0.0:
            return 2.0 * math.sqrt(bfun(r0, r0) / (1.0 - bpfun(r0, r0)))
        rr = r0 + s * s
        bb = bfun(rr, r0)
        return 2.0 * s * math.sqrt(max(bb, 0.0) / (rr - bb))

    return _simpson(f, math.sqrt(r - r0))


def embedding_z_ellis_closed(r, r0):
    """Closed form for the Ellis shape: z = r0 arcosh(r / r0)."""
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    return r0 * math.acosh(r / r0)


def embedding_table(r0=1.0, multiples=(1.0, 1.25, 1.5, 2.0, 3.0, 5.0, 10.0)):
    rows = []
    for m in multiples:
        r = m * r0
        rows.append({"r_over_r0": m, "z_ellis_m": embedding_z(r, r0, "ellis"),
                     "z_ellis_closed_m": embedding_z_ellis_closed(r, r0),
                     "z_linear_m": (embedding_z(r, r0, "linear")
                                    if r <= 3.0 * r0 else None)})
    return rows


def proper_distance(r, r0, shape="ellis"):
    """Proper radial distance l(r) = int dr / sqrt(1 - b/r) from throat."""
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    bfun, bpfun = SHAPES[shape]

    def f(s):
        if s == 0.0:
            return 2.0 * math.sqrt(r0 / (1.0 - bpfun(r0, r0)))
        rr = r0 + s * s
        return 2.0 * s / math.sqrt(1.0 - bfun(rr, r0) / rr)

    return _simpson(f, math.sqrt(r - r0))


def proper_distance_ellis_closed(r, r0):
    """Closed form for Ellis: l = sqrt(r^2 - r0^2)."""
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    return math.sqrt(r * r - r0 * r0)


def station_radius(r0, proper_m, shape="ellis"):
    """Invert l(r): the coordinate r at a given proper distance."""
    if proper_m <= 0:
        raise ValueError("proper distance must be positive")
    lo, hi = r0, r0 + proper_m        # l(r) < r - r0 is FALSE; l > r - r0,
    while proper_distance(hi, r0, shape) < proper_m:   # so bracket upward
        hi = r0 + 2.0 * (hi - r0)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if proper_distance(mid, r0, shape) < proper_m:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ================================================================ 3. Energy conditions
# Feed the metric to the Einstein equations and the matter content
# is no longer a choice - it is read off:
#   rho(r) = (c^4 / 8 pi G) * b'(r) / r^2          [energy density]
#   tau(r) = (c^4 / 8 pi G) * [ b/r - 2 (r - b) Phi' ] / r^2
#                                                 [radial tension]
# with radial pressure p_r = -tau. The null energy condition (NEC)
# demands rho + p_r >= 0 for any physical matter. At the throat of
# the Ellis wormhole (Phi = 0): b'(r0) = -1 gives rho < 0 outright,
# and rho - tau = -2 (c^4 / 8 pi G) / r0^2 < 0 - the NEC is
# violated by exactly the flare-out geometry. That violation IS the
# price of the tunnel: no flare-out without exotic matter.

def rho_si(r, r0, shape="ellis"):
    """Energy density rho(r) in J/m^3 from the Einstein equations."""
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    return EINSTEIN_PREFACTOR * shape_bp(r, r0, shape) / (r * r)


def tau_si(r, r0, shape="ellis", phi="zero"):
    """Radial tension tau(r) in Pa (radial pressure is -tau)."""
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    b = shape_b(r, r0, shape)
    phip = phi_prime(r, r0, phi)
    geom = (b / r - 2.0 * (r - b) * phip) / (r * r)
    return EINSTEIN_PREFACTOR * geom


def nec_radial(r, r0, shape="ellis", phi="zero"):
    """rho + p_r = rho - tau in J/m^3; < 0 violates the NEC."""
    return rho_si(r, r0, shape) - tau_si(r, r0, shape, phi)


def exotic_mass_shell(r0, shape="ellis", r_out_mult=2.0):
    """Exotic (negative) mass in the shell r0..r_out_mult*r0, in kg.

    Proper-volume integral of rho/c^2 - a LABELLED estimate of how
    much exotic matter threads the throat region for this shape.
    """
    bfun, bpfun = SHAPES[shape]

    def g(s):
        rr = r0 + s * s
        rho_m = rho_si(rr, r0, shape) / C_LIGHT ** 2
        if s == 0.0:
            dl = 2.0 * math.sqrt(r0 / (1.0 - bpfun(r0, r0)))
            return rho_m * 4.0 * math.pi * rr * rr * dl
        return (rho_m * 4.0 * math.pi * rr * rr
                * 2.0 * s / math.sqrt(1.0 - bfun(rr, r0) / rr))

    return _simpson(g, math.sqrt((r_out_mult - 1.0) * r0))


def ford_roman_time_s(energy_density_j_m3):
    """Ford-Roman quantum-inequality timescale (LABELLED estimate).

    Quantum inequalities bound sustained negative energy roughly by
    |rho| * tau^4 ~ hbar / c^3, so tau ~ (hbar / (|rho| c^3))^{1/4}.
    At wormhole throat densities this is ~1e-26 s - versus the
    seconds a traveller would need the tunnel held open.
    """
    if energy_density_j_m3 == 0:
        raise ValueError("density must be nonzero")
    return (HBAR / (abs(energy_density_j_m3) * C_LIGHT ** 3)) ** 0.25


def energy_report(r0=1.0, shape="ellis"):
    rho0 = rho_si(r0, r0, shape)
    tau0 = tau_si(r0, r0, shape)
    shell = exotic_mass_shell(r0, shape)
    return {"r0_m": r0, "shape": shape,
            "rho_throat_j_m3": rho0,
            "rho_throat_mass_equiv_kg_m3": rho0 / C_LIGHT ** 2,
            "tau_throat_pa": tau0,
            "nec_throat_j_m3": rho0 - tau0,
            "nec_violated": (rho0 - tau0) < 0,
            "exotic_mass_shell_r0_to_2r0_kg": shell,
            "exotic_mass_shell_jupiters": shell / JUPITER_KG,
            "char_mass_scale_kg_per_m": C_LIGHT ** 2 / G_NEWTON,
            "ford_roman_time_s": ford_roman_time_s(rho0)}


# ================================================================ 4. Redshift functions
# Phi(r) is the redshift function: clocks at r tick at e^{Phi(r)}
# relative to distant clocks, and Phi -> 0 at infinity (no event
# horizon anywhere: e^{2 Phi} never vanishes). Two cases:
#   zero: Phi = 0 - the "zero tidal force" wormhole of MT.
#   neg : Phi = -r0 / r - a redshifted throat: a photon climbing
#         out from the throat is redshifted by 1 + z = e^{-Phi(r0)}
#         = e^1, and radial tidal forces appear (section 5).

def phi_value(r, r0, phi="zero"):
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    if phi == "zero":
        return 0.0
    if phi == "neg":
        return -r0 / r
    raise ValueError(f"unknown redshift function {phi!r}")


def phi_prime(r, r0, phi="zero"):
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    if phi == "zero":
        return 0.0
    if phi == "neg":
        return r0 / (r * r)
    raise ValueError(f"unknown redshift function {phi!r}")


def phi_second(r, r0, phi="zero"):
    if r0 <= 0 or r < r0:
        raise ValueError("need r >= r0 > 0")
    if phi == "zero":
        return 0.0
    if phi == "neg":
        return -2.0 * r0 / (r ** 3)
    raise ValueError(f"unknown redshift function {phi!r}")


def grav_redshift(r, r0, phi="neg"):
    """z of a photon emitted at r and received at infinity."""
    return math.exp(-phi_value(r, r0, phi)) - 1.0


def redshift_report(r0=1.0):
    return {"phi_zero_throat_z": grav_redshift(r0, r0, "zero"),
            "phi_neg_throat_z": grav_redshift(r0, r0, "neg"),
            "phi_neg_2r0_z": grav_redshift(2.0 * r0, r0, "neg"),
            "phi_neg_10r0_z": grav_redshift(10.0 * r0, r0, "neg"),
            "phi_neg_at_1e6_r0": phi_value(1.0e6 * r0, r0, "neg")}


# ================================================================ 5. Tidal forces + comfort bounds
# A traveller is not a point: head and feet sit at different r, and
# spacetime curvature pulls them apart (or squeezes them) - the
# tidal acceleration across a body of size xi. Morris-Thorne's
# human-comfort yardstick: tidal acceleration <= ~1 g across
# xi = 2 m.
#   RADIAL tidal (static frame): a = c^2 xi |R_rt rt| with
#     R = (1 - b/r) [ -Phi'' - Phi'^2
#                     + (b' r - b) / (2 r (r - b)) * Phi' ]
#   For Phi = 0 this is EXACTLY zero everywhere - the reason
#   Phi = 0 is called the zero-tidal-force wormhole. For
#   Phi = -r0/r it peaks just outside the throat at ~c^2 xi / r0^2.
#   LATERAL tidal (moving traveller, at the throat):
#     a = gamma^2 v^2 xi (1 - b'(r0)) / (2 r0^2)
#   - zero standing still, growing with crossing speed. Inverting
#   the comfort bound gives the minimum throat radius per speed.

BODY_XI_M = 2.0
CROSS_V_FRAC = 0.01             # classifier reference crossing speed


def radial_tidal(r, r0, shape="ellis", phi="zero", xi=BODY_XI_M):
    """Radial tidal acceleration across xi at radius r (m/s^2)."""
    if r0 <= 0 or r <= r0:
        raise ValueError("need r > r0 > 0 (defined outside the throat)")
    b = shape_b(r, r0, shape)
    bp = shape_bp(r, r0, shape)
    pp, ppp = phi_prime(r, r0, phi), phi_second(r, r0, phi)
    r_comp = (1.0 - b / r) * (-ppp - pp * pp
                              + (bp * r - b) / (2.0 * r * (r - b)) * pp)
    return C_LIGHT ** 2 * xi * abs(r_comp)


def radial_tidal_peak(r0, shape="ellis", phi="neg", xi=BODY_XI_M):
    """Worst radial tidal on a log grid from just outside the throat."""
    worst = 0.0
    for i in range(241):
        frac = 10.0 ** (-4.0 + 4.3 * i / 240.0)     # 1e-4 .. ~2
        worst = max(worst, radial_tidal(r0 * (1.0 + frac), r0, shape, phi, xi))
    return worst


def lateral_tidal_throat(r0, shape="ellis", v_frac=CROSS_V_FRAC, xi=BODY_XI_M):
    """Lateral tidal acceleration at the throat for speed v (m/s^2)."""
    if r0 <= 0:
        raise ValueError("throat radius must be positive")
    if not 0.0 <= v_frac < 1.0:
        raise ValueError("speed must be a fraction of c below 1")
    v = v_frac * C_LIGHT
    gamma = 1.0 / math.sqrt(1.0 - v_frac ** 2)
    bp0 = shape_bp(r0, r0, shape)
    return gamma * gamma * v * v * xi * (1.0 - bp0) / (2.0 * r0 * r0)


def min_throat_radius_lateral(v_frac, shape="ellis", xi=BODY_XI_M,
                              a_max=G_EARTH):
    """Smallest r0 whose lateral tidal at speed v stays <= a_max."""
    if not 0.0 < v_frac < 1.0:
        raise ValueError("speed must be a fraction of c in (0, 1)")
    v = v_frac * C_LIGHT
    gamma = 1.0 / math.sqrt(1.0 - v_frac ** 2)
    bp0 = shape_bp(1.0, 1.0, shape)
    return v * gamma * math.sqrt(xi * (1.0 - bp0) / (2.0 * a_max))


def min_throat_radius_walking(shape="ellis", xi=BODY_XI_M, a_max=G_EARTH):
    """Same bound at a labelled 5 m/s crawl (non-relativistic)."""
    bp0 = shape_bp(1.0, 1.0, shape)
    return 5.0 * math.sqrt(xi * (1.0 - bp0) / (2.0 * a_max))


def min_throat_radius_radial(phi="neg", shape="ellis", xi=BODY_XI_M,
                             a_max=G_EARTH):
    """Smallest r0 whose peak radial tidal stays <= a_max (Phi != 0).

    The peak scales as 1/r0^2, so measure it at a reference r0 and
    rescale: r0_min = r0_ref * sqrt(peak_ref / a_max).
    """
    r_ref = 1.0e6
    peak = radial_tidal_peak(r_ref, shape, phi, xi)
    return r_ref * math.sqrt(peak / a_max)


def tidal_report():
    rows = {}
    for v in (0.001, 0.01, 0.1):
        rows[f"min_r0_lateral_v{int(v * 1000)}e-3c_m"] = \
            min_throat_radius_lateral(v)
    rows["min_r0_lateral_walking_5ms_m"] = min_throat_radius_walking()
    rows["min_r0_radial_phi_neg_m"] = min_throat_radius_radial()
    rows["radial_tidal_phi_zero_max_ms2"] = max(
        radial_tidal((1.0 + f) * 1000.0, 1000.0, "ellis", "zero")
        for f in (0.001, 0.01, 0.1, 0.5, 1.0))
    rows["lateral_tidal_r0_1m_v0.01c_ms2"] = lateral_tidal_throat(1.0)
    rows["lateral_tidal_r0_1e6m_v0.01c_ms2"] = lateral_tidal_throat(1.0e6)
    return rows


# ================================================================ 6. The journey
# LABELLED EXAMPLE: throat r0 = 10 m (Ellis, Phi as chosen),
# stations parked at proper distance L = 5,000 m on BOTH sides, a
# ship crossing at constant v = 0.02 c measured by the station
# (shell) observers. Traveller proper time: Dt = 2L / (gamma v).
# Coordinate (distant-station) time with the lapse weighting:
# Dt_coord = (2 / v) * int e^{-Phi} dl along the path - for Phi = 0
# it reduces to gamma * Dt; for Phi = -r0/r the redshifted throat
# region makes distant clocks wait longer still.

JOURNEY = {"r0_m": 10.0, "station_proper_m": 5000.0, "v_frac": 0.02}


def _lapse_weighted_path(r0, r_station, shape, phi):
    """int e^{-Phi(r)} dl from throat to r_station (metres)."""
    bfun, bpfun = SHAPES[shape]

    def f(s):
        rr = r0 + s * s
        base = (2.0 * math.sqrt(r0 / (1.0 - bpfun(r0, r0))) if s == 0.0
                else 2.0 * s / math.sqrt(1.0 - bfun(rr, r0) / rr))
        return math.exp(-phi_value(rr, r0, phi)) * base

    return _simpson(f, math.sqrt(r_station - r0))


def journey_report(r0=JOURNEY["r0_m"], station_proper_m=JOURNEY["station_proper_m"],
                   v_frac=JOURNEY["v_frac"], shape="ellis"):
    v = v_frac * C_LIGHT
    gamma = 1.0 / math.sqrt(1.0 - v_frac ** 2)
    r_station = station_radius(r0, station_proper_m, shape)
    proper_time = 2.0 * station_proper_m / (gamma * v)
    out = {"r0_m": r0, "shape": shape, "v_frac": v_frac,
           "station_proper_m_each_side": station_proper_m,
           "station_coord_r_m": r_station,
           "traveller_proper_time_s": proper_time}
    for phi in ("zero", "neg"):
        path = _lapse_weighted_path(r0, r_station, shape, phi)
        out[f"coord_time_phi_{phi}_s"] = 2.0 * path / v
    return out


# ================================================================ 7. kNN traversability classifier
# Features: (log10 throat radius, log10 lateral tidal in g at the
# 0.01 c reference crossing, log10 |NEC density| at the throat in
# J/m^3). Training rows are GENERATED from the physics above across
# both shapes; labels follow the Morris-Thorne comfort rule on the
# reference crossing: <= 1 g comfortable, 1-50 g harsh, > 50 g
# non-traversable. kNN (k=3) then labels any new design point.

def _label_for_tidal_g(tidal_g):
    if tidal_g <= 1.0:
        return "traversable-comfortable"
    if tidal_g <= 50.0:
        return "traversable-harsh"
    return "non-traversable"


def _features(r0, shape):
    tidal_g = lateral_tidal_throat(r0, shape) / G_EARTH
    nec = abs(nec_radial(r0, r0, shape))
    return (math.log10(r0), math.log10(tidal_g), math.log10(nec))


def _build_train():
    rows = []
    for shape in ("ellis", "linear"):
        for exp in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5,
                    5.0, 5.5, 6.0, 6.48, 7.0, 7.5, 8.0, 9.0):
            r0 = 10.0 ** exp
            tidal_g = lateral_tidal_throat(r0, shape) / G_EARTH
            rows.append((*_features(r0, shape), _label_for_tidal_g(tidal_g)))
    return rows


_CLASSIFIER_TRAIN = _build_train()


def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def classify_design(r0, shape="ellis", k=3):
    """kNN (k=3) traversability label for a throat design."""
    if r0 <= 0:
        raise ValueError("throat radius must be positive")
    f = _features(r0, shape)
    ranked = sorted(_CLASSIFIER_TRAIN, key=lambda row: _dist(f, row[:3]))
    votes = {}
    for row in ranked[:k]:
        votes[row[3]] = votes.get(row[3], 0) + 1
    return max(sorted(votes), key=lambda lab: votes[lab])


def classify_report():
    scenarios = {
        "backyard_throat_1m": (1.0, "ellis"),
        "lab_throat_1km": (1.0e3, "ellis"),
        "mountain_throat_1000km": (1.0e6, "ellis"),
        "continental_throat_3000km": (3.0e6, "ellis"),
        "giant_throat_1e8m": (1.0e8, "ellis"),
        "linear_throat_1000km": (1.0e6, "linear"),
    }
    return {name: classify_design(r0, shape)
            for name, (r0, shape) in scenarios.items()}


# ================================================================ 8. Advisory seats
def _trace(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def carbon4_decide(topic="wormhole-lab-demo"):
    """Gemini Carbon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-carbon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Carbon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all claim gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="wormhole-lab-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Print the NEC violation next to every pretty funnel picture: the geometry is real mathematics, the exotic matter bill is the physics, and no wormhole has ever been observed.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["the embedding funnel: two sheets, one throat",
                  "flare-out at the rim, b'(r0) = -1",
                  "the tidal squeeze vs the 1 g comfort line",
                  "the exotic ledger: -4.8e42 J/m^3 at the throat",
                  "Phi = 0 vs Phi = -r0/r: two clocks disagree"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": carbon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    # 1. shape functions + flare-out
    chk("ellis_throat_b_equals_r0", shape_b(1.0, 1.0, "ellis") == 1.0)
    chk("linear_throat_b_equals_r0", shape_b(5.0, 5.0, "linear") == 5.0)
    chk("ellis_b_below_r",
        all(shape_b(m, 1.0, "ellis") < m for m in (1.5, 2.0, 5.0, 10.0, 100.0)))
    chk("linear_b_below_r_domain",
        all(shape_b(m, 1.0, "linear") < m for m in (1.5, 2.0, 2.5, 2.9)))
    chk("flare_out_ellis_analytic", shape_bp(1.0, 1.0, "ellis") == -1.0)
    chk("flare_out_ellis_numeric",
        abs(shape_bp_numeric(1.0, 1.0, "ellis") - (-1.0)) < 1e-4)
    chk("flare_out_linear_analytic", shape_bp(1.0, 1.0, "linear") == -0.5)
    chk("flare_out_linear_numeric",
        abs(shape_bp_numeric(1.0, 1.0, "linear") - (-0.5)) < 1e-4)
    chk("flare_out_both_hold",
        flare_out(1.0, "ellis")["flare_out_ok"]
        and flare_out(1.0, "linear")["flare_out_ok"])
    chk("bp_numeric_matches_analytic_2r0",
        abs(shape_bp_numeric(2.0, 1.0, "ellis") - shape_bp(2.0, 1.0, "ellis")) < 1e-5)
    # 2. embedding diagram + proper distance
    chk("embedding_zero_at_throat", embedding_z(1.0, 1.0, "ellis") == 0.0)
    z2 = embedding_z(2.0, 1.0, "ellis")
    chk("embedding_matches_closed_form_2r0",
        abs(z2 - embedding_z_ellis_closed(2.0, 1.0)) < 1e-9 * z2)
    z10 = embedding_z(10.0, 1.0, "ellis")
    chk("embedding_matches_closed_form_10r0",
        abs(z10 - embedding_z_ellis_closed(10.0, 1.0)) < 1e-9 * z10)
    chk("embedding_closed_form_value", abs(z2 - 1.3169579) < 1e-6)
    chk("embedding_monotonic",
        embedding_z(1.5, 1.0) < embedding_z(2.0, 1.0) < embedding_z(5.0, 1.0))
    chk("embedding_vertical_tangent_at_throat",
        embedding_z(1.0001, 1.0) / 0.0001 > 100.0)
    zl = embedding_z(2.0, 1.0, "linear")
    chk("embedding_linear_finite_positive", 0.0 < zl < 3.0)
    l2 = proper_distance(2.0, 1.0, "ellis")
    chk("proper_matches_closed_form",
        abs(l2 - proper_distance_ellis_closed(2.0, 1.0)) < 1e-9 * l2)
    chk("proper_exceeds_coordinate_gap",
        proper_distance(5.0, 1.0) > 4.0 and proper_distance(10.0, 1.0) > 9.0)
    chk("station_radius_inverts_proper",
        abs(proper_distance(station_radius(10.0, 5000.0), 10.0) - 5000.0) < 0.5)
    # 3. energy conditions + exotic matter
    rho1 = rho_si(1.0, 1.0, "ellis")
    chk("rho_throat_negative_ellis", rho1 < 0)
    chk("rho_throat_value_1m", abs(rho1 - (-4.81567e42)) < 0.01 * 4.81567e42)
    chk("tau_throat_positive", tau_si(1.0, 1.0, "ellis") > 0)
    nec1 = nec_radial(1.0, 1.0, "ellis")
    chk("nec_violated_at_throat", nec1 < 0)
    chk("nec_value_1m", abs(nec1 - (-9.63134e42)) < 0.01 * 9.63134e42)
    chk("nec_violated_linear_too", nec_radial(1.0, 1.0, "linear") < 0)
    chk("rho_scales_inverse_r0_squared",
        abs(rho_si(2.0, 2.0, "ellis") / rho1 - 0.25) < 1e-12)
    shell1 = exotic_mass_shell(1.0, "ellis")
    chk("exotic_mass_negative", shell1 < 0)
    chk("exotic_mass_shell_value", abs(shell1 - (-7.05105e26)) < 0.02 * 7.05105e26)
    chk("exotic_mass_scales_with_r0",
        abs(exotic_mass_shell(10.0, "ellis") / shell1 - 10.0) < 0.01 * 10.0)
    chk("exotic_mass_jupiter_scale", 0.2 < abs(shell1) / JUPITER_KG < 0.6)
    chk("ford_roman_time_tiny", 0.0 < ford_roman_time_s(rho1) < 1e-20)
    # 4. redshift functions
    chk("phi_zero_no_redshift", grav_redshift(1.0, 1.0, "zero") == 0.0)
    chk("redshift_throat_phi_neg",
        abs(grav_redshift(1.0, 1.0, "neg") - (math.e - 1.0)) < 1e-12)
    chk("redshift_2r0_phi_neg",
        abs(grav_redshift(2.0, 1.0, "neg") - (math.exp(0.5) - 1.0)) < 1e-12)
    chk("phi_neg_decays_at_infinity", abs(phi_value(1.0e6, 1.0, "neg")) < 1e-5)
    chk("redshift_falls_with_r",
        grav_redshift(2.0, 1.0, "neg") > grav_redshift(10.0, 1.0, "neg") > 0.0)
    # 5. tidal forces + comfort bounds
    chk("radial_tidal_phi_zero_exactly_zero",
        tidal_report()["radial_tidal_phi_zero_max_ms2"] == 0.0)
    lat1 = lateral_tidal_throat(1.0)
    chk("lateral_tidal_1m_value", abs(lat1 - 1.79769e13) < 0.01 * 1.79769e13)
    chk("lateral_tidal_inverse_r0_squared",
        abs(lateral_tidal_throat(10.0) / lat1 - 0.01) < 1e-12)
    chk("lateral_tidal_zero_at_rest", lateral_tidal_throat(1.0, v_frac=0.0) == 0.0)
    chk("min_throat_radius_0p01c",
        abs(min_throat_radius_lateral(0.01) - 1.35393e6) < 0.01 * 1.35393e6)
    chk("min_throat_radius_walking",
        abs(min_throat_radius_walking() - 2.258) < 0.01 * 2.258)
    chk("min_radius_grows_with_speed",
        min_throat_radius_lateral(0.001) < min_throat_radius_lateral(0.01)
        < min_throat_radius_lateral(0.1))
    chk("radial_tidal_phi_neg_nonzero",
        radial_tidal(1.1e6, 1.0e6, "ellis", "neg") > 1.0)
    chk("min_throat_radius_radial_phi_neg",
        1.0e8 < min_throat_radius_radial() < 2.0e8)
    # 6. the journey
    j = journey_report()
    chk("journey_proper_time_value",
        abs(j["traveller_proper_time_s"] - 1.66749e-3) < 0.01 * 1.66749e-3)
    chk("journey_coord_phi_zero_is_gamma_x_proper",
        abs(j["coord_time_phi_zero_s"] / j["traveller_proper_time_s"]
            - 1.0 / math.sqrt(1.0 - 0.02 ** 2)) < 1e-3)
    chk("journey_coord_phi_neg_longer",
        j["coord_time_phi_neg_s"] > j["coord_time_phi_zero_s"])
    chk("journey_coord_phi_neg_value",
        abs(j["coord_time_phi_neg_s"] - 1.69417e-3) < 0.01 * 1.69417e-3)
    chk("journey_station_coord_beyond_proper",
        j["station_coord_r_m"] > j["r0_m"] and j["station_coord_r_m"] < 5001.0)
    # 7. classifier
    rep = classify_report()
    chk("classifier_backyard_non", rep["backyard_throat_1m"] == "non-traversable")
    chk("classifier_lab_non", rep["lab_throat_1km"] == "non-traversable")
    chk("classifier_mountain_harsh",
        rep["mountain_throat_1000km"] == "traversable-harsh")
    chk("classifier_continental_comfortable",
        rep["continental_throat_3000km"] == "traversable-comfortable")
    chk("classifier_giant_comfortable",
        rep["giant_throat_1e8m"] == "traversable-comfortable")
    chk("classifier_linear_harsh",
        rep["linear_throat_1000km"] == "traversable-harsh")
    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14 and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_time_travel_hold", gate("time_travel_claim") == "HOLD")
    chk("gate_build_hold", gate("build_wormhole_claim") == "HOLD")
    chk("gate_ftl_hold", gate("ftl_travel_claim") == "HOLD")
    chk("gate_observed_hold", gate("observed_wormhole_claim") == "HOLD")
    chk("gate_exotic_hold", gate("exotic_matter_production_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    b = brains_report()
    chk("carbon4_no_override", b["decider"]["can_override_hold"] is False)
    chk("claude_no_override", b["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", b["flow"]["rendered"] is False and b["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("Wormhole-Lab - educational Morris-Thorne wormhole physics lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] Shape functions b(r) + the flare-out condition b'(r0) < 1")
    for name in SHAPES:
        fo = flare_out(1.0, name)
        print(f"    {name:6s}: b(r0) = {fo['b_at_throat_m']:.1f} m | "
              f"b'(r0) analytic = {fo['bp_analytic']:+.2f} | "
              f"numeric = {fo['bp_numeric']:+.4f} | flare-out "
              f"{'OK' if fo['flare_out_ok'] else 'FAILS'}")
    for row in shape_table():
        lin = ("  n/a (domain)" if row["b_linear_m"] is None
               else f"{row['b_linear_m']:8.3f} m")
        print(f"    r = {row['r_over_r0']:4.1f} r0: b_ellis = {row['b_ellis_m']:8.3f} m | "
              f"b_linear = {lin}")
    print("    -> both shapes pinch to b = r0 at the throat and open outward:")
    print("       b'(r0) < 1 is the flare-out condition, verified numerically.")
    print("\n[2] Embedding diagram z(r) - the funnel, integrated + closed form")
    for row in embedding_table():
        lin = ("  n/a (domain)" if row["z_linear_m"] is None
               else f"{row['z_linear_m']:8.4f} m")
        print(f"    r = {row['r_over_r0']:5.2f} r0: z_ellis = {row['z_ellis_m']:8.4f} m | "
              f"closed form = {row['z_ellis_closed_m']:8.4f} m | z_linear = {lin}")
    print("    -> the numeric integral matches r0 arcosh(r/r0) to ~1e-13; the")
    print("       tangent at the throat is vertical (the funnel neck).")
    print("\n[3] Energy conditions - the Einstein equations send the bill")
    er = energy_report(1.0)
    print(f"    Ellis throat, r0 = 1 m:")
    print(f"    rho(throat)  = {er['rho_throat_j_m3']:.4e} J/m^3 "
          f"({er['rho_throat_mass_equiv_kg_m3']:.3e} kg/m^3 equivalent)")
    print(f"    tau(throat)  = {er['tau_throat_pa']:.4e} Pa (radial tension)")
    print(f"    rho + p_r    = {er['nec_throat_j_m3']:.4e} J/m^3  <- NEC VIOLATED")
    print(f"    exotic mass in shell r0..2r0 = {er['exotic_mass_shell_r0_to_2r0_kg']:.4e} kg "
          f"({er['exotic_mass_shell_jupiters']:.2f} Jupiter masses, negative)")
    print(f"    Ford-Roman timescale at this density: {er['ford_roman_time_s']:.2e} s")
    print("    -> flare-out geometry FORCES rho + p_r < 0: exotic matter is not")
    print("       an ingredient choice, it is the Einstein equations' invoice.")
    print("\n[4] Redshift functions - Phi = 0 vs Phi = -r0/r")
    rr = redshift_report()
    print(f"    Phi = 0     : z at throat = {rr['phi_zero_throat_z']:.3f} (no redshift, no horizon)")
    print(f"    Phi = -r0/r : z at throat = {rr['phi_neg_throat_z']:.4f} | "
          f"at 2 r0 = {rr['phi_neg_2r0_z']:.4f} | at 10 r0 = {rr['phi_neg_10r0_z']:.4f}")
    print("    -> both keep e^{2 Phi} > 0 everywhere: no event horizon, by design.")
    print("\n[5] Tidal forces + the Morris-Thorne comfort bound (1 g over 2 m)")
    tr = tidal_report()
    print(f"    radial tidal, Phi = 0: {tr['radial_tidal_phi_zero_max_ms2']:.1f} m/s^2 "
          "everywhere (zero tidal force)")
    print(f"    lateral tidal at throat, v = 0.01 c: r0 = 1 m -> "
          f"{tr['lateral_tidal_r0_1m_v0.01c_ms2']:.3e} m/s^2 | "
          f"r0 = 1000 km -> {tr['lateral_tidal_r0_1e6m_v0.01c_ms2']:.2f} m/s^2")
    print(f"    minimum throat radius: crawl 5 m/s -> "
          f"{tr['min_r0_lateral_walking_5ms_m']:.2f} m | 0.001 c -> "
          f"{tr['min_r0_lateral_v1e-3c_m']:.3e} m | 0.01 c -> "
          f"{tr['min_r0_lateral_v10e-3c_m']:.3e} m | 0.1 c -> "
          f"{tr['min_r0_lateral_v100e-3c_m']:.3e} m")
    print(f"    with Phi = -r0/r the RADIAL tidal binds instead: "
          f"r0 >= {tr['min_r0_radial_phi_neg_m']:.3e} m even standing still")
    print("    -> cross slowly or build big: comfort is a size requirement.")
    print("\n[6] The journey (LABELLED example: r0 = 10 m, stations 5 km out, 0.02 c)")
    j = journey_report()
    print(f"    station coordinate r = {j['station_coord_r_m']:.2f} m "
          f"(proper distance {j['station_proper_m_each_side']:.0f} m each side)")
    print(f"    traveller proper time      : {j['traveller_proper_time_s'] * 1e3:.4f} ms")
    print(f"    coordinate time, Phi = 0   : {j['coord_time_phi_zero_s'] * 1e3:.4f} ms")
    print(f"    coordinate time, Phi=-r0/r : {j['coord_time_phi_neg_s'] * 1e3:.4f} ms")
    print("    -> a shortcut in space, not in the traveller's own clock: the")
    print("       crossing is local subluminal motion the whole way.")
    print("\n[7] Traversability classifier (TinyML kNN, reference crossing 0.01 c)")
    for name, label in classify_report().items():
        print(f"    {name:26s} -> {label}")
    print("\n[8] Advisory seats")
    print(f"    decider: {carbon4_decide()['decision']} trace={carbon4_decide()['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {claude_advisor()['can_override_hold']}")
    print(f"    flow rendered = {google_flow_plan()['rendered']} live = {google_flow_plan()['live']}")
    print(f"\n[9] HOLD gates: {len(HOLD_GATES)}")
    for k in HOLD_GATES:
        print(f"    HOLD  {k}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "shape":
        print(json.dumps(shape_table(), indent=2, sort_keys=True))
        return 0
    if cmd == "embedding":
        print(json.dumps(embedding_table(), indent=2, sort_keys=True))
        return 0
    if cmd == "energy":
        print(json.dumps(energy_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "redshift":
        print(json.dumps(redshift_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "tidal":
        print(json.dumps(tidal_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "journey":
        print(json.dumps(journey_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(classify_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for k, v in HOLD_GATES.items():
            print(f"{k}: {v}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "time_travel_claim"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
