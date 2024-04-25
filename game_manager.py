from poker_oracle import PokerOracle
from card_deck import Card, CardDeck
from resolver import Resolver
from state_manager import PokerStateManager

class PokerGameManager:
    
    def __init__(self, use_limited_deck=False):
        self.use_limited_deck = use_limited_deck 
        self.poker_agents: list[RolloutPokerAgent | ResolverPokerAgent | HumanPlayer | CombinationPokerAgent] = []
        self.pot = 0
        self.poker_oracle = PokerOracle(use_limited_deck)
        self.public_cards: list[Card] = []
        self.num_chips_bet = 2
        self.small_blind_chips: int = self.num_chips_bet / 2
        self.big_blind_chips: int = self.num_chips_bet
        self.current_bet = self.big_blind_chips
        self.small_blind_player_index = 0 # Needs to "rotate" with modulo operation
        self.current_stage: str = "pre-flop" # "pre-flop", "flop", "turn", "river"
        self.legal_num_raises_per_stage = 2 # To shorten each stage
        
        self.current_game_players = []
        self.current_hand_players = []
        self.current_round_actions = []
    
        
    
    
    # NOTE: Based on "Generate Poker Agents" from slides
    def add_poker_agent(self, agent_type: str, chips: int, name: str) -> None:
        if agent_type == "rollout":
            poker_agent = RolloutPokerAgent(agent_type, chips, name)
        elif agent_type == "resolver":
            poker_agent = ResolverPokerAgent(agent_type, chips, name) # TODO: NOT WORKING!
        elif agent_type == "combination":
            poker_agent = CombinationPokerAgent(agent_type, chips, name) # TODO: NOT WORKING!
        elif agent_type == "human":
            poker_agent = HumanPlayer(agent_type, chips, name)
        self.poker_agents.append(poker_agent)
    
    # NOTE: Based on "Manage Game" from slides
    def run_one_game(self):
        
        self.current_game_players = self.poker_agents
        
        small_blind_index = self.small_blind_player_index
        big_blind_index = (small_blind_index + 1) % len(self.current_game_players)
        
        while len(self.current_game_players) > 1:
            
            for player in self.current_game_players:
                player.current_bet = 0
            self.current_bet = self.big_blind_chips
            self.run_one_hand(small_blind_index, big_blind_index)
            
            small_blind_index = (small_blind_index + 1) % len(self.current_game_players)
            big_blind_index = (small_blind_index + 1) % len(self.current_game_players)
            
            print("Game players:", *self.current_game_players)
            current_chips = [player.num_chips for player in self.current_game_players]
            print("Current chips per player:", *current_chips)
            print()
        
        print("Game winner:", self.current_game_players[0])
        
    
    def run_one_hand(self, small_blind_index, big_blind_index):
        # Assumes two or more players
        # Run one hand to showdown
        self.current_hand_players = self.current_game_players[:]
        
        card_deck: CardDeck = self.poker_oracle.get_deck_of_cards()
        card_deck.shuffle()
        for player in self.current_hand_players:
            player.recieve_hole_cards(card_deck.deal(2))
        while len(self.current_hand_players) > 1:
            card_deck: CardDeck = self.poker_oracle.get_deck_of_cards()
            card_deck.shuffle()
            if not self.public_cards == []:
                card_deck.exclude(self.public_cards)
            for player in self.current_game_players:
                card_deck.exclude(player.hole_cards)
            print()
            print(f"============ Sart of {self.current_stage} stage ============")
            self.run_one_stage(card_deck, small_blind_index, big_blind_index)
            print("Players remaining in hand:", *self.current_hand_players, "after stage", self.current_stage)
            
            # This assumes that one can only have showdown after river stage
            winners = []
         
            if not self.current_stage == 'river':
                self.current_stage = PokerStateManager.get_next_stage(self.current_stage)
            else:
                # Assuming player wins because opponent folded or won in showdown
                if len(self.current_hand_players) >= 2:
                    print(f"SHOWDOWN with {len(self.current_hand_players)} players!")
                    
                    for player in self.current_hand_players:
                        for opponent in self.current_hand_players:
                            is_winner = True
                            if player == opponent:
                                continue
                            winner = self.poker_oracle.evaluate_showdown(self.public_cards, player.hole_cards, opponent.hole_cards)
                            if winner == -1:
                                is_winner = False
                                break
                        if is_winner:
                            winners.append(player)
                    break
                       
            if len(self.current_hand_players) == 1:
                winners.append(self.current_hand_players[0])
        
        
        # Winner recieves pot
        if len(winners) > 1:
            print("No winner, split pot!")
            # Split pot if two players are tied. (Using integer division to avoid floating point numbers)
            for player in self.current_hand_players:
                player.recieve_winnings(self.pot//len(winners))  # NOTE: May get weird if there are an odd number of winners.
        else:        
            print(f"Player {self.current_hand_players[0]} won the hand and a pot of {self.pot} chips!")
            self.current_hand_players[0].recieve_winnings(self.pot)
        # Reset pot to prepare for new hand
        self.pot = 0
        
        # Remove out of chips players
        for player in self.current_game_players:
            if player.num_chips == 0:
                print(f"Player {player} is out of chips!")
                self.current_game_players.remove(player)
            
        print(f"Number of players remaining in game: {len(self.current_game_players)}")
        
        # Reset public cards and stage for next hand
        self.public_cards = []
        self.current_stage = "pre-flop"
        
            
    def run_one_stage(self, card_deck: CardDeck, small_blind_index: int, big_blind_index: int):    
            legal_num_raises = self.legal_num_raises_per_stage
            self.current_round_actions = []
            
            # Deal out public new public cards for stage
            self.public_cards = [*self.public_cards, *self.deal_public_cards(card_deck)]
            
            # Small and big blind only has to "buy in" in pre-flop stage
            # In later stages, small blind is just the first to act.
            if self.current_stage == "pre-flop":

                legal_num_raises = self.run_buy_in_round(legal_num_raises, small_blind_index, big_blind_index)
            
                if self.can_go_to_next_hand(self.current_hand_players):
                    return 

                if PokerStateManager.can_go_to_next_stage(self.current_round_actions):
                    return
            
            players_in_order = [*self.current_hand_players[small_blind_index:], *self.current_hand_players[:small_blind_index]]
            
            remove_folded_players = False # NOTE: Don't remove folded players directly after buy in round. May cause crash if someone folded in buy in round.
            
            while not (PokerStateManager.can_go_to_next_stage(self.current_round_actions) or self.can_go_to_next_hand(self.current_hand_players)):
                print()
                print(f"============ New round in {self.current_stage} stage ============")
                # Update player order if someone folded
                if remove_folded_players:
                    while "fold" in self.current_round_actions:
                        fold_player_index = self.current_round_actions.index("fold")
                        players_in_order.remove(players_in_order[fold_player_index]) 
                        self.current_round_actions.remove(self.current_round_actions[fold_player_index])
                        
                remove_folded_players = True
                self.current_round_actions = []
                
                for player in players_in_order:
                    # For last player, check if all other players have folded, then that player wins the pot
                    if len(self.current_hand_players) == 1:
                        # No need for player to decide action, because all other players have folded
                        break
                    if isinstance(player, HumanPlayer):
                        game_snapshot = {"small_blind_player": self.current_hand_players[small_blind_index],
                             "big_blind_player": self.current_hand_players[big_blind_index],
                             "public_cards": self.public_cards,
                             "pot": self.pot,
                             "table_bet": self.current_bet,
                             "stage": self.current_stage
                             }
            
                        game_snapshot["all_player_bets"] = []
                        game_snapshot["all_player_chips"] = []
                        for round_player in self.current_hand_players:
                            if not round_player.name == player.name: 
                                game_snapshot["all_player_bets"].append((round_player.name, player.current_bet))
                                game_snapshot["all_player_chips"].append((round_player.name, player.num_chips))
                        desired_action = player.get_action(self.public_cards, game_snapshot)
                    else:
                        desired_action = player.get_action(self.public_cards, len(self.current_hand_players) - 1, 100, self.poker_oracle)
                    played_action, legal_num_raises = self.handle_desired_action(player, desired_action, legal_num_raises)
                    if not desired_action == played_action:
                        print(f"Player {player.name} wanted to {desired_action} but had to {played_action}")
                        print()
                    else:
                        print(f"Player {player.name} decided to {played_action}")
                        print()
                    self.current_round_actions.append(played_action)            

            
    def run_buy_in_round(self, legal_num_raises: int, small_blind_index: int, big_blind_index: int):
        self.current_round_actions = []
        small_blind_index = small_blind_index
        big_blind_index = big_blind_index
        initial_player_count = len(self.current_hand_players)
        
        for i in range(initial_player_count):
            
            if initial_player_count > len(self.current_hand_players):
                i, small_blind_index, big_blind_index = self.adjust_player_index_for_removal(i, small_blind_index, big_blind_index, initial_player_count)
                   
            game_snapshot = {"small_blind_player": self.current_hand_players[small_blind_index],
                             "big_blind_player": self.current_hand_players[big_blind_index],
                             "public_cards": self.public_cards,
                             "table_bet": self.current_bet,
                             "pot": self.pot,
                             "stage": self.current_stage
                             }
            
            game_snapshot["all_player_bets"] = []
            game_snapshot["all_player_chips"] = []
            for player in self.current_hand_players:
                if not player.name == self.current_hand_players[i].name:
                    game_snapshot["all_player_bets"].append((player.name, player.current_bet))
                    game_snapshot["all_player_chips"].append((player.name, player.num_chips))
                
            print_player = self.current_hand_players[i].name
            played_action = ""
            if i == small_blind_index: 
                if self.current_hand_players[i].num_chips < self.small_blind_chips:
                    # If not enough chips for small blind, player is out
                    print(f"Player {self.current_hand_players[i]} cannot afford small blind and is out of game!")
                    self.pot += self.current_hand_players[i].bet(self.small_blind_chips)
                    played_action, self.current_hand_players = PokerStateManager.handle_fold(self.current_hand_players[i], self.current_hand_players)
                else:
                    self.pot += self.current_hand_players[i].bet(self.small_blind_chips)
                    game_snapshot["pot"] = self.pot
                    if isinstance(self.current_hand_players[i], HumanPlayer):
                        desired_action = self.current_hand_players[i].get_action(self.public_cards, game_snapshot)
                    else:
                        desired_action = self.current_hand_players[i].get_action(self.public_cards, len(self.current_hand_players) - 1, 100, self.poker_oracle)
                    played_action, legal_num_raises = self.handle_desired_action(self.current_hand_players[i], desired_action, legal_num_raises)
                    if not desired_action == played_action:
                        print(f"Player {print_player} wanted to {desired_action} but had to {played_action}")
                        print()
                    else:
                        print(f"Player {print_player} decided to {played_action}")
                        print()
            elif i == big_blind_index:
                if self.current_hand_players[i].num_chips < self.big_blind_chips:
                    # If not enough chips for big blind, player is out
                    print(f"Player {self.current_hand_players[i]} cannot afford big blind and is out of game!")
                    self.pot += self.current_hand_players[i].bet(self.big_blind_chips) 
                    played_action, self.current_hand_players = PokerStateManager.handle_fold(self.current_hand_players[i], self.current_hand_players)
                else:
                    self.pot += self.current_hand_players[i].bet(self.big_blind_chips)
                    if isinstance(self.current_hand_players[i], HumanPlayer):
                        desired_action = self.current_hand_players[i].get_action(self.public_cards, game_snapshot)
                    else:
                        desired_action = self.current_hand_players[i].get_action(self.public_cards, len(self.current_hand_players) - 1, 100, self.poker_oracle)
                    played_action, legal_num_raises = self.handle_desired_action(self.current_hand_players[i], desired_action, legal_num_raises)
                    if not desired_action == played_action:
                        print(f"Player {print_player} wanted to {desired_action} but had to {played_action}")
                        print()
                    else:
                        print(f"Player {print_player} decided to {played_action}")
                        print()
            else:
                try:
                    if isinstance(self.current_hand_players[i], HumanPlayer):
                        desired_action = self.current_hand_players[i].get_action(self.public_cards, game_snapshot)
                    else:
                        desired_action = self.current_hand_players[i].get_action(self.public_cards, len(self.current_hand_players) - 1, 100, self.poker_oracle)
                except:
                    print(f"Player index {i}")
                    print(f"Number of players {len(self.current_hand_players)}")
                    print(f"Player {small_blind_index}, {self.current_hand_players[small_blind_index]}")
                    print(f"Player {big_blind_index}, {self.current_hand_players[big_blind_index]}")
                    print()
                played_action, legal_num_raises = self.handle_desired_action(self.current_hand_players[i], desired_action, legal_num_raises)
                if not desired_action == played_action:
                    print(f"Player {print_player} wanted to {desired_action} but had to {played_action}")
                    print()
                else:
                    print(f"Player {print_player} decided to {played_action}")
                    print()
                
            self.current_round_actions.append(played_action)
        
        return legal_num_raises
            
               
    def adjust_player_index_for_removal(self, i, small_blind_index, big_blind_index, initial_player_count):
        num_removed_players = initial_player_count - len(self.current_hand_players)
        
        i = (i - num_removed_players) % len(self.current_hand_players)
        small_blind_index = (small_blind_index - num_removed_players) % len(self.current_hand_players)
        big_blind_index = (big_blind_index - num_removed_players) % len(self.current_hand_players)
        
        return i, small_blind_index, big_blind_index
    
                
    def handle_desired_action(self, player, desired_action: str, legal_num_raises: int):
        played_action = desired_action
        if desired_action == "fold":
            played_action, self.current_hand_players = PokerStateManager.handle_fold(player, self.current_hand_players)
        if desired_action == "call":
            bet_amount, played_action, self.current_hand_players = PokerStateManager.handle_call(player, self.current_bet ,self.current_hand_players)
            self.pot += bet_amount
        if desired_action == "raise":
            if legal_num_raises > 0:               
                bet_amount, played_action, legal_num_raises, self.current_hand_players = PokerStateManager.handle_raise(player, legal_num_raises, self.current_bet, self.big_blind_chips, self.current_hand_players)
                self.current_bet = player.current_bet
            else:
                bet_amount, played_action, self.current_hand_players = PokerStateManager.handle_call(player, self.current_bet, self.current_hand_players)
            self.pot += bet_amount
        return played_action, legal_num_raises
        
    def can_go_to_next_hand(self, players_remaining_in_hand) -> bool:
        return len(players_remaining_in_hand) == 1
    
    
    def deal_public_cards(self, card_deck: CardDeck) -> list[Card]:
        if self.current_stage == "pre-flop":
            return []
        if self.current_stage == "flop":
            return card_deck.deal(3)
        if self.current_stage == "turn":
            return card_deck.deal(1)
        if self.current_stage == "river":
            return card_deck.deal(1)

    
    def prepare_new_game(self, keep_players: bool):
        if not keep_players:
            self.poker_agents = []
        self.pot = 0
        self.public_cards = []
        
    def set_small_blind_chips(self, num_chips: int):
        self.small_blind_chips = num_chips
        
    def set_big_blind_chips(self, num_chips: int):
        self.big_blind_chips = num_chips
    
    # NOTE: Based on "Monitor Players" from slides
    def monitor_players():
        pass
    
    # NOTE: Based on "Texas Hold'em Simulator" from slides
    def texas_holdem_simulator(self, num_players: int, num_games: int):
        pass
    
    # TODO: Add method for taking a "snapshot" of the game state and initialize a state object to be used in the resolver.
    # This will be called each time a player capable of using the resolver is to make a decision. Maybe this should be a Agent method and not Game Manager method.
    
    
class PokerAgent():
    def __init__(self, type: str, initial_chips: int, name: str):
        self.name = name
        self.type = type
        self.num_chips = initial_chips
        self.hole_cards: list[Card] = None
        self.current_bet = 0
        
    def __str__(self) -> str:
        return self.type + " " + self.name
        
    def recieve_hole_cards(self, hole_cards: list[Card]):
        self.hole_cards = hole_cards
    
    # I think this is reasonable
    def bet(self, num_chips: int) -> int:
        if self.num_chips > num_chips:
            self.current_bet += num_chips
            self.num_chips -= num_chips
        else:
            self.current_bet += self.num_chips
            self.num_chips = 0
        
        return self.current_bet
    
    def recieve_winnings(self, num_chips: int) -> None:
        self.num_chips += num_chips
    
    def get_action(self, public_cards: list[Card], num_opponents: int, poker_oracle: PokerOracle) -> str:
        pass


class RolloutPokerAgent(PokerAgent):
    def __init__(self, type: str, initial_chips: int, name: str):
        super().__init__(type, initial_chips, name)
    
    # Implementing get action for a pure rollout based agent
    def get_action(self, public_cards: list[Card], num_opponents: int, rollout_count: int, poker_oracle: PokerOracle) -> str:
        # TODO: Should get probabilities from a pre-generated (and preferably saved) cheat sheet
        # TODO: Probability thresholds should be initialization paramaters
        # TODO: The probabilities could vary depending on stage of the game
        # TODO: Should have a probaibility of bluffin, i.e. a probability of raining with a bad hand (when you actually want to fold)
        if public_cards == []:
            try:
                OPPONENTS = 6
                ROLLOUTS = 1000
                cheat_sheet = poker_oracle.load_cheat_sheet(OPPONENTS, ROLLOUTS)
                win_probability = poker_oracle.get_cheat_sheet_hole_pair_probabilitiy(self.hole_cards, num_opponents, cheat_sheet)
            except:
                 win_probability = poker_oracle.rollout_hole_pair_evaluator(self.hole_cards, public_cards, num_opponents, rollout_count)
        else:
            win_probability = poker_oracle.rollout_hole_pair_evaluator(self.hole_cards, public_cards, num_opponents, rollout_count) 
        if win_probability >= 0.3:
            action = "raise"
        if win_probability >= 0.05:
            action = "call"
        else:
            action = "fold" 
        return action
        
        
class ResolverPokerAgent(PokerAgent):
    def __init__(self, type: str, initial_chips: int, name: str):
        super().__init__(type, initial_chips, name)
    
    def get_action(self, public_cards: list[Card], num_opponents: int, poker_oracle: PokerOracle) -> str:
        pass
        
        
class CombinationPokerAgent(PokerAgent):
    def __init__(self, type: str, initial_chips: int, name: str):
        super().__init__(type, initial_chips, name)
    
    def get_action(self, public_cards: list[Card], num_opponents: int, poker_oracle: PokerOracle) -> str:
        pass        


class HumanPlayer(PokerAgent):
    def __init__(self, type: str, initial_chips: int, name: str):
        super().__init__(type, initial_chips, name)
    
    def get_action(self, public_cards: list[Card], game_snapshot) -> str:
        hole_cards = [str(card) for card in self.hole_cards]
        public_cards = [str(card) for card in public_cards]
        index_to_action = {"0": "fold", "1": "call", "2": "raise"}
        pot = game_snapshot["pot"]
        table_bet = game_snapshot["table_bet"]
        all_player_bet = game_snapshot["all_player_bets"]
        all_player_chips = game_snapshot["all_player_chips"]
        small_blind = game_snapshot["small_blind_player"]
        big_blind = game_snapshot["big_blind_player"]
        print(f"Player {self.name}'s turn!")
        print("Cards:")
        print(f"Your hole cards: {hole_cards}")
        print(f"Public cards: {public_cards}")
        print("Pot, bets and piles:")
        print(f"Current pot: {pot}")
        print(f"Bet on table: {table_bet}")
        print(f"Your current bet: {self.current_bet}")
        print(f"Other players current bet: {all_player_bet}")
        print(f"Number of chips for call: {table_bet - self.current_bet if table_bet > self.current_bet else 0}")
        print(f"Your pile of chips: {self.num_chips}")
        print(f"Other players piles of chips: {all_player_chips}")
        print("Blinds:")
        print(f"Player {small_blind} is small blind")
        print(f"Player {big_blind} is big blind")
        print("Choose action: 0 (fold), 1 (call), 2 (raise)")
        action_index = ""
        while action_index not in list(index_to_action.keys()):
            action_index = input("> ")
        action = index_to_action[action_index]
        return action
    
    
if __name__ == "__main__":
    
    use_limited_deck = True
    
    game_manager = PokerGameManager(use_limited_deck=use_limited_deck)
    print(game_manager.poker_oracle.get_deck_of_cards())
    print(f"Number of cards: {len(game_manager.poker_oracle.get_deck_of_cards().cards)}") # NOTE: Somehow more chips are added...
    game_manager.add_poker_agent("rollout", 30, "Alice")
    # game_manager.add_poker_agent("human", 30, "Hans")
    game_manager.add_poker_agent("rollout", 30, "Bob")
    game_manager.add_poker_agent("rollout", 30, "Chris")
    # game_manager.add_poker_agent("rollout", 30, "Dave")
    # game_manager.add_poker_agent("rollout", 30, "Eric")
    # game_manager.add_poker_agent("rollout", 30, "Fred")
    
    game_manager.run_one_game()
    