from card_deck import Card, CardDeck
from itertools import combinations
import random


class PokerOracle:
    
    def __init__(self):
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
    
    # NOTE: Easiest to evaluate set of 5 cards.
    # Sets of 6 or 7 cards will be split into all possible sets 
    # of 5 cards. Each of these are evaluated and the best
    # classification is returned.
    def hand_classifier(self, card_set: list[Card]) -> tuple[str, int]: 
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
                    if self.get_highest_card(card_set).get_rank() == 14: # TODO: Make this a constant? Or use something from the card_deck class?
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
    
    # TODO: Ace is only considered as 14, but should technically
    # also be considered a 1 when checking for straight!!!
    def is_straight(self, card_set: list[Card]) -> bool:
        rank_set = [card.get_rank() for card in card_set]
        rank_set.sort()
        lower_set = rank_set[:-1]
        upper_set = rank_set[1:]
        for lower, upper in zip(lower_set, upper_set):
            if not upper == lower + 1:
                return False
        return True
        
    def get_highest_card(self, card_set: list[Card]) -> Card:
        sorted_card_set = sorted(card_set, key=lambda card: card.get_rank())
        highest_card = sorted_card_set[-1]
        return highest_card
    
    def count_ranks(self, card_set: list[Card]) -> list[int]:
        # Possible card rank ranges from 2 - 14.
        # Count number of ocurrences of each rank.
        # Similar to procedure in Counting Sort
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
    
    def evaluate_showdown(self, public_cards: list[Card], p1_hole_cards: list[Card], p2_hole_cards: list[Card]) -> int:
        # NOTE: For hand rankings, lower rank is better
        p1_win = 1
        p2_win = -1
        tie = 0
        num_public_cards = len(public_cards)
        # NOTE: Draw remaining public cards and evaluate
        if not num_public_cards == 5:
            deck = CardDeck()
            deck.shuffle()
            cards_to_exclude = [*public_cards, *p1_hole_cards, *p2_hole_cards]
            deck.exclude(cards_to_exclude)
            num_cards_to_deal = 5 - num_public_cards
            new_public_cards = deck.deal(num_cards_to_deal)
            public_cards = [*public_cards, *new_public_cards]
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
            return tie
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
        for _ in range(rollout_count):
            # Generate card deck with known private and public card excluded
            card_deck = CardDeck()
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
    
    def poker_cheat_sheet_generator(self, max_num_opponents: int, num_rollouts: int) -> list[list[float]]:
        hole_pair_types = self.get_all_hole_pairs_by_type()
        cheat_sheet: dict[list[float]] = {}
        pair_types = list(hole_pair_types.keys())
        print("Number of pair types:", len(pair_types))
        for pair_type in pair_types:
            cheat_sheet[pair_type] = []
            random_hole_pair = random.choice(hole_pair_types[pair_type])
            for i in range(max_num_opponents):
                num_opponents = i + 1
                winning_probability = self.rollout_hole_pair_evaluator(random_hole_pair, None, num_opponents, num_rollouts)
                cheat_sheet[pair_type].append(winning_probability)       
        return cheat_sheet
    
    
    # TODO: Create method for saving cheat sheet to file
    def get_cheat_sheet_hole_pair_probabilitiy(self, hole_pair: list[Card], num_opponents: int, 
                                               cheat_sheet: dict[list[float]]) -> float:
        hole_pair_type = self.get_hole_pair_type(hole_pair)
        num_opponents_index = num_opponents - 1
        win_probability = cheat_sheet[hole_pair_type][num_opponents_index]
        return win_probability
        
        
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
        pair_type = ""
        card1_suit = card1.get_suit()
        card2_suit = card2.get_suit()
        if card1.get_rank() == card2.get_rank():
            pair_type = f"{str(card1.get_rank())}{card1_suit}_{str(card2.get_rank())}{card2_suit}"
        else:
            # NOTE: Sort the ranks to make sure that e.g. both rank pairs (10H,9C) and (9C,10H)
            # results in key 10H_9C
            sorted_ranks = sorted([card1.get_rank(), card2.get_rank()])
            pair_type = f"{sorted_ranks[1]}{card1_suit}_{sorted_ranks[0]}{card2_suit}"
        return pair_type
        
    # TODO: Maybe change to pandas dataframe?
    def utility_matrix_generator(self, public_cards: list[Card]) -> dict[dict[int]]:
        utility_matrix: dict[dict[int]] = {}
        all_hole_pairs_by_type: dict[list[Card]] = self.get_all_hole_pairs_by_type()
        hole_pair_types = list(all_hole_pairs_by_type.keys()) 
        all_hole_pairs = []
        hole_pair_keys = []
        for key in hole_pair_types:
            hole_pairs_one_type = all_hole_pairs_by_type[key]
            for i in range(len(hole_pairs_one_type)):
                hole_pair = hole_pairs_one_type[i]
                hole_pair_key = self.get_hole_pair_key(hole_pair)
                # NOTE: Want to avoid having duplicate entries because of the order of the cards in the hole card list.
                # TODO: I think this is necessary but i may be wrong. Should probably ask about it.
                if not hole_pair_key in hole_pair_keys:
                    all_hole_pairs.append(hole_pair)
                    hole_pair_keys.append(hole_pair_key)
        for hole_pair_1 in all_hole_pairs:
            key_hole_pair_1 = self.get_hole_pair_key(hole_pair_1)
            utility_matrix[key_hole_pair_1] = []
            for hole_pair_2 in all_hole_pairs:
                key_hole_pair_2 = self.get_hole_pair_key(hole_pair_2)
                if hole_pair_1 == hole_pair_2:
                    utility_matrix[key_hole_pair_1].append({key_hole_pair_2: 0})
                elif self.is_card_overlap(hole_pair_1, hole_pair_2, public_cards):
                    utility_matrix[key_hole_pair_1].append({key_hole_pair_2: 0})
                else:
                    # NOTE: P1 perspective. 1 if P1 wins, -1 if P2 wins, 0 if tie
                    winner = self.evaluate_showdown(public_cards, hole_pair_1, hole_pair_2)
                    utility_matrix[key_hole_pair_1].append({key_hole_pair_2: winner})
        return utility_matrix, hole_pair_keys

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
        card_deck = CardDeck()
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
        return CardDeck()
    

if __name__ == "__main__":

    poker_oracle = PokerOracle()
    card_deck = CardDeck()
    card_deck.shuffle()
    card_set = card_deck.deal(7)
    subsets = poker_oracle.get_all_five_card_subsets(card_set)
    for subset in subsets:
        print(type(subset))
        for card in subset:
            print(card)