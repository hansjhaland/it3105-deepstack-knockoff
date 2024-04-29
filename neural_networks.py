from card_deck import CardDeck, Card
from poker_oracle import PokerOracle
import numpy as np

# MARK: MODEL

# MARK: TRAINING

# MARK: DATA SET GENERATION

def generate_random_ranges(public_cards: list[Card], poker_oracle: PokerOracle):
    exclude_cards: list[str] = []
    for card in public_cards:
        card_key = str(card.get_rank()) + card.get_suit()
        exclude_cards.append(card_key)
        
    hole_pair_keys: list[str] = poker_oracle.get_all_hole_pair_keys()
    num_hole_pairs = len(hole_pair_keys)
    player1_range = np.zeros(num_hole_pairs)
    player2_range = np.zeros(num_hole_pairs)
    
    num_non_zero_probabilities = num_hole_pairs - len(public_cards)
    player1_random_probabilities = np.random.rand(num_non_zero_probabilities)
    player1_random_probabilities = player1_random_probabilities / np.sum(player1_random_probabilities)
    player2_random_probabilities = np.random.rand(num_non_zero_probabilities)
    player2_random_probabilities = player2_random_probabilities / np.sum(player2_random_probabilities)
    
    prob_index_1, prob_index_2 = 0, 0
    for i in range(num_hole_pairs):
        hole_pair_is_possible = True
        for card in exclude_cards:
            if card in hole_pair_keys[i]:
                hole_pair_is_possible = False
                break
        if hole_pair_is_possible:
            player1_range[i] = player1_random_probabilities[prob_index_1]
            player2_range[i] = player2_random_probabilities[prob_index_2]
            prob_index_1 += 1
            prob_index_2 += 1
            
    return player1_range, player2_range
    

def encode_public_cards(public_cards, use_limited_deck):       
    public_cards_strings: list[str] = [str(card) for card in public_cards]
    
    card_deck = CardDeck(use_limited_deck)
    num_cards = len(card_deck.cards)
    
    encoding = np.zeros(num_cards)
    for i, card in enumerate(card_deck.cards):
        if str(card) in public_cards_strings:
            encoding[i] = 1
            
    return encoding
    
    
# NOTE: Based on "Cheap method" from slides
def generate_training_data_for_stage(stage, num_cases, use_limited_deck, save_to_file):
    stage_to_num_public_cards = {
        "flop": 3,
        "turn": 4,
        "river": 5
    }

    # NOTE: Just picked some values that seems reasonable:
    stage_max_pot = {
        "flop": 40,
        "turn": 60,
        "river": 80
    }
    
    num_public_cards = stage_to_num_public_cards[stage]
    
    poker_oracle = PokerOracle(use_limited_deck)
    
    training_data = []
    for _ in range(num_cases):
        card_deck = CardDeck(use_limited_deck)
        card_deck.shuffle()
        public_cards = card_deck.deal(num_public_cards)
        
        encoded_public_cards = encode_public_cards(public_cards, use_limited_deck)
        # print("Public cards", len(encoded_public_cards))
        
        p1_range, p2_range = generate_random_ranges(public_cards, poker_oracle)
        # print("Ranges",len(p1_range))
        
        utility_matrix, _ = poker_oracle.utility_matrix_generator(public_cards)
        
        p1_evaluation = np.squeeze(np.matmul(utility_matrix, np.atleast_2d(p2_range).T))
        p2_evaluation = -1 * np.matmul(p1_range, utility_matrix)
        
        # print("Evaluations",len(p1_evaluation))
        
        max_pot = stage_max_pot[stage]
        min_pot = max_pot // 4 # NOTE: Arbitrary scaling of max pot to reflect the fact that the minimum pot is different for each stage
        pot = np.random.randint(min_pot, max_pot, size=1)[0]
        relative_pot = [pot/max_pot]
        
        #NOTE: Length of ranges, evaluations, and public card encodings vary with the deck size
        # Deck size:            52   or 24
        # Encoded public cards: 52   or 24
        # Ranges:               1326 or 276
        # Evaluations:          1326 or 276
        # Total case length:    5357 or 1129
        training_case = [*p1_range, *encoded_public_cards, *relative_pot, *p2_range, *p1_evaluation, *p2_evaluation]
        training_data.append(training_case)
        # print(len(training_case))
    
    training_data = np.asarray(training_data)
    
    if save_to_file:
        if use_limited_deck:
            save_path = f"./training_data/limited_{stage}_{num_cases}"
        else:    
            save_path = f"./training_data/{stage}_{num_cases}"    
        np.save(save_path, training_data) 
        
    return training_data


def load_data_set_from_file(file_name: str):
    training_data = np.load(f"./training_data/{file_name}.npy")
    
    is_limited = False
    if file_name.split("_")[0] == "limited":
        is_limited = True
    
    if not is_limited:
        # NOTE: Index ranges in each data case for REGULAR deck
        # p1_range:             0    - 1325
        # encoded_public_cards: 1326 - 1377
        # relative_pot:         1378 - 1379
        # p2_range:             1380 - 2705
        # p1_evaluation:        2706 - 4031
        # p2_evaluation:        4032 - 5356
        
        # Input indices:        0    - 2705
        # P1 target:            2706 - 4031
        # P2 target:            4032 - 5356
        input_indices = {
            "input": (0, 2705),
            "p1_target": (2706, 4031),
            "input": (4032, 5356)
        }
    else:
        # NOTE: Index ranges in each data case for LIMITED deck
        # p1_range:             0   - 275
        # encoded_public_cards: 276 - 299
        # relative_pot:         300 - 301
        # p2_range:             302 - 577
        # p1_evaluation:        578 - 853
        # p2_evaluation:        854 - 1129
        
        # Input indices:        0   - 577
        # P1 target:            578 - 853
        # P2 target:            854 - 1129
        input_indices = {
            "input": (0, 577),
            "p1_target": (578, 853),
            "p2_target": (854, 1129)
        }       
    
    inputs = training_data[:, input_indices["input"][0]:input_indices["input"][1]]
    p1_targets = training_data[:, input_indices["p1_target"][0]:input_indices["p1_target"][1]]
    p2_targets = training_data[:, input_indices["p2_target"][0]:input_indices["p2_target"][1]]
    
    # print(inputs.shape, p1_targets.shape, p2_targets.shape)
    
    return inputs, p1_targets, p2_targets
    
is_limited_list = [True, False]
stage_list = ["flop", "turn", "river"]
num_cases = 50000
save_to_file = True

for is_limited in is_limited_list:
    for stage in stage_list:
        if is_limited:
            print(f"Generating {num_cases} for {stage} stae with limited deck")
        else:
            print(f"Generating {num_cases} for {stage} stae with regular deck")
        generate_training_data_for_stage(stage, num_cases, is_limited, save_to_file)

