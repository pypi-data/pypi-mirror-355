use crate::base::state;

pub trait StateValidityChecker<S: state::State> {
    fn is_valid(&self, state: &S) -> bool;
}

pub struct DimensionBoundsChecker {
    pub bounds_per_dimension: Vec<(f64, f64)>,
}

impl StateValidityChecker<state::RealVectorState> for DimensionBoundsChecker {
    fn is_valid(&self, state: &state::RealVectorState) -> bool {
        if state.values.len() != self.bounds_per_dimension.len() {
            return false;
        }
        for (i, &value) in state.values.iter().enumerate() {
            let (min_b, max_b) = self.bounds_per_dimension[i];
            if value < min_b || value > max_b {
                return false;
            }
        }
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rvs_dimension_bounds_checker_is_valid_provided() {
        let rvs_db_checker = DimensionBoundsChecker {
            bounds_per_dimension: vec![(-2.0, 2.0), (-5.0, 0.0)],
        };

        let s1 = state::RealVectorState {
            values: vec![-2.0, -1.0],
        };
        let s2 = state::RealVectorState {
            values: vec![0.0, 0.0],
        };
        let s3 = state::RealVectorState {
            values: vec![1.0, -4.5],
        };
        let s4 = state::RealVectorState {
            values: vec![-2.1, -4.5],
        };
        let s5 = state::RealVectorState {
            values: vec![1.0, 1.0],
        };

        assert!(rvs_db_checker.is_valid(&s1), "s1 should be valid");
        assert!(rvs_db_checker.is_valid(&s2), "s2 should be valid");
        assert!(rvs_db_checker.is_valid(&s3), "s3 should be valid");
        assert!(!rvs_db_checker.is_valid(&s4), "s4 should be invalid (dim 0 too low)");
        assert!(!rvs_db_checker.is_valid(&s5), "s5 should be invalid (dim 1 too high)");
    }

    #[test]
    fn test_rvs_dimension_bounds_checker_boundary_conditions() {
        let rvs_db_checker = DimensionBoundsChecker {
            bounds_per_dimension: vec![(-2.0, 2.0), (-5.0, 0.0)],
        };

        let s_on_lower = state::RealVectorState {
            values: vec![-2.0, -5.0],
        };
        assert!(rvs_db_checker.is_valid(&s_on_lower), "State on all lower bounds should be valid");
        let s_on_upper = state::RealVectorState {
            values: vec![2.0, 0.0],
        };
        assert!(rvs_db_checker.is_valid(&s_on_upper), "State on all upper bounds should be valid");
        let s_below_lower_dim0 = state::RealVectorState {
            values: vec![-2.0000001, -2.5],
        };
        assert!(!rvs_db_checker.is_valid(&s_below_lower_dim0), "State just below lower bound for dim 0 should be invalid");
        let s_below_lower_dim1 = state::RealVectorState {
            values: vec![0.0, -5.0000001],
        };
        assert!(!rvs_db_checker.is_valid(&s_below_lower_dim1), "State just below lower bound for dim 1 should be invalid");
        let s_above_upper_dim0 = state::RealVectorState {
            values: vec![2.0000001, -2.5],
        };
        assert!(!rvs_db_checker.is_valid(&s_above_upper_dim0), "State just above upper bound for dim 0 should be invalid");
        let s_above_upper_dim1 = state::RealVectorState {
            values: vec![0.0, 0.0000001],
        };
        assert!(!rvs_db_checker.is_valid(&s_above_upper_dim1), "State just above upper bound for dim 1 should be invalid");
    }

    #[test]
    fn test_rvs_dimension_bounds_checker_dimension_mismatch() {
        let rvs_db_checker = DimensionBoundsChecker {
            bounds_per_dimension: vec![(-2.0, 2.0), (-5.0, 0.0)],
        };

        let s_too_few_dims = state::RealVectorState {
            values: vec![0.0],
        };
        assert!(!rvs_db_checker.is_valid(&s_too_few_dims), "State with too few dimensions should be invalid");
        let s_too_many_dims = state::RealVectorState {
            values: vec![0.0, -1.0, 0.0],
        };
        assert!(!rvs_db_checker.is_valid(&s_too_many_dims), "State with too many dimensions should be invalid");
    }

    #[test]
    fn test_rvs_dimension_bounds_checker_empty_bounds_and_state() {
        let checker_empty_bounds = DimensionBoundsChecker {
            bounds_per_dimension: vec![],
        };
        let s_empty = state::RealVectorState {
            values: vec![],
        };
        assert!(checker_empty_bounds.is_valid(&s_empty), "Empty state with empty bounds should be valid");
        let s_non_empty = state::RealVectorState {
            values: vec![0.0],
        };
        assert!(!checker_empty_bounds.is_valid(&s_non_empty), "Non-empty state with empty bounds should be invalid (dim mismatch)");
        let checker_non_empty_bounds = DimensionBoundsChecker {
            bounds_per_dimension: vec![(0.0, 1.0)],
        };
        assert!(!checker_non_empty_bounds.is_valid(&s_empty), "Empty state with non-empty bounds should be invalid (dim mismatch)");
    }

    #[test]
    fn test_rvs_dimension_bounds_checker_single_dimension() {
        let rvs_db_checker = DimensionBoundsChecker {
            bounds_per_dimension: vec![(-1.0, 1.0)],
        };

        let s_valid_1d = state::RealVectorState { values: vec![0.0] };
        let s_invalid_low_1d = state::RealVectorState { values: vec![-1.1] };
        let s_invalid_high_1d = state::RealVectorState { values: vec![1.1] };
        let s_on_lower_1d = state::RealVectorState { values: vec![-1.0] };
        let s_on_upper_1d = state::RealVectorState { values: vec![1.0] };

        assert!(rvs_db_checker.is_valid(&s_valid_1d));
        assert!(!rvs_db_checker.is_valid(&s_invalid_low_1d));
        assert!(!rvs_db_checker.is_valid(&s_invalid_high_1d));
        assert!(rvs_db_checker.is_valid(&s_on_lower_1d));
        assert!(rvs_db_checker.is_valid(&s_on_upper_1d));
    }
}
