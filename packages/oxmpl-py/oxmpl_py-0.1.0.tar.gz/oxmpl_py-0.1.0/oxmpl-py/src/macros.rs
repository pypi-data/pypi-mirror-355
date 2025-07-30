/// A macro to generate a full PyO3 wrapper for a given planner.
///
/// This macro acts as a template to reduce repetitive boilerplate code. It takes a
#[macro_export]
macro_rules! define_planner {
    (
        // $wrapper_name: The name for the Rust struct that will wrap the planner.
        $wrapper_name:ident,
        // $python_name: The name of the class as it will be exposed to Python.
        $python_name:literal,
        // $concrete_planner_ty: The full, concrete Rust type of the planner to be wrapped.
        //   This type alias should be defined *before* calling the macro.
        $concrete_planner_ty:ty,
        // $problem_def_py_ty: The Python wrapper for the ProblemDefinition.
        $problem_def_py_ty:ty,
        // $path_py_ty: The Python wrapper for the resulting Path.
        $path_py_ty:ty
    ) => {
        #[pyclass(name = $python_name, unsendable)]
        struct $wrapper_name {
            planner: Arc<Mutex<$concrete_planner_ty>>,
        }

        #[pymethods]
        impl $wrapper_name {
            #[new]
            fn new(max_distance: f64, goal_bias: f64) -> Self {
                let planner_instance = <$concrete_planner_ty>::new(max_distance, goal_bias);
                Self {
                    planner: Arc::new(Mutex::new(planner_instance)),
                }
            }

            fn setup(
                &mut self,
                problem_def_py: &$problem_def_py_ty,
                validity_callback: PyObject,
            ) -> PyResult<()> {
                let problem_def_rust = problem_def_py.0.clone();
                let checker = Arc::new(PyStateValidityChecker {
                    callback: validity_callback,
                });

                self.planner
                    .lock()
                    .unwrap()
                    .setup(problem_def_rust, checker);

                Ok(())
            }

            fn solve(&mut self, timeout_secs: f32) -> PyResult<$path_py_ty> {
                let timeout = Duration::from_secs_f32(timeout_secs);
                let result = self.planner.lock().unwrap().solve(timeout);

                match result {
                    Ok(path) => Ok(<$path_py_ty>::from_rust_path(path)),
                    Err(e) => Err(pyo3::exceptions::PyException::new_err(e.to_string())),
                }
            }
        }
    };
}
