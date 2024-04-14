import random

class Card:
    
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        
    def __str__(self):
        rank_symbols = {"10":"T", "11":"J", "12":"Q", "13":"K", "14":"A"}
        rank = str(self.rank)
        if rank in rank_symbols:
            rank = rank_symbols[rank]
        return rank + self.suit
    
    def get_suit(self):
        return self.suit
    
    def get_rank(self):
        return self.rank
    
    
class CardDeck:
    
        def __init__(self, limited = False):
            self.suits = ['S', 'H', 'D', 'C']
            self.ranks = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14] if not limited else [9, 10, 11, 12, 13, 14]
            self.cards: list[Card] = []
            for suit in self.suits:
                for rank in self.ranks:
                    self.cards.append(Card(suit, rank))
                    
        def __str__(self):
            return ' '.join(str(card) for card in self.cards)
        
        def shuffle(self):
            random.shuffle(self.cards)
            
        def deal(self, n):
            return [self.cards.pop() for _ in range(n)]
        
        def exclude(self, cards: list[Card]):
            for exclude_card in cards:
                self.cards = [deck_card for deck_card in self.cards 
                              if not (deck_card.get_rank() == exclude_card.get_rank()
                                      and deck_card.get_suit() == exclude_card.get_suit())]
                
        def get_suits(self):
            return self.suits
        
        def get_ranks(self):
            return self.ranks
        
        
        
        
if __name__ == "__main__":
    card_deck = CardDeck()
    print(card_deck)
    print(len(card_deck.cards))
    card_deck.shuffle()
    [print(card) for card in card_deck.deal(4)]
    print(len(card_deck.cards))
    print(card_deck)