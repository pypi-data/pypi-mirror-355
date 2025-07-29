from card_games.player import Player
import time

class PlayWar(Player):

    def __init__(self, player1 : Player, player2: Player):
        
        # Players
        self.player1 = player1
        self.player2 = player2
        
        # Players' top card
        self.p1_topcard = self.player1.hand[0]
        self.p2_topcard = self.player2.hand[0]

        # Container to hold all cards in play
        self.arena = []

    def card_compare(self) -> int:
        """Compares values of two cards"""

        if self.p1_topcard.value > self.p2_topcard.value:
            return 0
        elif self.p1_topcard.value < self.p2_topcard.value:
            return 1
        else:
            return 2
        
    def not_enough_cards(self, min : int = 4) -> str | bool:
        """
        Returns false if players have enough cards for 'war', else returns which player
        doesn't have enough cards.
        """

        if len(self.player1.hand) < min:
            return self.player1.name
        elif len(self.player2.hand) < min:
            return self.player2.name
        else:
            return False

    def round_summary(self) -> None:
            """ Displays how many cards each player has to keep track of 'score' """
            print(f"{self.player1.name} has {len(self.player1.hand) + len(self.player1.cards_won)} cards")
            print(f"{self.player2.name} has {len(self.player2.hand) + len(self.player2.cards_won)} cards")
            print("\n")
            input("Press 'Enter' to play next hand")
            print("\n")     
        
    def battle(self, war : bool = False) -> str | bool:
        """
        Each players' top card is compared. 
        The player with the higher value card wins their opponent's card
        """

        # Top card for each player
        self.p1_topcard = self.player1.hand[0]
        self.p2_topcard = self.player2.hand[0]

        """Card reveal Dialogue"""
        print(f"{self.player1.name} shows a {self.p1_topcard.name} of {self.p1_topcard.suit}")
        time.sleep(1)
        print(f"{self.player2.name} shows a {self.p2_topcard.name} of {self.p2_topcard.suit}")
        print("\n")
        time.sleep(1)

        # Add both top cards to 'arena'
        self.arena.extend([self.p1_topcard, self.p2_topcard])

        # Remove both top cards from each player's deck
        self.player1.hand.pop(0)
        self.player2.hand.pop(0)

        """Battle"""
        # Compare card values
        compare = self.card_compare()

        # Declare winner, award winner all self.arena cards
        if compare == 0:
            print(f"{self.p1_topcard.name} beats {self.p2_topcard.name}. {self.player1.name} wins")
            print("\n")
            time.sleep(1)
            self.player1.set_cards_won(self.arena)
            self.player1.remove_duplicates()
            if not war:
                self.round_summary()
            return "player1 wins"

        elif compare == 1:
            print(f"{self.p2_topcard.name} beats {self.p1_topcard.name}. {self.player2.name} wins")
            print("\n")
            time.sleep(1)
            self.player2.set_cards_won(self.arena)
            self.player2.remove_duplicates()
            if not war:
                self.round_summary()
            return "player2 wins"
        
        else: 
            print(f"{self.player1.name} and {self.player2.name} each have a {self.p1_topcard.name}! We have a War!")
            print("\n")
            time.sleep(1)
            return False
        

        
    def war(self) -> None | bool:
        """
        If both players' top card is the same value, each player pulls three cards
        from their decks and places them into the arena face down. Then each player 
        pulls one more card from the top and compare values. The highest value breaks the tie
        and the winning player wins all 10 cards.
        """

        # Winner false until tie is broken
        winner = False

        # Check if each player has enough cards for war
        if self.not_enough_cards():
            print(f"{self.not_enough_cards} does not have enough cards to wage war!")
            print("\n")
            return False

        # Players' next three cards
        p1_facedown = self.player1.hand[0:3]
        p2_facedown = self.player2.hand[0:3]

        # All cards added to self.arena
        self.arena.extend(p1_facedown)
        self.arena.extend(p2_facedown)

        # All arena cards removed from players' decks
        for i in range(len(p1_facedown)):
            self.player1.hand.pop(0)
            self.player2.hand.pop(0)

        """Three card draw"""
        print(f"{self.player1.name} and {self.player2.name} each place 3 cards face down")
        time.sleep(1)
        print(".")
        time.sleep(1)
        print("..")
        time.sleep(1)
        print("...")
        time.sleep(1)
        print("Each player then reveals their next card.")
        time.sleep(1)
        print("\n")

        # Winner is awarded all arena cards
        while winner == False:

            b = self.battle(war=True)

            if b == "player1 wins":
                self.player1.set_cards_won(self.arena)
                self.player1.remove_duplicates()
                self.round_summary()
                winner = True

            elif b == "player2 wins":
                self.player2.set_cards_won(self.arena)
                self.player2.remove_duplicates()
                self.round_summary()
                winner = True

            else:
                print(f"{self.player1.name} and {self.player2.name} have the same cards again! The war continues!")