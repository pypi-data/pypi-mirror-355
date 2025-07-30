use crate::base::{goal::Goal, space::StateSpace, state::State};
use std::sync::Arc;

pub struct ProblemDefinition<S: State, SP: StateSpace<StateType = S>, G: Goal<S>> {
    pub space: Arc<SP>,
    pub start_states: Vec<S>,
    pub goal: Arc<G>,
    // Potentially state_validity_checker here if not passed directly to planner
}
