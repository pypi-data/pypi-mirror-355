from card_games.card import Card
import random

class Deck(Card):
    """
    Standard playing card deck. 52 cards total (without jokers).
    Custom card values accepted. List of custom card values will be assigned
    in order 'Ace' through 2, so highest to lowest.
    
    Includes shuffle and split methods.
    """

    def __init__(self, card_values : list = [], jokers : bool = False, joker_value : int = 15, num_of_jokers : int = 2):

        self.jokers = jokers
        self.deck = []
        self.suits = ['Spades', 'Clubs', 'Hearts', 'Diamonds']
        self.names = ['Ace', 'King', 'Queen', 'Jack', '10', '9', '8', '7', '6', '5', '4', '3', '2']
        self.values = card_values if card_values else [14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]

        if self.jokers:
            for _ in range(num_of_jokers):
                self.deck.append(Card('Joker', joker_value, 'Joker'))

        for suit in self.suits:
            for name, value in zip (self.names, self.values):
                self.deck.append(Card(name, value, suit))

    def shuffle(self):
        """ Shuffle entire deck """
        shuffled_deck = []
        indexes = []

        while len(indexes) != 52:
            rand_int = random.randint(0, 51)
            if rand_int not in indexes:
                indexes.append(rand_int)

        for i in indexes:
            shuffled_deck.append(self.deck[i])

        self.deck = shuffled_deck
        return self
    
    def split(self):
        """ Split deck in half """
        deck1 = self.deck[:26]
        deck2 = self.deck[26:52]

        return deck1, deck2