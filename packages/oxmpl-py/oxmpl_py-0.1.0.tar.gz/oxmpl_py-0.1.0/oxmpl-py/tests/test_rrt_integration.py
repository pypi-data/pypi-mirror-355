import pytest
import math
import random

# Import the necessary classes from your Rust-based Python module.
# The `from ... import ...` syntax is used for convenience.
import oxmpl_py
# from oxmpl_py.base import RealVectorState, RealVectorStateSpace, ProblemDefinition
# from oxmpl_py.geometric.planners import RRT

# --- Helper Classes and Functions for the Test ---

class CircularGoal:
    """
    A Python class that defines a goal region for the planner.
    The Rust binding code will call these methods.
    """
    def __init__(self, space: oxmpl_py.base.RealVectorStateSpace, x: float, y: float, radius: float):
        self.space = space
        self.target = oxmpl_py.base.RealVectorState([x, y])
        self.radius = radius
        # Seed a random number generator for deterministic goal sampling
        self.rng = random.Random(123)

    def is_satisfied(self, state: oxmpl_py.base.RealVectorState) -> bool:
        """Checks if a state is within the goal region."""
        # This will call the Rust `distance` method on the space object.
        return self.space.distance(self.target, state) <= self.radius

    def sample_goal(self) -> oxmpl_py.base.RealVectorState:
        """Generates a random state from within the goal region."""
        angle = self.rng.uniform(0, 2 * math.pi)
        # Taking the sqrt of a uniform sample gives a uniform distribution over a disk's area.
        radius = self.radius * math.sqrt(self.rng.uniform(0, 1))
        
        x = self.target.values[0] + radius * math.cos(angle)
        y = self.target.values[1] + radius * math.sin(angle)
        return oxmpl_py.base.RealVectorState([x, y])

def is_state_valid(state: oxmpl_py.base.RealVectorState) -> bool:
    """
    A simple Python function to act as a state validity checker.
    This function defines a vertical wall obstacle in the middle of the space.
    """
    x, y = state.values
    
    # Define the wall properties
    wall_x_pos = 5.0
    wall_y_min = 2.0
    wall_y_max = 8.0
    wall_thickness = 0.5
    
    # Check if the state is inside the wall's bounding box
    is_in_wall = (x >= wall_x_pos - wall_thickness / 2.0 and
                  x <= wall_x_pos + wall_thickness / 2.0 and
                  y >= wall_y_min and
                  y <= wall_y_max)
                  
    # The state is valid if it is NOT in the wall
    return not is_in_wall

def test_rrt_solves_problem_with_wall():
    """
    An integration test that sets up a planning problem and verifies
    that the RRT planner can find a valid solution.
    """
    # 1. DEFINE THE STATE SPACE
    # A 10x10 2D world
    space = oxmpl_py.base.RealVectorStateSpace(dimension=2, bounds=[(0.0, 10.0), (0.0, 10.0)])

    # 2. DEFINE THE PROBLEM
    start_state = oxmpl_py.base.RealVectorState([1.0, 5.0])
    # The user creates their goal logic in a Python class instance
    goal_region = CircularGoal(space, x=9.0, y=5.0, radius=0.5)

    # The ProblemDefinition wrapper takes the Python objects
    problem_def = oxmpl_py.base.ProblemDefinition(space, start_state, goal_region)

    # 3. CREATE AND SETUP THE PLANNER
    # Instantiate the Rust RRT planner from Python
    planner = oxmpl_py.geometric.planners.RRT(max_distance=0.5, goal_bias=0.05)

    # Setup the planner, passing the Python function `is_state_valid`
    # and the Python class instance `goal_region` as callbacks.
    planner.setup(problem_def, is_state_valid)

    # 4. SOLVE THE PROBLEM
    print("\nAttempting to solve planning problem...")
    try:
        # Solve with a 5-second timeout
        path = planner.solve(timeout_secs=20.0)
        print(f"Solution found with {len(path.states)} states.")
    except Exception as e:
        # If the planner fails, fail the test with a helpful message
        pytest.fail(f"Planner failed to find a solution when one should exist. Error: {e}")

    # 5. VALIDATE THE SOLUTION PATH
    # The path should not be empty
    assert len(path.states) > 1, "Path should contain at least a start and end state."

    # The path should start at the beginning
    path_start = path.states[0]
    assert space.distance(path_start, start_state) < 1e-9, "Path must start at the start state."

    # The path must end in the goal region
    path_end = path.states[-1]
    assert goal_region.is_satisfied(path_end), "Path must end inside the goal region."

    # Every state and every motion segment in the path must be valid
    for state in path.states:
        assert is_state_valid(state), f"Path contains an invalid state: {state.values}"
    
    print("Path validation successful!")

# To run this test:
# 1. Make sure you have pytest installed: `pip install pytest`
# 2. Save this code as a Python file (e.g., `test_integration.py`) in your `oxmpl-py` directory.
# 3. Run pytest from your terminal in that directory: `pytest -v`

