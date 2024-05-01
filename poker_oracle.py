from card_deck import Card, CardDeck
from itertools import combinations
import random
import numpy as np
import pandas as pd


class PokerOracle:
    
    def __init__(self, use_limited_deck=False):
        self.hand_rankings = {"royal_flush": 1,
                              "straight_flush": 2,
                              "four_of_a_kind": 3,
                              "full_house": 4,
                              "flush": 5,
                              "straight": 6,
                              "three_of_a_kind": 7,
                              "two_pair": 8,
                              "pair": 9,
                              "high_card": 10}
        
        self.use_limited_deck = use_limited_deck
        self.hole_pair_keys = None

# MARK: Hand classification
    
    # NOTE: Easiest to evaluate set of 5 cards.
    # Sets of 6 or 7 cards will be split into all possible sets 
    # of 5 cards. Each of these are evaluated and the best
    # classification is returned.
    def hand_classifier(self, card_set: list[Card]) -> tuple[str, int, list[Card]]: 
        num_cards = len(card_set)
        classification = ""
        ranking = 100 # Arbitrary initial value. Lower hand ranking is better
        if not num_cards == 5:
            subsets = self.get_all_five_card_subsets(card_set)
            best_subset = None
            for subset in subsets:
                subset_classification, subset_ranking, subset = self.hand_classifier(subset)
                if subset_ranking < ranking:
                    classification = subset_classification
                    ranking = subset_ranking
                    best_subset = subset
            return classification, ranking, best_subset
        else:
            if self.is_flush(card_set):
                if self.is_straight(card_set):
                    if self.get_highest_card(card_set).get_rank() == 14:
                        hand = "royal_flush"
                        return hand, self.hand_rankings[hand], card_set 
                    hand = "straight_flush"
                    return hand, self.hand_rankings[hand], card_set
                hand = "flush"
                return hand, self.hand_rankings[hand], card_set
            if self.is_straight(card_set):
                hand = "straight"
                return hand, self.hand_rankings[hand], card_set
            if self.is_four_of_a_kind(card_set):
                hand = "four_of_a_kind"
                return hand, self.hand_rankings[hand], card_set
            if self.is_full_house(card_set):
                hand = "full_house"
                return hand, self.hand_rankings[hand], card_set
            if self.is_three_of_a_kind(card_set):
                hand = "three_of_a_kind"
                return hand, self.hand_rankings[hand], card_set
            paired_ranks = self.get_paired_ranks(card_set)
            num_pairs = len(paired_ranks)
            if num_pairs == 2:
                hand = "two_pair"
                return hand, self.hand_rankings[hand], card_set
            if num_pairs == 1:
                hand = "pair"
                return hand, self.hand_rankings[hand], card_set
            # Hand is high card if not any of the above
            hand = "high_card"
            return hand, self.hand_rankings[hand], card_set
         
                 
    def get_all_five_card_subsets(self, card_set: list[Card]) -> tuple[list[Card]]: 
        # Returns all possible five card subsets of a given
        # 6 or 7 card set.
        return list(combinations(card_set, 5))
            
            
    def is_flush(self, card_set: list[Card]) -> bool:
        # Assumes 5 cards in card set
        suits = [card.get_suit() for card in card_set]
        num_different_suits = len(set(suits))
        return num_different_suits == 1
    
    # NOTE: Ace is only considered as 14, but should technically
    # also be considered a 1 when checking for straight!!!
    def is_straight(self, card_set: list[Card]) -> bool:
        rank_set = [card.get_rank() for card in card_set]
        rank_set.sort()
        lower_set = rank_set[:-1]
        upper_set = rank_set[1:]
        for lower, upper in zip(lower_set, upper_set):
            if not (upper == (lower + 1)):
                return False
        return True
        
        
    def get_highest_card(self, card_set: list[Card]) -> Card:
        sorted_card_set = sorted(card_set, key=lambda card: card.get_rank())
        highest_card = sorted_card_set[-1]
        return highest_card
    
    
    def count_ranks(self, card_set: list[Card]) -> list[int]:
        # Possible card rank ranges from 2 - 14.
        # Count number of ocurrences of each rank.
        rank_count = [0] * 14
        for card in card_set:
            card_rank = card.get_rank()
            rank_index = card_rank - 1
            rank_count[rank_index] += 1
        return rank_count
    
    
    def get_paired_ranks(self, card_set: list[Card]) -> int:
            num_each_rank = self.count_ranks(card_set)
            paired_ranks = []
            for i in range(len(num_each_rank)):
                if num_each_rank[i] == 2:
                    paired_rank = i+1
                    paired_ranks.append(paired_rank)
            return paired_ranks
        
        
    def is_full_house(self, card_set: list[Card]) -> bool:
        num_each_rank = self.count_ranks(card_set)
        return 2 in num_each_rank and 3 in num_each_rank
    
    
    def is_four_of_a_kind(self, card_set: list[Card]) -> bool:
        num_each_rank = self.count_ranks(card_set)
        return 4 in num_each_rank
            
            
    def is_three_of_a_kind(self, card_set: list[Card]) -> bool:
        # NOTE: Assumes full house is checked before this
        num_each_rank = self.count_ranks(card_set)
        return 3 in num_each_rank
    
    
 # MARK: Hole pair evaluation  
    def evaluate_showdown(self, public_cards: list[Card], p1_hole_cards: list[Card], p2_hole_cards: list[Card]) -> int:
        # NOTE: For hand rankings, lower rank is better
        p1_win = 1
        p2_win = -1
        tie = 0
        p1_card_set = [*public_cards, *p1_hole_cards]
        p2_card_set = [*public_cards, *p2_hole_cards]
        p1_classification, p1_hand_ranking, p1_best_set = self.hand_classifier(p1_card_set)
        p2_classification, p2_hand_ranking, p2_best_set = self.hand_classifier(p2_card_set)
        if not (p1_classification == p2_classification):
            if p1_hand_ranking < p2_hand_ranking:
                return p1_win
            return p2_win
        # NOTE: Assuming high card break ties for same classifications
        p1_highest_card = self.get_highest_card(p1_best_set)
        p2_highest_card = self.get_highest_card(p2_best_set)
        if p1_highest_card.get_rank() > p2_highest_card.get_rank():
            return p1_win
        elif p1_highest_card.get_rank() == p2_highest_card.get_rank():
            # NOTE: In case ranks of highest cards are equal
            # Need to also check each players hole card which is not included in the "best set" 
            p1_hole_card_not_in_best_set = [hole_card for hole_card in p1_hole_cards if hole_card not in p1_best_set]
            p2_hole_card_not_in_best_set = [hole_card for hole_card in p2_hole_cards if hole_card not in p2_best_set]
            p1_hole_card_not_in_best_set = p1_hole_card_not_in_best_set if len(p1_hole_card_not_in_best_set) > 0 else p1_hole_cards
            p2_hole_card_not_in_best_set = p2_hole_card_not_in_best_set if len(p2_hole_card_not_in_best_set) > 0 else p2_hole_cards
            p1_highest_hole_card = self.get_highest_card(p1_hole_card_not_in_best_set) 
            p2_highest_hole_card = self.get_highest_card(p2_hole_card_not_in_best_set) 
            if p1_highest_hole_card.get_rank() == p2_highest_hole_card.get_rank():
                return tie
            if p1_highest_hole_card.get_rank() > p2_highest_hole_card.get_rank():
                return p1_win
        return p2_win
    
    # TODO: Sometimes returns a 0 probability for win. Is this realistic?
    def rollout_hole_pair_evaluator(self, hole_pair: list[Card], public_cards: list[Card] | None, num_opponents: int, rollout_count: int) -> float:
        exclude_from_deck = [*hole_pair]
        num_public_cards_to_deal = 5
        dealt_public_cards = []
        num_rollout_wins = 0
        if public_cards is not None:
            dealt_public_cards = [*public_cards]
            num_public_cards_to_deal -= len(public_cards)
            [exclude_from_deck.append(card) for card in public_cards]
        for i in range(rollout_count):
            # Generate card deck with known private and public card excluded
            card_deck = CardDeck(limited=self.use_limited_deck)
            card_deck.exclude(exclude_from_deck)
            card_deck.shuffle()
            
            # Reset opponents hole cards and deal random cards to each opponent
            all_opponents_hole_cards = []
            for _ in range(num_opponents):
                opponent_hole_cards = card_deck.deal(2)
                all_opponents_hole_cards.append(opponent_hole_cards)
                
            # Reset public cards and deal out remaining public cards
            dealt_public_cards = []
            if public_cards is not None:
                dealt_public_cards = [*public_cards]   
            if not num_public_cards_to_deal == 0:
                new_public_cards = card_deck.deal(num_public_cards_to_deal)
                dealt_public_cards = [*dealt_public_cards, *new_public_cards]
                
            win_rollout = True
            # Assumes win when hole_pair beats all opponents
            for opponent_hole_cards in all_opponents_hole_cards:
                winner = self.evaluate_showdown(dealt_public_cards, hole_pair, opponent_hole_cards)
                if not winner == 1:
                    win_rollout = False
                    break
            if win_rollout:
                num_rollout_wins += 1
                            
        hole_pair_win_probability = num_rollout_wins / rollout_count
        return hole_pair_win_probability
    

# MARK: Cheat sheet
    def poker_cheat_sheet_generator(self, max_num_opponents: int, num_rollouts: int) -> np.ndarray:
        hole_pair_types = self.get_all_hole_pairs_by_type()     
        cheat_sheet: list[list[float]] = []
        pair_types = list(hole_pair_types.keys())
        for i in range(len(hole_pair_types)):
            cheat_sheet.append([])
            random_hole_pair = random.choice(hole_pair_types[pair_types[i]])
            for j in range(max_num_opponents):
                num_opponents = j + 1
                winning_probability = self.rollout_hole_pair_evaluator(random_hole_pair, None, num_opponents, num_rollouts)
                cheat_sheet[i].append(winning_probability)
        
        return np.asarray(cheat_sheet)
    
    
    def generate_and_save_cheat_sheet(self, max_num_opponents: int, num_rollouts: int) -> np.ndarray:
        cheat_sheet = self.poker_cheat_sheet_generator(max_num_opponents, num_rollouts)
        file_name = ""
        if self.use_limited_deck:
            file_name += "limited_"
        file_name += f"{max_num_opponents}opponents_{num_rollouts}rollouts.csv"
        df_cheat_sheet = pd.DataFrame(np.asarray(cheat_sheet))
        df_cheat_sheet.to_csv(f"cheat_sheets/{file_name}", index=False)
        return np.asarray(cheat_sheet)
        
        
    def load_cheat_sheet(self, max_num_opponents: int, num_rollouts: int) -> np.ndarray:
        file_name = ""
        if self.use_limited_deck:
            file_name += "limited_"
        file_name += f"{max_num_opponents}opponents_{num_rollouts}rollouts.csv"
        try:
            cheat_sheet = pd.read_csv(f"cheat_sheets/{file_name}")
            cheat_sheet = cheat_sheet.to_numpy()
        except:
            cheat_sheet = None
        return cheat_sheet      
        
    
    def get_cheat_sheet_hole_pair_probabilitiy(self, hole_pair: list[Card], num_opponents: int, 
                                               cheat_sheet: np.ndarray) -> float:
        all_hole_pair_types = list(self.get_all_hole_pairs_by_type().keys())
        hole_pair_type = self.get_hole_pair_type(hole_pair)
        hole_pair_type_index = all_hole_pair_types.index(hole_pair_type)
        num_opponents_index = num_opponents - 1
        win_probability = cheat_sheet[hole_pair_type_index][num_opponents_index]
        return win_probability
        

# MARK: Utility matrix

    def utility_matrix_generator(self, public_cards: list[Card]) -> tuple[np.ndarray, list[int]]:
            utility_matrix: list[list[int]] = []
            all_hole_pairs_by_type: dict[list[Card]] = self.get_all_hole_pairs_by_type()
            hole_pair_types = list(all_hole_pairs_by_type.keys()) 
            all_hole_pairs = []
            hole_pair_keys = []
            for key in hole_pair_types:
                hole_pairs_one_type = all_hole_pairs_by_type[key]
                for i in range(len(hole_pairs_one_type)):
                    hole_pair = hole_pairs_one_type[i]
                    # NOTE: Want to avoid having duplicate entries because of the order of the cards in the hole card list.
                    hole_pair_key = self.get_hole_pair_key(hole_pair)
                    if not hole_pair_key in hole_pair_keys:
                        all_hole_pairs.append(hole_pair)
                        hole_pair_keys.append(hole_pair_key)
            for index_1, hole_pair_1 in enumerate(all_hole_pairs):
                utility_matrix.append([])
                for _, hole_pair_2 in enumerate(all_hole_pairs):
                    if hole_pair_1 == hole_pair_2:
                        utility_matrix[index_1].append(0)
                    elif self.is_card_overlap(hole_pair_1, hole_pair_2, public_cards):
                        utility_matrix[index_1].append(0)
                    else:
                        # NOTE: P1 perspective. 1 if P1 wins, -1 if P2 wins, 0 if tie
                        winner = self.evaluate_showdown(public_cards, hole_pair_1, hole_pair_2)
                        utility_matrix[index_1].append(winner)
                        
            self.hole_pair_keys = hole_pair_keys
            
            return np.asarray(utility_matrix), hole_pair_keys
        
        
    def get_utility_matrix_indices_by_hole_cards(self, hole_pair_1: list[Card], hole_pair_2: list[Card]) -> tuple[int, int]:
            # NOTE: Allows for getting the entry in the utility matrix directly from the hole cards
            key_hole_pair_1 = self.get_hole_pair_key(hole_pair_1)
            key_hole_pair_2 = self.get_hole_pair_key(hole_pair_2)
            index_hole_pair_1 = self.hole_pair_keys.index(key_hole_pair_1)
            index_hole_pair_2 = self.hole_pair_keys.index(key_hole_pair_2)
            return index_hole_pair_1, index_hole_pair_2

        
# MARK: Helper methods   

    def get_hole_pair_type(self, hole_pair: list[Card]) -> str:
        card1 = hole_pair[0]
        card2 = hole_pair[1]
        pair_type = ""
        if card1.get_rank() == card2.get_rank():
            pair_type = str(card1.get_rank()) + "_pair"
        else:
            # NOTE: Sort the ranks to make sure that e.g. both rank pairs (10,9) and (9,10)
            # results in key 10_9_suited
            sorted_ranks = sorted([card1.get_rank(), card2.get_rank()])
            if card1.get_suit() == card2.get_suit():
                pair_type = str(sorted_ranks[1]) + "_" + str(sorted_ranks[0]) + "_suited"
            else: 
                pair_type = str(sorted_ranks[1]) + "_" + str(sorted_ranks[0]) + "_unsuited"
        return pair_type
        
        
    def get_hole_pair_key(self, hole_pair: list[Card]) -> str:
        # NOTE: This differs from get_hole_pair_type by specifying
        # the suits of the cards in the hole pair. Not just classify as "suited" or "unsuited".
        card1 = hole_pair[0]
        card2 = hole_pair[1]
        pair_key = ""
        if card1.get_rank() == card2.get_rank():
            # NOTE: Sort suits alphabetically to avoid duplicates like (3H_3S) and (3S_3H)
            sorted_pair = sorted(hole_pair, key=lambda card: card.get_suit())
            alpha_last_card = sorted_pair[1]
            alpha_first_card = sorted_pair[0]
            pair_key = f"{str(card1.get_rank())}{alpha_first_card.get_suit()}_{str(card2.get_rank())}{alpha_last_card.get_suit()}"
        else:
            # NOTE: Sort the ranks to make sure that e.g. both rank pairs (10H,9C) and (9C,10H)
            # results in key 10H_9C
            sorted_pair = sorted(hole_pair, key=lambda card: card.get_rank())
            highest_card = sorted_pair[1]
            lowest_card = sorted_pair[0]
            pair_key = f"{str(highest_card.get_rank())}{highest_card.get_suit()}_{str(lowest_card.get_rank())}{lowest_card.get_suit()}"
        return pair_key
        
        
    def get_all_hole_pair_keys(self) -> list[str]:       
        card_deck = CardDeck(self.use_limited_deck)
        
        hole_pair_keys = []
        for card1 in card_deck.cards:
            for card2 in card_deck.cards:
                if card1 == card2:
                    continue
                hole_pair = [card1, card2]
                hole_pair_key = self.get_hole_pair_key(hole_pair)
                if hole_pair_key not in hole_pair_keys:
                    hole_pair_keys.append(hole_pair_key)
        
        self.hole_pair_keys = hole_pair_keys
        return self.hole_pair_keys


    def is_card_overlap(self, hole_pair_1: list[Card], hole_pair_2: list[Card], public_cards: list[Card]) -> bool:
        for card1 in hole_pair_1:
            for card2 in hole_pair_2:
                if card1.get_rank() == card2.get_rank() and card1.get_suit() == card2.get_suit():
                    return True
        for card1 in hole_pair_1:
            for card2 in public_cards:
                if card1.get_rank() == card2.get_rank() and card1.get_suit() == card2.get_suit():
                    return True
        for card1 in hole_pair_2:
            for card2 in public_cards:
                if card1.get_rank() == card2.get_rank() and card1.get_suit() == card2.get_suit():
                    return True
        return False         
    
    
    def get_all_hole_pairs_by_type(self) -> dict[list[Card]]:
        card_deck = CardDeck(limited=self.use_limited_deck)
        hole_pairs_by_type: dict[list[Card]] = {}
        deck: list[Card] = card_deck.cards
        for card1 in deck:
            for card2 in deck:
                if card1 == card2:
                    continue
                hole_pair = [card1, card2]
                pair_type_key = self.get_hole_pair_type(hole_pair)
                if pair_type_key in list(hole_pairs_by_type.keys()):
                    hole_pairs_by_type[pair_type_key].append(hole_pair)
                else:
                    hole_pairs_by_type[pair_type_key] = [hole_pair]
        return hole_pairs_by_type
    
    
    def get_deck_of_cards(self) -> CardDeck:
        return CardDeck(limited=self.use_limited_deck)
    

# MARK: Main
if __name__ == "__main__":

    use_limited_deck = True

    poker_oracle = PokerOracle(use_limited_deck)
    card_deck = CardDeck(use_limited_deck)
    card_deck.shuffle()
    # card_set = card_deck.deal(7)
    # subsets = poker_oracle.get_all_five_card_subsets(card_set)
    # for subset in subsets:
    #     print(type(subset))
    #     for card in subset:
    #         print(card)
    
    # pc = card_deck.deal(5)
    # h1 = card_deck.deal(2)
    # h2 = card_deck.deal(2)
    
    # print(len(poker_oracle.get_all_hole_pair_keys()))
    
    # ============== UTILITY MATRIX ===============
    
    # utility_matrix, hole_pair_keys = poker_oracle.utility_matrix_generator(card_deck.deal(3))
    
    # NOTE: Utiliti matrix generator does a lot of showdown evaluations.
    # When there are more than 3 public cards, the evaluation needs to check all 5 card combinations
    # to find the best one.
    # Even though the utility matrix has fewer entries in the 5 public card version,
    # the run time of each evaluation increases.
    # For 3 public cards the time to 100 000 evaluations was about 14 seconds
    # For 5 public cards the time to 100 000 evaluations was about 48 seconds, about 3.5 times slower
    # Thus, generating the matrix for 5 public cards is a deal slower than for 3 public cards.
    # Using the functools.cache decorator did not provide any significant improvement.
    
    # hole_pair_1 = card_deck.deal(2)
    # hole_pair_2 = card_deck.deal(2)
    
    # index_hole_pair_1, index_hole_pair_2 = poker_oracle.get_utility_matrix_indices_by_hole_cards(hole_pair_1, hole_pair_2)
    # hole_pair_key_1 = poker_oracle.get_hole_pair_key(hole_pair_1)
    # hole_pair_key_2 = poker_oracle.get_hole_pair_key(hole_pair_2)
    
    # print(utility_matrix.shape)
    # print(utility_matrix[index_hole_pair_1][index_hole_pair_2])
    
    
    # ============ CHEAT SHEET ==============
    
    # cheat_sheet_gen = poker_oracle.generate_and_save_cheat_sheet(6, 100)
    # cheat_sheet_load = poker_oracle.load_cheat_sheet(6, 100)
    
    # print(cheat_sheet_gen)
    # print(cheat_sheet_load)
    # print(cheat_sheet_gen == cheat_sheet_load)
    
    print()
    poker_oracle.generate_and_save_cheat_sheet(6, 1000)
    

    
    