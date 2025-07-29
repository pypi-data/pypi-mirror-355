import random

class Player:
    def __init__(self, name : str = None, hand : list = None, cards_won : list = None):

        self.name = name if name is not None else ''
        self.hand = hand if hand is not None else []
        self.cards_won = cards_won if cards_won is not None else []

    def set_name(self, name) -> None:
        self.name = name

    def set_hand(self, hand : list) -> None:
        self.hand = hand

    def set_cards_won(self, cards_won : list) -> None:
        """ Extend list of 'cards won' by one or multiple cards """
        self.cards_won.extend(cards_won)

    def remove_duplicates(self) -> None:
        """ Ensures no duplicates in 'cards_won' list """
        only_originals = []
        for card in self.cards_won:
            if card not in only_originals:
                only_originals.append(card)
            else:
                continue
        self.cards_won = only_originals

    def shuffle_cards(self, cards : list) -> list:
        """Shuffle a specific list of cards"""

        shuffled = []
        indexes = []

        while len(indexes) != len(cards):
            rand_int = random.randint(0,len(cards) - 1)
            if rand_int not in indexes:
                indexes.append(rand_int)

        for i in indexes:
            shuffled.append(cards[i])

        return shuffled 

    def consolidate_cards(self) -> None:
        """Combine 'cards won' list into player's main 'hand' list"""

        if len(self.cards_won) > 6:
            self.shuffle_cards(self.cards_won)
            self.hand.extend(self.cards_won)
            self.cards_won.clear()

        

    
