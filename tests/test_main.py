"""Tests for Wormhole-Lab: every number checked against analytics."""
import io
import contextlib
import math

import pytest

import main as m


# ---- shape functions + flare-out (Morris-Thorne conditions)
def test_throat_b_equals_r0_both_shapes():
    assert m.shape_b(1.0, 1.0, "ellis") == 1.0
    assert m.shape_b(5.0, 5.0, "linear") == 5.0


def test_b_below_r_ellis():
    for mult in (1.5, 2.0, 5.0, 10.0, 100.0):
        assert m.shape_b(mult, 1.0, "ellis") < mult


def test_b_below_r_linear_domain():
    for mult in (1.5, 2.0, 2.5, 2.9):
        assert m.shape_b(mult, 1.0, "linear") < mult


def test_flare_out_analytic():
    assert m.shape_bp(1.0, 1.0, "ellis") == -1.0
    assert m.shape_bp(1.0, 1.0, "linear") == -0.5


def test_flare_out_numeric_matches():
    assert abs(m.shape_bp_numeric(1.0, 1.0, "ellis") - (-1.0)) < 1e-4
    assert abs(m.shape_bp_numeric(1.0, 1.0, "linear") - (-0.5)) < 1e-4
    assert abs(m.shape_bp_numeric(2.0, 1.0, "ellis")
               - m.shape_bp(2.0, 1.0, "ellis")) < 1e-5


def test_flare_out_both_hold():
    assert m.flare_out(1.0, "ellis")["flare_out_ok"]
    assert m.flare_out(1.0, "linear")["flare_out_ok"]


def test_invalid_radius_raises():
    with pytest.raises(ValueError):
        m.shape_b(0.5, 1.0, "ellis")
    with pytest.raises(ValueError):
        m.rho_si(1.0, 0.0, "ellis")


# ---- embedding diagram + proper distance
def test_embedding_zero_at_throat():
    assert m.embedding_z(1.0, 1.0, "ellis") == 0.0


def test_embedding_matches_closed_form():
    for mult in (1.5, 2.0, 5.0, 10.0):
        z_num = m.embedding_z(mult, 1.0, "ellis")
        z_closed = m.embedding_z_ellis_closed(mult, 1.0)
        assert abs(z_num - z_closed) < 1e-9 * z_closed


def test_embedding_closed_form_value():
    assert abs(m.embedding_z(2.0, 1.0, "ellis") - 1.3169579) < 1e-6


def test_embedding_monotonic_and_vertical_tangent():
    assert m.embedding_z(1.5, 1.0) < m.embedding_z(2.0, 1.0) < m.embedding_z(5.0, 1.0)
    assert m.embedding_z(1.0001, 1.0) / 0.0001 > 100.0


def test_embedding_linear_finite():
    assert 0.0 < m.embedding_z(2.0, 1.0, "linear") < 3.0


def test_proper_distance_matches_closed_form():
    l_num = m.proper_distance(2.0, 1.0, "ellis")
    assert abs(l_num - math.sqrt(3.0)) < 1e-9 * l_num


def test_proper_distance_exceeds_coordinate_gap():
    assert m.proper_distance(5.0, 1.0) > 4.0
    assert m.proper_distance(10.0, 1.0) > 9.0


def test_station_radius_inverts_proper_distance():
    r = m.station_radius(10.0, 5000.0)
    assert abs(m.proper_distance(r, 10.0) - 5000.0) < 0.5


# ---- energy conditions + exotic matter
def test_rho_throat_negative_and_value():
    rho = m.rho_si(1.0, 1.0, "ellis")
    assert rho < 0
    assert abs(rho - (-4.81567e42)) < 0.01 * 4.81567e42


def test_tau_throat_positive():
    assert m.tau_si(1.0, 1.0, "ellis") > 0


def test_nec_violated_at_throat():
    nec = m.nec_radial(1.0, 1.0, "ellis")
    assert nec < 0
    assert abs(nec - (-9.63134e42)) < 0.01 * 9.63134e42
    assert m.nec_radial(1.0, 1.0, "linear") < 0


def test_rho_scales_inverse_r0_squared():
    ratio = m.rho_si(2.0, 2.0, "ellis") / m.rho_si(1.0, 1.0, "ellis")
    assert abs(ratio - 0.25) < 1e-12


def test_exotic_mass_shell():
    shell = m.exotic_mass_shell(1.0, "ellis")
    assert shell < 0
    assert abs(shell - (-7.05105e26)) < 0.02 * 7.05105e26
    assert 0.2 < abs(shell) / m.JUPITER_KG < 0.6


def test_exotic_mass_scales_with_r0():
    ratio = m.exotic_mass_shell(10.0, "ellis") / m.exotic_mass_shell(1.0, "ellis")
    assert abs(ratio - 10.0) < 0.1


def test_ford_roman_time_tiny():
    t = m.ford_roman_time_s(m.rho_si(1.0, 1.0, "ellis"))
    assert 0.0 < t < 1e-20


# ---- redshift functions
def test_phi_zero_no_redshift():
    assert m.grav_redshift(1.0, 1.0, "zero") == 0.0
    assert m.grav_redshift(5.0, 1.0, "zero") == 0.0


def test_redshift_phi_neg_values():
    assert abs(m.grav_redshift(1.0, 1.0, "neg") - (math.e - 1.0)) < 1e-12
    assert abs(m.grav_redshift(2.0, 1.0, "neg") - (math.exp(0.5) - 1.0)) < 1e-12


def test_phi_neg_decays_and_redshift_falls():
    assert abs(m.phi_value(1.0e6, 1.0, "neg")) < 1e-5
    assert m.grav_redshift(2.0, 1.0, "neg") > m.grav_redshift(10.0, 1.0, "neg") > 0.0


# ---- tidal forces + comfort bounds
def test_radial_tidal_phi_zero_exactly_zero():
    assert m.tidal_report()["radial_tidal_phi_zero_max_ms2"] == 0.0
    assert m.radial_tidal(2.0e6, 1.0e6, "ellis", "zero") == 0.0


def test_lateral_tidal_value_and_scaling():
    lat1 = m.lateral_tidal_throat(1.0)
    assert abs(lat1 - 1.79769e13) < 0.01 * 1.79769e13
    assert abs(m.lateral_tidal_throat(10.0) / lat1 - 0.01) < 1e-12


def test_lateral_tidal_zero_at_rest():
    assert m.lateral_tidal_throat(1.0, v_frac=0.0) == 0.0


def test_min_throat_radius_values():
    assert abs(m.min_throat_radius_lateral(0.01) - 1.35393e6) < 0.01 * 1.35393e6
    assert abs(m.min_throat_radius_walking() - 2.258) < 0.01 * 2.258


def test_min_radius_grows_with_speed():
    assert (m.min_throat_radius_lateral(0.001)
            < m.min_throat_radius_lateral(0.01)
            < m.min_throat_radius_lateral(0.1))


def test_radial_tidal_phi_neg_binds():
    assert m.radial_tidal(1.1e6, 1.0e6, "ellis", "neg") > 1.0
    assert 1.0e8 < m.min_throat_radius_radial() < 2.0e8


# ---- the journey
def test_journey_proper_time():
    j = m.journey_report()
    assert abs(j["traveller_proper_time_s"] - 1.66749e-3) < 0.01 * 1.66749e-3


def test_journey_coord_times():
    j = m.journey_report()
    gamma = 1.0 / math.sqrt(1.0 - 0.02 ** 2)
    assert abs(j["coord_time_phi_zero_s"] / j["traveller_proper_time_s"]
               - gamma) < 1e-3
    assert j["coord_time_phi_neg_s"] > j["coord_time_phi_zero_s"]
    assert abs(j["coord_time_phi_neg_s"] - 1.69417e-3) < 0.01 * 1.69417e-3


def test_journey_station_radius():
    j = m.journey_report()
    assert j["r0_m"] < j["station_coord_r_m"] < 5001.0


# ---- classifier
def test_classifier_scenarios():
    rep = m.classify_report()
    assert rep["backyard_throat_1m"] == "non-traversable"
    assert rep["lab_throat_1km"] == "non-traversable"
    assert rep["mountain_throat_1000km"] == "traversable-harsh"
    assert rep["continental_throat_3000km"] == "traversable-comfortable"
    assert rep["giant_throat_1e8m"] == "traversable-comfortable"
    assert rep["linear_throat_1000km"] == "traversable-harsh"


# ---- gates + seats
def test_hold_gates_all_present():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())


def test_claim_gates_hold():
    for action in ("build_wormhole_claim", "exotic_matter_production_claim",
                   "time_travel_claim", "ftl_travel_claim",
                   "observed_wormhole_claim", "transport_service_claim"):
        assert m.gate(action) == "HOLD"


def test_sandbox_proceeds():
    assert m.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    b = m.brains_report()
    assert b["decider"]["can_override_hold"] is False
    assert b["advisor"]["can_override_hold"] is False
    assert b["flow"]["rendered"] is False and b["flow"]["live"] == 0


def test_demo_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks), [n for n, ok in checks if not ok]


def test_demo_deterministic():
    out1, out2 = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out1):
        m.demo()
    with contextlib.redirect_stdout(out2):
        m.demo()
    assert out1.getvalue() == out2.getvalue()
