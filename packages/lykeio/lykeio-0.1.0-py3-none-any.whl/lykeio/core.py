class StateDescription:
    """
    A class to represent the current state in natural language.
    """

    def __init__(self, description: str):
        if not isinstance(description, str):
            raise ValueError("StateDescription must be type string.")
        self.description = description

    def __str__(self) -> str:
        return self.description

    def __repr__(self) -> str:
        return f"StateDescription(description={self.description!r})"

class Action:
    """
    Represent an action in natural language environments.
    """

    def __init__(self, action: any, description: str):
        """
        Args:
            action: Actionable input (e.g. an int),
            description: Natural language description of the action.
        """
        self.action = action
        self.description = description

    def __eq__(self, other):
        if isinstance(other, Action):
            return self.action == other.action
        return False

    def __hash__(self):
        return hash(self.action)

    def __repr__(self):
        return f"Action(action={self.action}, description='{self.description}')
