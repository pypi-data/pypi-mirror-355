use std::{
    sync::Arc,
    time::{Duration, Instant},
};

use rand::Rng;

use crate::base::{
    error::PlanningError,
    goal::{Goal, GoalSampleableRegion},
    planner::{Path, Planner},
    problem_definition::ProblemDefinition,
    space::StateSpace,
    state::State,
    validity::StateValidityChecker,
};

// A helper struct to build the tree. Each node stores its state
// and the index of its parent in the tree vector.
#[derive(Clone)]
struct Node<S: State> {
    state: S,
    parent_index: Option<usize>,
}

/// The RRT (Rapidly-exploring Random Tree) planner.
pub struct RRT<S: State, SP: StateSpace<StateType = S>, G: Goal<S>> {
    /// The maximum distance between nodes in the tree. This is the "step size".
    pub max_distance: f64,
    /// The probability of sampling the goal region instead of the whole space (e.g., 0.05 for 5%).
    pub goal_bias: f64,

    problem_def: Option<Arc<ProblemDefinition<S, SP, G>>>,
    validity_checker: Option<Arc<dyn StateValidityChecker<S> + Send + Sync>>,
    tree: Vec<Node<S>>,
}

impl<S, SP, G> RRT<S, SP, G>
where
    S: State,
    SP: StateSpace<StateType = S>,
    G: Goal<S>,
{
    pub fn new(max_distance: f64, goal_bias: f64) -> Self {
        RRT {
            max_distance,
            goal_bias,
            problem_def: None,
            validity_checker: None,
            tree: Vec::new(),
        }
    }

    /// Helper function to check if the motion between two states is valid.
    /// This involves discretizing the path and checking each intermediate step.
    fn check_motion(&self, from: &S, to: &S) -> bool {
        // We need access to the space and checker from our stored setup info.
        if let (Some(pd), Some(vc)) = (&self.problem_def, &self.validity_checker) {
            let space = &pd.space;

            // Determine the number of steps to check based on distance and resolution.
            // A simple approach: one check per unit of distance (or a fraction thereof).
            let dist = space.distance(from, to);
            let num_steps = (dist / (self.max_distance * 0.1)).ceil() as usize;

            if num_steps <= 1 {
                return vc.is_valid(to);
            }

            let mut interpolated_state = from.clone();
            for i in 1..=num_steps {
                let t = i as f64 / num_steps as f64;
                space.interpolate(from, to, t, &mut interpolated_state);
                if !vc.is_valid(&interpolated_state) {
                    return false;
                }
            }

            true
        } else {
            false
        }
    }
}

// The main implementation of the Planner trait for RRT.
impl<S, SP, G> Planner<S, SP, G> for RRT<S, SP, G>
where
    // RRT needs to clone states to store them in its tree.
    S: State + Clone,
    SP: StateSpace<StateType = S>,
    // For goal biasing, the Goal type must be sampleable.
    G: Goal<S> + GoalSampleableRegion<S>,
{
    fn setup(
        &mut self,
        problem_def: Arc<ProblemDefinition<S, SP, G>>,
        validity_checker: Arc<dyn StateValidityChecker<S> + Send + Sync>,
    ) {
        self.problem_def = Some(problem_def);
        self.validity_checker = Some(validity_checker);
        self.tree.clear();

        // Initialize the tree with the start state.
        let start_state = self.problem_def.as_ref().unwrap().start_states[0].clone();
        let start_node = Node {
            state: start_state,
            parent_index: None,
        };
        self.tree.push(start_node);
    }

    fn solve(&mut self, timeout: Duration) -> Result<Path<S>, PlanningError> {
        // Ensure setup has been called.
        let pd = self
            .problem_def
            .as_ref()
            .expect("Planner setup was not called before solve.");
        let goal = &pd.goal;

        let start_time = Instant::now();
        let mut rng = rand::rng();

        loop {
            // 1. Check for timeout
            if start_time.elapsed() > timeout {
                return Err(PlanningError::Timeout);
            }

            // 2. Sample a state (q_rand)
            let q_rand = if rng.random_bool(self.goal_bias) {
                // TODO: assume sample_goal can't fail here for simplicity, but a real implementation would handle the Result.
                goal.sample_goal(&mut rng).unwrap()
            } else {
                // TODO: assume uniform sampling can't fail if bounds are set correctly.
                pd.space.sample_uniform(&mut rng).unwrap()
            };

            // 3. Find the nearest node in the tree (q_near)
            let mut nearest_node_index = 0;
            let mut min_dist = pd.space.distance(&self.tree[0].state, &q_rand);

            for i in 1..self.tree.len() {
                let dist = pd.space.distance(&self.tree[i].state, &q_rand);
                if dist < min_dist {
                    min_dist = dist;
                    nearest_node_index = i;
                }
            }
            let q_near = &self.tree[nearest_node_index].state;

            // 4. Steer from q_near towards q_rand to get q_new
            let mut q_new = q_near.clone();
            if min_dist > self.max_distance {
                // If q_rand is too far, interpolate to a point at max_distance
                let t = self.max_distance / min_dist;
                pd.space.interpolate(q_near, &q_rand, t, &mut q_new);
            } else {
                // If q_rand is close enough, just use it as q_new
                q_new = q_rand;
            }

            // 5. Check if the motion to q_new is valid
            if self.check_motion(q_near, &q_new) {
                // 6. Add q_new to the tree
                let new_node = Node {
                    state: q_new.clone(),
                    parent_index: Some(nearest_node_index),
                };
                let new_node_index = self.tree.len();
                self.tree.push(new_node);

                // 7. Check if the new node satisfies the goal
                if goal.is_satisfied(&q_new) {
                    println!("Solution found after {} nodes.", self.tree.len());
                    let mut path_states = Vec::new();
                    let mut current_index = Some(new_node_index);
                    while let Some(index) = current_index {
                        path_states.push(self.tree[index].state.clone());
                        current_index = self.tree[index].parent_index;
                    }
                    path_states.reverse();
                    return Ok(Path(path_states));
                }
            }
        }
        // Err(PlanningError::NoSolutionFound)
    }
}
