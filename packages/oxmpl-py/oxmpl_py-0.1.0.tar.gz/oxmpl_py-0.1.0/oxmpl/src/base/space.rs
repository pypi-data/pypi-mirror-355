use rand::Rng;

use crate::base::{error::StateSamplingError, state::State};

pub use crate::base::spaces::{
    real_vector_state_space::RealVectorStateSpace,
    so2_state_space::SO2StateSpace,
};

pub trait StateSpace {
    /// StateType defines what is acceptable in current StateSpace
    type StateType: State;
    /// Find distance between current state1 and target state2. Depends on StateSpace.
    fn distance(&self, state1: &Self::StateType, state2: &Self::StateType) -> f64;
    /// Find state interpolated between `from` and `to` states given 0<=`t`<=1.
    fn interpolate(
        &self,
        from: &Self::StateType,
        to: &Self::StateType,
        t: f64,
        state: &mut Self::StateType,
    );
    /// Modifies the given state to ensure it conforms to the space's defined bounds.
    fn enforce_bounds(&self, state: &mut Self::StateType);

    fn satisfies_bounds(&self, state: &Self::StateType) -> bool;

    /// Generates a state uniformly at random from the entire state space.
    fn sample_uniform(&self, rng: &mut impl Rng) -> Result<Self::StateType, StateSamplingError>;
}

// #[cfg(test)]
// #[path = "unittests/rvss_tests.rs"]
// mod rvss_tests;

// #[cfg(test)
// #[path = "unittests/so2ss_tests.rs"]
// mod so2ss_tests;
