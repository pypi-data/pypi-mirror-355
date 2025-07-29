class Card:
    """
        Standard Playing card. Contains a name, a suit, and a value
    """

    def __init__(self, name : str, value : int, suit : str):
        valid_suits = ['spades','hearts','clubs','diamonds','joker']
        valid_names = ['a','k','q','j','10','9','8','7','6','5','4','3','2','ace','king','queen','jack',
                       'ten','nine','eight','seven','six','five','four','three','two','joker']

        self.name = name if name.lower() in valid_names else ValueError("Invalid Name. Please use standard playing card names.")
        self.value = value
        self.suit = suit if suit.lower() in valid_suits else ValueError("Invalid Suit. Suit must be 'Spades','Hearts','Clubs','Diamonds' or 'Joker'")

