use std::f64::consts::PI;

pub trait State: Clone + Send + Sync + 'static {}

#[derive(Clone, Debug, PartialEq)]
pub struct RealVectorState {
    pub values: Vec<f64>,
}
impl State for RealVectorState {}

#[derive(Clone, Debug, PartialEq)]
pub struct SO2State {
    pub value: f64,
}
impl SO2State {
    pub fn new(val: f64) -> Self {
        SO2State {
            value: (val + PI).rem_euclid(2.0 * PI) - PI,
        }
    }

    pub fn normalise(&mut self) -> Self {
        SO2State {
            value: (self.value + PI).rem_euclid(2.0 * PI) - PI,
        }
    }
}
impl State for SO2State {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_real_vector_state_creation() {
        let state = RealVectorState {
            values: vec![1.0, 2.0],
        };
        assert_eq!(state.values, vec![1.0, 2.0]);
    }

    #[test]
    fn test_real_vector_state_clone() {
        let state1 = RealVectorState {
            values: vec![1.0, 2.0],
        };
        let state2 = state1.clone();
        assert_eq!(state1, state2);
    }

    #[test]
    fn test_so2_state_creation() {
        let state = SO2State { value: 1.0 };
        assert_eq!(state.value, 1.0);
    }

    #[test]
    fn test_so2_state_clone() {
        let state1 = SO2State { value: 1.0 };
        let state2 = state1.clone();
        assert_eq!(state1, state2);
    }

    #[test]
    fn test_so2_state_normalise() {
        let mut state1 = SO2State { value: 3.0 * PI / 2.0 };
        let state2 = state1.normalise();
        assert_eq!(state2.value, -PI / 2.0);
    }
}
