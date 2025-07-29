from abc import ABC, abstractmethod

from .core import StateDescription, Action

class BaseCourse(ABC):
    """
    Base class for natural language envs.
    Courses can inherit this to define courses.
    """
    def __init__(self):
        super(BaseCourse, self).__init__()
        self.current_state = None
        self.action_space = len(self.available_actions())

    @abstractmethod
    def reset(self) -> StateDescription:
        """
        Resets the environment to initial state.
        Returns the inital state description
        """
        pass

    @abstractmethod
    def step(self, action: Action) -> tuple[StateDescription, int|float, bool, bool, dict[str, any]]:
        """
        Moves the environment a single timestep based on the action.
        Returns as tuple:
            (StateDescription, reward, truncated, terminated, info)
        """
        pass

    @abstractmethod
    def available_actions(self) -> list[Action]:
        """
        Returns a list of available actions  
        """
        return []
