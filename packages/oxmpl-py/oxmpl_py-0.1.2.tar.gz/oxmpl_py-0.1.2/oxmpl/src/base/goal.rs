use crate::base::{error::StateSamplingError, state::State};
use rand::Rng;

pub trait Goal<S: State> {
    fn is_satisfied(&self, state: &S) -> bool;
}

pub trait GoalRegion<S: State>: Goal<S> {
    /// Returns the distance from a state to the goal region.
    fn distance_goal(&self, state: &S) -> f64;
}

pub trait GoalSampleableRegion<S: State>: GoalRegion<S> {
    /// Generates a state from the goal region.
    fn sample_goal(&self, rng: &mut impl Rng) -> Result<S, StateSamplingError>;
}
