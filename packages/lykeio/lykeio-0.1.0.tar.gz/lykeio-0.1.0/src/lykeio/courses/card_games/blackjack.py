import random

from ...core import StateDescription, Action
from ...base import BaseCourse


class BlackJackCourse(BaseCourse):
    """
    Course to teach an agent to play blackjack.
    """

    def __init__(self):
        super(BlackJackCourse, self).__init__()
        self.player_hand = []
        self.dealer_hand = []
        self.deck = self._shuffle_deck()
        self.current_state = None
        self.action_space = len(self.available_actions())

    def reset(self) -> StateDescription:
        """
        Resets the game to the initial state  
        """
        self.player_hand = []
        self.dealer_hand = []
        self.deck = self._shuffle_deck()
        self._deal_card(self.player_hand)
        self._deal_card(self.player_hand)
        self._deal_card(self.dealer_hand)
        self._deal_card(self.dealer_hand)

        return self._state_description()

    def step(self, action: Action) -> tuple[StateDescription, int|float, bool, bool, dict[str, any]]:
        """
        Processes the player's action and updates the game state.
        """
        # action_str is 'hit' or 'stand'
        action_str = action.action.lower()
        terminated, truncated = False, False

        if action_str == 'hit':
            self._deal_card(self.player_hand)
            player_total = self._hand_value(self.player_hand)

            if player_total > 21:
                reward = -1
                terminated = True
                return (
                    StateDescription('You went over 21. The dealer wins.'),
                    reward,
                    terminated,
                    truncated,
                    {}
                )
            elif player_total < 21:
                reward = 0
                return (
                    self._state_description(),
                    reward,
                    terminated,
                    truncated,
                    {}
                )
            else:
                reward = 1
                terminated = True
                return (
                    StateDescription('Blackjack! You win!'),
                    reward,
                    terminated,
                    truncated,
                    {}
                )

            if action_str == 'stand':
                return self._dealer_turn()

            return (
                StateDescription("Invalid action. Choose between 'hit' or 'stand'."),
                -1000,
                terminated,
                truncated,
                {}
            )
                    
    def available_actions(self) -> list[Action]:
        """
        Returns the available actions: 'hit' or 'stand'.
        """
        action_list = [
            Action(action='hit', description="When you choose 'hit', you request an additional card from the dealer."),
            Action(action='stand', description="When you choose to stand, you decide to end your turn and not take any more cards.")
        ]
        return action_list

    def _dealer_turn(self) -> tuple[StateDescription, int|float, bool, bool, dict[str, any]]:
        """
        Deals card to the dealer.
        """
        terminated, truncated = True, False
        while self._hand_value(self.dealer_hand) < 17:
            self._deal_card(self.dealer_hand)

        player_total = self._hand_value(self.player_hand)
        dealer_total = self._hand_value(self.dealer_hand)

        if dealer_total > 21 or player_total > dealer_total:
            reward = 1
            return (
                StateDescription('The dealer lost, you win!'),
                reward,
                terminated,
                truncated,
                {}
            )
        if dealer_total == player_total:
            reward = 0
            return (
                StateDescription('A draw. Nobody wins')
                reward,
                terminated,
                truncated,
                {}
            )
        if dealer_total > player_total:
            reward = -1
            return (
                StateDescription('The dealer wins, you lose.'),
                reward,
                terminated,
                truncated,
                {}
            )
    
    def _state_description(self) -> StateDescription:
        """
        Returns the state description in natural language.
        """
        player_total = self._hand_value(self.player_hand)
        dealer_card = self.dealer_hand[0]

        description = f"""
        You are playing blackjack.
        The goal is to get a value as close to 21 as possible.
        Each card has a value equal to its number.
        Face cards are worth 10, aces are worth 11 or 1.
        Your hand consists of {self.player_hand}, with a total value of {player_total}
        The dealer shows a {dealer_card}.
        """
        return StateDescription(description=description)

    def _shuffle_deck(self) -> list[int]:
        """
        Initializes a deck of cards and then shuffles it.
        """
        deck = []
        values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        suits = ['Hearts', 'Clubs', 'Spades', 'Diamonds']

        for suits in suits:
            for value in values:
                deck.append((value, suit))
        random.shuffle(deck)
        return deck

    def _deal_card(self, hand: list[int]):
        """
        Deals a single card to a given hand.
        """
        hand.append(self.deck.pop())

    def _hand_value(self, hand: list[int]) -> int:
        """
        Calculates the best possible value for a given hand.
        """
        values = {
            'A': 1, '2': 2, '3': 3,
            '4': 4, '5': 5, '6': 6,
            '7': 7, '8': 8, '9': 9,
            '10': 10, 'J': 10, 'Q': 10, 'K': 10   
        }
        hand_value = [values[i[0]] for i in hand]
        total = sum(hand_value)
        if 'A' in hand and total + 10 <= 21:
            return total + 10
        return total
