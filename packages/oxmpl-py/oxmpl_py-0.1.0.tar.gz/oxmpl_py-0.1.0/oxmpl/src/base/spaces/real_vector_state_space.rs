use rand::Rng;

use crate::base::{
    error::{StateSamplingError, StateSpaceError}, space::StateSpace, state::RealVectorState
};

pub struct RealVectorStateSpace {
    /// n-Dimensionality of VectorStateSpace i.e. R^n.
    pub dimension: usize,
    pub bounds: Vec<(f64, f64)>,
}

impl RealVectorStateSpace {
    pub fn new(
        dimension: usize,
        bounds_option: Option<Vec<(f64, f64)>>,
    ) -> Result<Self, StateSpaceError> {
        let bounds = match bounds_option {
            Some(explicit_bounds) => {
                if explicit_bounds.len() != dimension {
                    return Err(StateSpaceError::DimensionMismatch {
                        expected: dimension,
                        found: explicit_bounds.len(),
                    });
                }
                for bound in &explicit_bounds {
                    if bound.0 >= bound.1 {
                        return Err(StateSpaceError::InvalidBound {
                            lower: bound.0,
                            upper: bound.1,
                        });
                    }
                }
                explicit_bounds
            }
            None => {
                if dimension == 0 {
                    return Err(StateSpaceError::ZeroDimensionUnbounded);
                }
                vec![(f64::NEG_INFINITY, f64::INFINITY); dimension]
            }
        };

        Ok(Self { dimension, bounds })
    }
}

impl StateSpace for RealVectorStateSpace {
    type StateType = RealVectorState;

    /// Find distance between current state1 and target state2. Depends on StateSpace.
    /// In RealVectorStateSpace, this refers to the L2-norm.
    fn distance(&self, state1: &Self::StateType, state2: &Self::StateType) -> f64 {
        assert_eq!(
            state1.values.len(),
            self.dimension,
            "State1 has incorrect dimension for this space."
        );
        assert_eq!(
            state2.values.len(),
            self.dimension,
            "State2 has incorrect dimension for this space."
        );
        state1
            .values
            .iter()
            .zip(state2.values.iter())
            .map(|(v1, v2)| (v1 - v2).powi(2))
            .sum::<f64>()
            .sqrt()
    }

    fn interpolate(
        &self,
        from: &Self::StateType,
        to: &Self::StateType,
        t: f64,
        out_state: &mut Self::StateType,
    ) {
        assert_eq!(
            from.values.len(),
            self.dimension,
            "From-state has incorrect dimension."
        );
        assert_eq!(
            to.values.len(),
            self.dimension,
            "To-state has incorrect dimension."
        );
        assert_eq!(
            out_state.values.len(),
            self.dimension,
            "Out-state has incorrect dimension or not properly initialized."
        );
        for i in 0..from.values.len() {
            out_state.values[i] = from.values[i] + (to.values[i] - from.values[i]) * t;
        }
    }

    fn enforce_bounds(&self, state: &mut Self::StateType) {
        if state.values.len() != self.dimension {
            assert_eq!(
                state.values.len(),
                self.dimension,
                "State and space dimension mismatch when enforcing bounds."
            );
        }
        for (i, value) in state.values.iter_mut().enumerate() {
            if i < self.bounds.len() {
                let (lower, upper) = self.bounds[i];
                *value = value.clamp(lower, upper);
            }
        }
    }

    fn satisfies_bounds(&self, state: &Self::StateType) -> bool {
        if state.values.len() != self.dimension {
            assert_eq!(
                state.values.len(),
                self.dimension,
                "State and space dimension mismatch when checking bound satisfaction."
            );
        }
        for i in 0..self.dimension {
            let (lower, upper) = self.bounds[i];
            if state.values[i] - f64::EPSILON > upper || state.values[i] + f64::EPSILON < lower {
                return false;
            }
        }
        true
    }

    fn sample_uniform(&self, rng: &mut impl Rng) -> Result<Self::StateType, StateSamplingError> {
        let mut values = Vec::with_capacity(self.dimension);

        for i in 0..self.dimension {
            let (lower, upper) = self.bounds[i];

            if !lower.is_finite() || !upper.is_finite() {
                return Err(StateSamplingError::UnboundedDimension { dimension_index: i });
            }
            if lower >= upper {
                return Err(StateSamplingError::ZeroVolume);
            }
            values.push(rng.random_range(lower..upper));
        }

        Ok(RealVectorState { values })
    }
}
