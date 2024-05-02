from poker_oracle import PokerOracle
from card_deck import Card

import time

poker_oracle = PokerOracle()
poker_oracle_limited = PokerOracle(True)

public_cards = [
    Card('D', 11),
    Card('S', 12),
    Card('C', 13),
    Card('C', 2),
    Card('H', 4)
]

#MARK: Limited deck
start_time = time.time()
utility_matrix_limited, hole_pair_keys_limited = poker_oracle_limited.utility_matrix_generator(public_cards[:-2])
print(utility_matrix_limited) 
# NOTE: Around 0.5 - 1 second
print(f"Generated utility matrix using 3 public cards and limited deck in {time.time() - start_time:.3f} seconds.")
print()

start_time = time.time()
utility_matrix_limited, hole_pair_keys_limited = poker_oracle_limited.utility_matrix_generator(public_cards[:-1])
print(utility_matrix_limited) 
# NOTE: Around 2 - 3 seconds
print(f"Generated utility matrix using 4 public cards and limited deck in {time.time() - start_time:.3f} seconds.")
print()

start_time = time.time()
utility_matrix_limited, hole_pair_keys_limited = poker_oracle_limited.utility_matrix_generator(public_cards)
print(utility_matrix_limited) 
# NOTE: Around 9 - 10 seconds
print(f"Generated utility matrix using 5 public cards and limited deck in {time.time() - start_time:.3f} seconds.")
print()
print("Number of hole pairs:", len(hole_pair_keys_limited))
print()

# MARK: Regular deck
start_time = time.time()
utility_matrix, hole_pair_keys = poker_oracle.utility_matrix_generator(public_cards[:-2])
print(utility_matrix) 
# NOTE: Around 21 seconds
print(f"Generated utility matrix using 3 public cards and limited deck in {time.time() - start_time:.3f} seconds.")
print()

start_time = time.time()
utility_matrix, hole_pair_keys = poker_oracle.utility_matrix_generator(public_cards[:-1])
print(utility_matrix) 
# NOTE: Around 93 seconds
print(f"Generated utility matrix using 4 public cards and limited deck in {time.time() - start_time:.3f} seconds.")
print()

start_time = time.time()
utility_matrix, hole_pair_keys = poker_oracle.utility_matrix_generator(public_cards)
print(utility_matrix) 
# NOTE: Around 283 seconds
print(f"Generated utility matrix using 5 public cards and limited deck in {time.time() - start_time:.3f} seconds.")
print()
print("Number of hole pairs:", len(hole_pair_keys_limited))
print()

