use pyo3::prelude::*;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use crate::base::{PyGoal, PyPath, PyProblemDefinition, PyStateValidityChecker};
use oxmpl::base::{
    planner::Planner,
    state::RealVectorState,
    space::RealVectorStateSpace,
};
use oxmpl::geometric::planners::rrt::RRT;

type RrtForRealVector = RRT<RealVectorState, RealVectorStateSpace, PyGoal>;
define_planner!(
    PyRrtRv,                // The Rust wrapper struct name
    "RRT",                  // The Python class name
    RrtForRealVector,       // The concrete Rust planner type
    PyProblemDefinition,    // The PyO3 ProblemDefinition wrapper
    PyPath                  // The PyO3 Path wrapper
);

pub fn create_module(py: Python<'_>) -> PyResult<Bound<'_, PyModule>> {
    let geometric_module = PyModule::new(py, "geometric")?;
    let planners_module = PyModule::new(py, "planners")?;

    planners_module.add_class::<PyRrtRv>()?;

    geometric_module.add_submodule(&planners_module)?;
    // parent_module.add_submodule(&geometric_module)?;
    Ok(geometric_module)
}
