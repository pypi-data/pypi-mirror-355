use super::*;
use crate::base::state;

use std::f64::consts::PI;
const EPS: f64 = 1e-9;

fn s_raw(val: f64) -> state::SO2State {
    state::SO2State { value: val }
}

fn s_norm(val: f64) -> state::SO2State {
    state::SO2State::new(val)
}

#[test]
fn zero_distance() {
    let space = SO2StateSpace {};
    assert!((space.distance(&s_raw(0.0), &s_raw(0.0)) - 0.0).abs() < EPS);
    assert!((space.distance(&s_raw(PI), &s_raw(PI)) - 0.0).abs() < EPS);
    assert!((space.distance(&s_raw(0.0), &s_raw(2.0 * PI)) - 0.0).abs() < EPS);
    assert!((space.distance(&s_raw(0.0), &s_raw(-2.0 * PI)) - 0.0).abs() < EPS);
    assert!((space.distance(&s_raw(PI), &s_raw(-PI)) - 0.0).abs() < EPS);
    assert!((space.distance(&s_raw(0.5), &s_raw(0.5 + 8.0 * PI)) - 0.0).abs() < EPS);
}

#[test]
fn simple_differences_no_wrap_needed_for_shortest() {
    let space = SO2StateSpace {};
    assert!((space.distance(&s_raw(0.1), &s_raw(0.5)) - 0.4).abs() < EPS);
    assert!((space.distance(&s_raw(0.5), &s_raw(0.1)) - 0.4).abs() < EPS);
    assert!((space.distance(&s_raw(-0.1), &s_raw(-0.5)) - 0.4).abs() < EPS);
    assert!((space.distance(&s_raw(0.0), &s_raw(PI - 0.1)) - (PI - 0.1)).abs() < EPS);
    assert!((space.distance(&s_raw(0.0), &s_raw(-(PI - 0.1))) - (PI - 0.1)).abs() < EPS);
}

#[test]
fn maximum_distance_pi() {
    let space = SO2StateSpace {};
    assert!((space.distance(&s_raw(0.0), &s_raw(PI)) - PI).abs() < EPS);
    assert!((space.distance(&s_raw(0.5), &s_raw(0.5 + PI)) - PI).abs() < EPS);
    assert!((space.distance(&s_raw(0.5), &s_raw(0.5 - PI)) - PI).abs() < EPS);
    assert!((space.distance(&s_raw(0.0), &s_raw(3.0 * PI)) - PI).abs() < EPS);
    assert!((space.distance(&s_raw(0.0), &s_raw(-3.0 * PI)) - PI).abs() < EPS);
}

#[test]
fn wrap_around_cases_for_shortest_angle() {
    let space = SO2StateSpace {};
    assert!((space.distance(&s_raw(0.1), &s_raw(2.0 * PI - 0.1)) - 0.2).abs() < EPS);
    assert!((space.distance(&s_raw(2.0 * PI - 0.1), &s_raw(0.1)) - 0.2).abs() < EPS);
    assert!((space.distance(&s_raw(0.1), &s_raw(-0.1)) - 0.2).abs() < EPS);

    assert!((space.distance(&s_raw(0.0), &s_raw(1.75 * PI)) - (0.25 * PI)).abs() < EPS);
    assert!((space.distance(&s_raw(0.0), &s_raw(1.25 * PI)) - (0.75 * PI)).abs() < EPS);

    assert!((space.distance(&s_raw(0.1), &s_raw(4.0 * PI - 0.1)) - 0.2).abs() < EPS);
    assert!((space.distance(&s_raw(0.1), &s_raw(-4.0 * PI - 0.1)) - 0.2).abs() < EPS);
}

#[test]
fn boundary_values_around_pi_for_normalization() {
    let space = SO2StateSpace {};
    assert!((space.distance(&s_raw(0.0), &s_raw(PI - EPS)) - (PI - EPS)).abs() < EPS * 2.0);
    assert!((space.distance(&s_raw(0.0), &s_raw(PI + EPS)) - (PI - EPS)).abs() < EPS * 2.0);

    assert!((space.distance(&s_raw(0.0), &s_raw(-(PI - EPS))) - (PI - EPS)).abs() < EPS * 2.0);
    assert!((space.distance(&s_raw(0.0), &s_raw(-(PI + EPS))) - (PI - EPS)).abs() < EPS * 2.0);
}

#[test]
fn t_equals_zero() {
    let space = SO2StateSpace {};
    let mut out = s_raw(0.0);
    space.interpolate(&s_raw(0.5), &s_raw(1.0), 0.0, &mut out);
    assert!((out.value - s_norm(0.5).value).abs() < EPS);

    space.interpolate(&s_raw(2.0 * PI - 0.1), &s_raw(0.1), 0.0, &mut out);
    assert!((out.value - s_norm(2.0 * PI - 0.1).value).abs() < EPS);

    space.interpolate(&s_raw(2.5 * PI), &s_raw(0.1), 0.0, &mut out);
    assert!((out.value - s_norm(0.5 * PI).value).abs() < EPS);
}

#[test]
fn t_equals_one() {
    let space = SO2StateSpace {};
    let mut out = s_raw(0.0);
    space.interpolate(&s_raw(0.5), &s_raw(1.0), 1.0, &mut out);
    assert!((out.value - s_norm(1.0).value).abs() < EPS);

    space.interpolate(&s_raw(0.1), &s_raw(2.0 * PI - 0.1), 1.0, &mut out);
    assert!((out.value - s_norm(2.0 * PI - 0.1).value).abs() < EPS);

    space.interpolate(&s_raw(0.1), &s_raw(2.5 * PI), 1.0, &mut out);
    assert!((out.value - s_norm(0.5 * PI).value).abs() < EPS);
}

#[test]
fn t_equals_half_simple_no_wrap() {
    let space = SO2StateSpace {};
    let mut out = s_raw(0.0);
    space.interpolate(&s_raw(0.0), &s_raw(1.0), 0.5, &mut out);
    assert!((out.value - s_norm(0.5).value).abs() < EPS);

    space.interpolate(&s_raw(PI / 2.0), &s_raw(PI), 0.5, &mut out);
    assert!((out.value - s_norm(0.75 * PI).value).abs() < EPS);
}

#[test]
fn t_equals_half_with_wrap_around() {
    let space = SO2StateSpace {};
    let mut out = s_raw(0.0);

    space.interpolate(&s_raw(0.1), &s_raw(2.0 * PI - 0.1), 0.5, &mut out);
    assert!((out.value - s_norm(0.0).value).abs() < EPS);

    space.interpolate(&s_raw(2.0 * PI - 0.1), &s_raw(0.1), 0.5, &mut out);
    assert!((out.value - s_norm(0.0).value).abs() < EPS);

    space.interpolate(&s_raw(PI - 0.1), &s_raw(PI + 0.1), 0.5, &mut out);
    assert!((out.value - s_norm(PI).value).abs() < EPS);

    space.interpolate(&s_raw(0.25 * PI), &s_raw(1.75 * PI), 0.5, &mut out);
    assert!((out.value - s_norm(0.0).value).abs() < EPS);
}

#[test]
fn same_from_and_to_states_interpolation() {
    let space = SO2StateSpace {};
    let mut out = s_raw(0.0);

    space.interpolate(&s_raw(0.5), &s_raw(0.5), 0.5, &mut out);
    assert!((out.value - s_norm(0.5).value).abs() < EPS);

    space.interpolate(&s_raw(0.5), &s_raw(0.5 + 2.0 * PI), 0.5, &mut out);
    assert!((out.value - s_norm(0.5).value).abs() < EPS);

    space.interpolate(&s_raw(0.5), &s_raw(0.5 - 4.0 * PI), 0.75, &mut out);
    assert!((out.value - s_norm(0.5).value).abs() < EPS);
}

#[test]
fn extrapolation_interpolation() {
    let space = SO2StateSpace {};
    let mut out = s_raw(0.0);

    space.interpolate(&s_raw(0.0), &s_raw(0.2), -1.0, &mut out);
    assert!((out.value - s_norm(-0.2).value).abs() < EPS);

    space.interpolate(&s_raw(0.0), &s_raw(0.2), 2.0, &mut out);
    assert!((out.value - s_norm(0.4).value).abs() < EPS);

    space.interpolate(&s_raw(0.1), &s_raw(2.0 * PI - 0.1), 2.0, &mut out);
    assert!((out.value - s_norm(2.0 * PI - 0.3).value).abs() < EPS);
}

#[test]
fn output_is_always_normalized_in_npi_to_pi() {
    let space = SO2StateSpace {};
    let mut out = s_raw(0.0);

    space.interpolate(
        &s_raw(PI),
        &s_raw(2.0 * PI),
        0.5,
        &mut out,
    );
    let expected1 = (3.0 * PI / 2.0 + PI).rem_euclid(2.0 * PI) - PI; // Should be 1.925*PI
    assert!(
        (out.value - expected1).abs() < EPS,
        "Output normalization (negative intermediate) failed. Expected {}, got {}",
        expected1,
        out.value
    );
    assert!(
        out.value > -PI && out.value <= PI,
        "Output not in (-PI, PI]"
    );

    space.interpolate(&s_raw(1.95 * PI), &s_raw(0.2 * PI), 0.5, &mut out);
    let expected2 = (2.075 * PI).rem_euclid(2.0 * PI); // Should be 0.075*PI
    assert!(
        (out.value - expected2).abs() < EPS,
        "Output normalization (large positive intermediate) failed. Expected {}, got {}",
        expected2,
        out.value
    );
    assert!(
        out.value >= 0.0 && out.value < 2.0 * PI,
        "Output not in [0, 2PI)"
    );
}
