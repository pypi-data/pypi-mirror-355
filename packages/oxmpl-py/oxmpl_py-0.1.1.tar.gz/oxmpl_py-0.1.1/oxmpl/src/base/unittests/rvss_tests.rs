use super::*;
use crate::base::state;

#[test]
fn test_rvss_distance_2d() {
    let space = RealVectorStateSpace::new(2, None)
        .expect("Test setup failed: Creating a 2D unbounded space should be valid.");

    let s1 = state::RealVectorState {
        values: vec![0.0, 0.0],
    };
    let s2 = state::RealVectorState {
        values: vec![3.0, 4.0],
    };
    let s3 = state::RealVectorState {
        values: vec![0.0, 0.0],
    };

    assert!(
        (space.distance(&s1, &s2) - 5.0).abs() < 1e-9,
        "Basic 2D distance failed"
    );
    assert!(
        (space.distance(&s1, &s3) - 0.0).abs() < 1e-9,
        "Zero distance failed"
    );
    assert!(
        (space.distance(&s2, &s1) - 5.0).abs() < 1e-9,
        "Symmetry failed"
    );
}

#[test]
fn test_rvss_distance_various_dimensions_and_values() {
    let space0d  = RealVectorStateSpace::new(0, None)
        .expect("Test setup failed: Creating a 2D unbounded space should be valid.");

    let s0d_1 = state::RealVectorState { values: vec![] };
    let s0d_2 = state::RealVectorState { values: vec![] };
    assert!(
        (space0d.distance(&s0d_1, &s0d_2) - 0.0).abs() < 1e-9,
        "0D distance failed"
    );

    let space1d  = RealVectorStateSpace::new(1, None)
        .expect("Test setup failed: Creating a 2D unbounded space should be valid.");
    let s1d_1 = state::RealVectorState { values: vec![-2.0] };
    let s1d_2 = state::RealVectorState { values: vec![3.0] };
    assert!(
        (space1d.distance(&s1d_1, &s1d_2) - 5.0).abs() < 1e-9,
        "1D distance failed"
    );

    let space3d  = RealVectorStateSpace::new(3, None)
        .expect("Test setup failed: Creating a 2D unbounded space should be valid.");
    let s3d_1 = state::RealVectorState {
        values: vec![1.0, -2.0, 3.0],
    };
    let s3d_2 = state::RealVectorState {
        values: vec![-1.0, 0.0, 7.0],
    };
    assert!(
        (space3d.distance(&s3d_1, &s3d_2) - 24.0_f64.sqrt()).abs() < 1e-9,
        "3D distance with negative values failed"
    );
}

#[test]
fn test_rvss_distance_triangle_inequality() {
    let space = RealVectorStateSpace { dimension: 2 };
    let s1 = state::RealVectorState {
        values: vec![0.0, 0.0],
    };
    let s2 = state::RealVectorState {
        values: vec![3.0, 4.0],
    };
    let s3 = state::RealVectorState {
        values: vec![7.0, 1.0],
    };

    let dist_s1_s2 = space.distance(&s1, &s2);
    let dist_s2_s3 = space.distance(&s2, &s3);
    let dist_s1_s3 = space.distance(&s1, &s3);

    assert!(
        dist_s1_s3 <= dist_s1_s2 + dist_s2_s3 + 1e-9,
        "Triangle inequality failed: d(ac) <= d(ab) + d(bc)"
    );
}

#[test]
#[should_panic(expected = "State1 has incorrect dimension for this space.")]
fn test_rvss_distance_panic_s1_wrong_dim() {
    let space = RealVectorStateSpace { dimension: 2 };
    let s1_wrong_dim = state::RealVectorState { values: vec![0.0] };
    let s2_correct_dim = state::RealVectorState {
        values: vec![3.0, 4.0],
    };
    space.distance(&s1_wrong_dim, &s2_correct_dim);
}

#[test]
#[should_panic(expected = "State2 has incorrect dimension for this space.")]
fn test_rvss_distance_panic_s2_wrong_dim() {
    let space = RealVectorStateSpace { dimension: 2 };
    let s1_correct_dim = state::RealVectorState {
        values: vec![0.0, 0.0],
    }; // 2D
    let s2_wrong_dim = state::RealVectorState {
        values: vec![3.0, 4.0, 5.0],
    }; // 3D
    space.distance(&s1_correct_dim, &s2_wrong_dim);
}

#[test]
fn test_rvss_interpolate_2d() {
    let space = RealVectorStateSpace { dimension: 2 };
    let s_from = state::RealVectorState {
        values: vec![0.0, 0.0],
    };
    let s_to = state::RealVectorState {
        values: vec![10.0, 20.0],
    };
    let mut s_interpolated = state::RealVectorState {
        values: vec![0.0, 0.0],
    };

    space.interpolate(&s_from, &s_to, 0.0, &mut s_interpolated);
    assert_eq!(s_interpolated, s_from, "Interpolate with t=0.0 failed");

    space.interpolate(&s_from, &s_to, 1.0, &mut s_interpolated);
    assert_eq!(s_interpolated, s_to, "Interpolate with t=1.0 failed");

    space.interpolate(&s_from, &s_to, 0.5, &mut s_interpolated);
    assert_eq!(
        s_interpolated,
        state::RealVectorState {
            values: vec![5.0, 10.0]
        },
        "Interpolate with t=0.5 failed"
    );
}

#[test]
fn test_rvss_interpolate_various_dimensions_and_values() {
    let space0d = RealVectorStateSpace { dimension: 0 };
    let s0d_from = state::RealVectorState { values: vec![] };
    let s0d_to = state::RealVectorState { values: vec![] };
    let mut s0d_interpolated = state::RealVectorState { values: vec![] };
    space0d.interpolate(&s0d_from, &s0d_to, 0.5, &mut s0d_interpolated);
    assert_eq!(s0d_interpolated, s0d_from, "0D interpolate failed");

    let space1d = RealVectorStateSpace { dimension: 1 };
    let s1d_from = state::RealVectorState {
        values: vec![-10.0],
    };
    let s1d_to = state::RealVectorState { values: vec![10.0] };
    let mut s1d_interpolated = state::RealVectorState { values: vec![0.0] };
    space1d.interpolate(&s1d_from, &s1d_to, 0.25, &mut s1d_interpolated);
    assert_eq!(
        s1d_interpolated,
        state::RealVectorState { values: vec![-5.0] },
        "1D interpolate failed"
    );

    // 3-Dimensional Space
    let space3d = RealVectorStateSpace { dimension: 3 };
    let s3d_from = state::RealVectorState {
        values: vec![0.0, 10.0, -20.0],
    };
    let s3d_to = state::RealVectorState {
        values: vec![10.0, 20.0, 0.0],
    };
    let mut s3d_interpolated = state::RealVectorState {
        values: vec![0.0, 0.0, 0.0],
    };
    space3d.interpolate(&s3d_from, &s3d_to, 0.75, &mut s3d_interpolated);
    assert_eq!(
        s3d_interpolated,
        state::RealVectorState {
            values: vec![7.5, 17.5, -5.0]
        },
        "3D interpolate failed"
    );
}

#[test]
fn test_rvss_interpolate_extrapolation() {
    let space = RealVectorStateSpace { dimension: 1 };
    let s_from = state::RealVectorState { values: vec![0.0] };
    let s_to = state::RealVectorState { values: vec![10.0] };
    let mut s_interpolated = state::RealVectorState { values: vec![0.0] };

    space.interpolate(&s_from, &s_to, -0.5, &mut s_interpolated);
    assert_eq!(
        s_interpolated,
        state::RealVectorState { values: vec![-5.0] },
        "Extrapolate with t < 0 failed"
    );

    // t > 1
    space.interpolate(&s_from, &s_to, 1.5, &mut s_interpolated);
    assert_eq!(
        s_interpolated,
        state::RealVectorState { values: vec![15.0] },
        "Extrapolate with t > 1 failed"
    );
}

#[test]
fn test_rvss_interpolate_same_from_to_states() {
    let space = RealVectorStateSpace { dimension: 2 };
    let s_from = state::RealVectorState {
        values: vec![1.0, 2.0],
    };
    let s_to = s_from.clone();
    let mut s_interpolated = state::RealVectorState {
        values: vec![0.0, 0.0],
    };

    space.interpolate(&s_from, &s_to, 0.0, &mut s_interpolated);
    assert_eq!(s_interpolated, s_from, "t=0.0 with same states failed");

    space.interpolate(&s_from, &s_to, 0.5, &mut s_interpolated);
    assert_eq!(s_interpolated, s_from, "t=0.5 with same states failed");

    space.interpolate(&s_from, &s_to, 1.0, &mut s_interpolated);
    assert_eq!(s_interpolated, s_from, "t=1.0 with same states failed");

    space.interpolate(&s_from, &s_to, 100.0, &mut s_interpolated);
    assert_eq!(s_interpolated, s_from, "t=100.0 with same states failed");
}

#[test]
#[should_panic(expected = "From-state has incorrect dimension.")]
fn test_rvss_interpolate_panic_from_wrong_dim() {
    let space = RealVectorStateSpace { dimension: 2 };
    let s_from_wrong_dim = state::RealVectorState { values: vec![0.0] };
    let s_to_correct_dim = state::RealVectorState {
        values: vec![1.0, 1.0],
    };
    let mut s_out_correct_dim = state::RealVectorState {
        values: vec![0.0, 0.0],
    };
    space.interpolate(
        &s_from_wrong_dim,
        &s_to_correct_dim,
        0.5,
        &mut s_out_correct_dim,
    );
}

#[test]
#[should_panic(expected = "To-state has incorrect dimension.")]
fn test_rvss_interpolate_panic_to_wrong_dim() {
    let space = RealVectorStateSpace { dimension: 2 };
    let s_from_correct_dim = state::RealVectorState {
        values: vec![0.0, 0.0],
    };
    let s_to_wrong_dim = state::RealVectorState { values: vec![1.0] };
    let mut s_out_correct_dim = state::RealVectorState {
        values: vec![0.0, 0.0],
    };
    space.interpolate(
        &s_from_correct_dim,
        &s_to_wrong_dim,
        0.5,
        &mut s_out_correct_dim,
    );
}

#[test]
#[should_panic(expected = "Out-state has incorrect dimension or not properly initialized.")]
fn test_rvss_interpolate_panic_out_wrong_dim() {
    let space = RealVectorStateSpace { dimension: 2 };
    let s_from_correct_dim = state::RealVectorState {
        values: vec![0.0, 0.0],
    };
    let s_to_correct_dim = state::RealVectorState {
        values: vec![1.0, 1.0],
    };
    let mut s_out_wrong_dim = state::RealVectorState { values: vec![0.0] };
    space.interpolate(
        &s_from_correct_dim,
        &s_to_correct_dim,
        0.5,
        &mut s_out_wrong_dim,
    );
}

#[test]
#[should_panic(expected = "Out-state has incorrect dimension or not properly initialized.")]
fn test_rvss_interpolate_panic_out_uninitialized_values_wrong_len() {
    let space = RealVectorStateSpace { dimension: 2 };
    let s_from = state::RealVectorState {
        values: vec![0.0, 0.0],
    };
    let s_to = state::RealVectorState {
        values: vec![10.0, 20.0],
    };
    let mut s_interpolated_wrong_len = state::RealVectorState { values: Vec::new() };

    space.interpolate(&s_from, &s_to, 0.5, &mut s_interpolated_wrong_len);
}
