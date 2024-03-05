from poker_oracle import PokerOracle
from card_deck import Card, CardDeck


class PokerGameManager:
    
    def __init__(self):
        self.poker_agents: list[RolloutPokerAgent | ResolverPokerAgent | HumanPlayer | CombinationPokerAgent] = []
        self.pot = 0
        self.current_bet = 0
        self.poker_oracle = PokerOracle()
        self.public_cards: list[Card] = []
        self.num_chips_bet = 2
        self.small_blind_player = None
        self.small_blind_chips: int = self.num_chips_bet / 2
        self.big_blind_player = None
        self.big_blind_chips: int = self.num_chips_bet
        self.small_blind_player_index = 0 # Needs to "rotate" with modulo operation
        self.current_stage: str = "pre-flop" # "pre-flop", "flop", "turn", "river"
        self.legal_num_raises_per_stage = 2 # To shorten each stage
    
    # NOTE: Based on "Generate Poker Agents" from slides
    def add_poker_agent(self, agent_type: str, chips: int, name: str) -> None:
        if agent_type == "rollout":
            poker_agent = RolloutPokerAgent(agent_type, chips, name)
        elif agent_type == "resolver":
            poker_agent = ResolverPokerAgent(agent_type, chips, name) # TODO: NOT WORKING!
        elif agent_type == "combination":
            poker_agent = CombinationPokerAgent(agent_type, chips, name)
        elif agent_type == "human":
            poker_agent = HumanPlayer(agent_type, chips, name)
        self.poker_agents.append(poker_agent)
    
    # NOTE: Based on "Manage Game" from slides
    def run_one_game(self):
        
        game_players = self.poker_agents
        while len(game_players) > 1:
            game_players = self.run_one_hand(game_players)
            print("Game players:", game_players)
            
        print("Game winner:", game_players[0])
    
    def run_one_hand(self, players):
        # Assumes two or more players
        # Run one hand to showdown
        players_remaining_in_game = players
        small_blind_index = self.small_blind_player_index
        big_blind_index = (small_blind_index + 1) % len(players_remaining_in_game)
        while len(players_remaining_in_game) > 1:
            card_deck: CardDeck = self.poker_oracle.get_deck_of_cards()
            card_deck.shuffle()
            if not self.public_cards == []:
                card_deck.exclude(self.public_cards)
            for player in players_remaining_in_game:
                player.recieve_hole_cards(card_deck.deal(2))
                card_deck.exclude(player.hole_cards)
            players_remaining_in_game = self.run_one_stage(players_remaining_in_game, self.current_stage, card_deck, small_blind_index, big_blind_index)
            print("Players remaining in hand:", players_remaining_in_game)
            small_blind_index = (small_blind_index + 1) % len(players_remaining_in_game)
            big_blind_index = (small_blind_index + 1) % len(players_remaining_in_game)
            
            winner=""
            if not self.current_stage == 'river':
                self.update_stage()
            else:
                # Assuming player wins because opponent folded or won in showdown
                # Also assuming two players
                if len(players_remaining_in_game) == 2:
                    p1 = players_remaining_in_game[0]
                    p2 = players_remaining_in_game[1]
                    winner = self.poker_oracle.evaluate_showdown(self.public_cards, p1.hole_cards, p2.hole_cards)
                if len(players_remaining_in_game) == 1:
                    winner = players_remaining_in_game[0]
        
        # Reset pot to prepare for new game
        self.pot = 0
        self.public_cards = []
        
        print(f"Player {winner} won the hand and a pot of {self.pot} chips!")
        return players_remaining_in_game
            
    def run_one_stage(self, players, stage: str, card_deck: CardDeck, small_blind_index: int, big_blind_index: int):    
            players_remaining_in_stage = players
            legal_num_raises = self.legal_num_raises_per_stage

            # Deal out public new public cards for stage
            self.public_cards = [*self.public_cards, *self.deal_public_cards(card_deck, stage)]
            
            # Small and big blind only has to "buy in" in pre-flop stage
            # In later stages, small blind is just the first to act.
            if stage == "pre-flop":
                players_remaining_in_stage, round_actions = self.run_buy_in_round(players_remaining_in_stage, legal_num_raises, small_blind_index, big_blind_index)
            
                if self.can_go_to_next_hand(players_remaining_in_stage):
                    return players_remaining_in_stage

                if self.can_go_to_next_stage(round_actions):
                    return players_remaining_in_stage
            
            players_in_order = [*players_remaining_in_stage[small_blind_index:], *players_remaining_in_stage[:small_blind_index]]
            
            # TODO: SHOULD BE CONSTRAINED BY LEGAL NUM RAISES! NEED TO ENSURE THAT I HAVE IMPLEMENTED THIS!!!!!
            round_actions = []
            while not self.can_go_to_next_stage(round_actions) or not self.can_go_to_next_hand(players_remaining_in_stage):
                round_actions = []
                for player in players_in_order:
                    desired_action = player.get_action(self.public_cards, len(players_remaining_in_stage) - 1, 100, self.poker_oracle)
                    players_remaining_in_stage, played_action = self.handle_desired_action(player, desired_action, players_remaining_in_stage, legal_num_raises)
                    round_actions.append(played_action)
            
            print("Players remaining in stage:", players_remaining_in_stage)
                    
            return players_remaining_in_stage

            
    def run_buy_in_round(self, players, legal_num_raises: int, small_blind_index: int, big_blind_index: int):
        players_remaining_in_round = players
        round_actions = []
        for i in range(len(players_remaining_in_round)):
            played_action = ""
            if i == small_blind_index:
                self.small_blind_player = players_remaining_in_round[i]
                if self.small_blind_player.num_chips < self.small_blind_chips:
                    players_remaining_in_round, played_action = self.handle_fold(players_remaining_in_round[i], players_remaining_in_round)
                self.pot += self.small_blind_player.bet(self.small_blind_chips)
                played_action = "small-blind"
            if i == big_blind_index:
                self.big_blind_player = players_remaining_in_round[i]
                if self.big_blind_player.num_chips < self.big_blind_chips:
                    players_remaining_in_round, played_action = self.handle_fold(players_remaining_in_round[i], players_remaining_in_round)
                self.pot += self.big_blind_player.bet(self.big_blind_chips)
                self.current_bet = self.big_blind_chips # NOTE: Current bet will never exceed big blind in first round a stage, since raise = big blind
                played_action = "call"
            else:
                desired_action = players_remaining_in_round[i].get_action(self.public_cards, len(players_remaining_in_round) - 1, 100, self.poker_oracle)
                players_remaining_in_round, played_action = self.handle_desired_action(players_remaining_in_round[i], desired_action, players_remaining_in_round, legal_num_raises)
            round_actions.append(played_action)
        # Small blind decides if interested in buy in
        small_blind_action = players_remaining_in_round[small_blind_index].get_action(self.public_cards, len(players_remaining_in_round) - 1, 100, self.poker_oracle)
        players_remaining_in_round, played_action = self.handle_desired_action(players_remaining_in_round[small_blind_index], small_blind_action, players_remaining_in_round, legal_num_raises)
        round_actions[small_blind_index] = played_action
        
        return players_remaining_in_round, round_actions
            
                
    def handle_desired_action(self, player, desired_action: str, players_remaining_in_round, legal_num_raises: int):
        played_action = desired_action
        if desired_action == "fold":
            players_remaining_in_round, played_action = self.handle_fold(player, players_remaining_in_round)
        if desired_action == "call":
            players_remaining_in_round, bet_amount, played_action = self.handle_call(player, players_remaining_in_round)
            self.pot += bet_amount
        if desired_action == "raise":                 
            players_remaining_in_round, bet_amount, played_action = self.handle_raise(player, players_remaining_in_round, legal_num_raises)
            self.pot += bet_amount
            self.current_bet = player.current_bet
        if desired_action == "all-in":
            players_remaining_in_round, bet_amount, played_action = self.handle_all_in(player, players_remaining_in_round)
            self.pot += bet_amount
        return players_remaining_in_round, played_action    
        
    def can_go_to_next_hand(self, players_remaining_in_stage) -> bool:
        return len(players_remaining_in_stage) == 1
    
    def can_go_to_next_stage(self, round_actions: list[str]) -> bool:
        action_counts = {"fold": 0, "call": 0, "raise": 0, "all-in": 0}
        if len(round_actions) == 0:
            return False
        for action in round_actions:
            action_counts[action] += 1
        if action_counts["raise"] > 0:
            return False
        if action_counts["all-in"] > 0: # TODO: CONSIDER REMOVING ALL-IN AS AN ACTION
            return False
        if action_counts["fold"] + action_counts["call"] == len(round_actions):
            return True
        return False # NOTE: Should not end up here! 
    
    def deal_public_cards(self, card_deck: CardDeck, stage: str) -> list[Card]:
        if stage == "pre-flop":
            return []
        if stage == "flop":
            return card_deck.deal(3)
        if stage == "turn":
            return card_deck.deal(1)
        if stage == "river":
            return card_deck.deal(1)
    
    def update_stage(self):
        # NOTE: Currently handles only one "round", not the beginning of a new round
        if self.current_stage == "pre-flop":
            self.current_stage = "flop"
        elif self.current_stage == "flop":
            self.current_stage = "turn"
        elif self.current_stage == "turn":
            self.current_stage = "river"
        elif self.current_stage == "river":
            self.current_stage = "river"

    def handle_fold(self, player, players_remaining_in_round):
        players_remaining_in_round.remove(player)
        return players_remaining_in_round, "fold"
    
    def handle_call(self, player, players_remaining_in_round):
        call_amount = self.current_bet - player.current_bet
        bet_amount = 0
        action = "call"
        if call_amount > player.num_chips:
            players_remaining_in_round, action = self.handle_fold(player, players_remaining_in_round)
        else:
            player.bet(call_amount)
            bet_amount = call_amount
        return players_remaining_in_round, bet_amount, action
    
    def handle_raise(self, player, players_remaining_in_round, num_remaining_raises: int):
        raise_amount = self.big_blind_chips
        bet_amount = 0
        action = "raise"
        if raise_amount > player.num_chips or num_remaining_raises == 0:
           players_remaining_in_round, bet_amount, action = self.handle_call(player, players_remaining_in_round)
        else:
            player.bet(raise_amount)
            bet_amount = raise_amount
        return players_remaining_in_round, bet_amount, action
    
    def handle_all_in(self, player, players_remaining_in_round):
        # NOTE: All may involve some techical details regarding the pot.
        # I will use a simple version for now. Removing all-in as an action is 
        # listed as a possible simplification. Might just end up doing that.
        bet_amount = player.bet(player.num_chips)
        return players_remaining_in_round, bet_amount, "all-in"
    
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
    

class PokerAgent:
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
        
    def bet(self, num_chips: int) -> int:
        self.current_bet = num_chips
        self.num_chips -= num_chips
        
        return self.current_bet
    
    def get_action(self, public_cards: list[Card], num_opponents: int, poker_oracle: PokerOracle) -> str:
        pass


class RolloutPokerAgent(PokerAgent):
    def __init__(self, type: str, initial_chips: int, name: str):
        super().__init__(type, initial_chips, name)
    
    # Implementing get action for a pure rollout based agent
    def get_action(self, public_cards: list[Card], num_opponents: int, rollout_count: int, poker_oracle: PokerOracle) -> str:
        # TODO: Should get probabilities from a pre-generated (and preferably saved) cheat sheet
        win_probability = poker_oracle.rollout_hole_pair_evaluator(self.hole_cards, public_cards, num_opponents, rollout_count)
        if win_probability >= 0.99:
            return "all-in"
        if win_probability >= 0.8:
            return "raise"
        if win_probability >= 0.2:
            return "call"
        else:
            return "fold" 
        
        
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
    
    def get_action(self, public_cards: list[Card], current_pot: int, table_bet) -> str:
        print(f"Your hole cards: {self.hole_cards}")
        print(f"Public cards: {public_cards}")
        print(f"Current pot: {current_pot}")
        print(f"Bet on table: {table_bet}")
        print(f"Your current bet: {self.current_bet}")
        print(f"Number of chips for call: {table_bet - self.current_bet if table_bet > self.current_bet else 0}")
        print(f"Your chips: {self.num_chips}")
        print("Choose action: fold, call, raise, all-in")
        action = input()
        return action
    
    
if __name__ == "__main__":
    game_manager = PokerGameManager()
    game_manager.add_poker_agent("rollout", 100, "Bob")
    game_manager.add_poker_agent("rollout", 100, "Alice")
    
    game_manager.run_one_game()
    
    