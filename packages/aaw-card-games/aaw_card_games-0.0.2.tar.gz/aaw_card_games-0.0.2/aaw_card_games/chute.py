from aaw_card_games.deck import Deck

class Chute(Deck):
    """
    
    """
    def __init__(self, number_of_decks : int = 6):

        self.number_of_decks = number_of_decks
        self.chute = [Deck().shuffle() for i in range(number_of_decks)]




test = Chute()

print(test.chute)
