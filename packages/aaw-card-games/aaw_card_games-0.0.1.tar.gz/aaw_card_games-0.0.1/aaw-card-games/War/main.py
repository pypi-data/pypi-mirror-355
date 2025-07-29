from card_games.deck import Deck
from war import PlayWar
from card_games.player import Player

def play_game(game_condition : bool, player1 : Player, player2 : Player) -> None:

    while game_condition:
        game = PlayWar(player1, player2)
        player.consolidate_cards()
        computer.consolidate_cards()

        b = game.battle()

        # Tie
        if b == False:
            w = game.war()
            # Game is over if one player doesn't have enough cards for 'war'
            if w == False:
                break
            
    if len(player1.hand) < len(player2.hand):
        print(f"{player1.name} loses! Better luck next time.")

    elif len(player2.hand) < len(player1.hand):
        print(f"{player2.name} has no cards left! {player1.name} wins!")

    else:
        print(f"The great war between {player1.name} and {player2.name} ends in a draw")

if __name__ == "__main__":

    # Deck object initialization
    deck = Deck()

    # Player objects initialization
    player = Player(input("Enter your name: "))
    computer = Player("Computer")

    # Shuffle Deck
    deck = deck.shuffle()

    # Split deck between players
    split_deck = deck.split()
    player.set_hand(split_deck[0])
    computer.set_hand(split_deck[1])

    # Game condition
    decks_not_zero = len(player.hand) != 0 or len(computer.hand) != 0

    # Welcome, start game
    input(f"Welcome to War, {player.name}. Press 'Enter' to start")
    print("\n")

    # GAME START
    play_game(decks_not_zero, player, computer)