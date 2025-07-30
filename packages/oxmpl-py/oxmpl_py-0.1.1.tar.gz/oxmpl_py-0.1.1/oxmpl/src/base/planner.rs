use crate::base::{
    error::PlanningError, goal::Goal, problem_definition::ProblemDefinition, space::StateSpace,
    state::State, validity::StateValidityChecker,
};
use std::{sync::Arc, time::Duration};

#[derive(Clone)]
pub struct Path<S: State>(pub Vec<S>);

pub trait Planner<S: State, SP: StateSpace<StateType = S>, G: Goal<S>> {
    fn setup(
        &mut self,
        problem_def: Arc<ProblemDefinition<S, SP, G>>,
        validity_checker: Arc<dyn StateValidityChecker<S> + Send + Sync>,
    );
    fn solve(&mut self, timeout: Duration) -> Result<Path<S>, PlanningError>;
}
