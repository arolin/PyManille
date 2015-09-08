################################################################################
#Implements a simple text based version of the card game Manie
#
#This is a 4 person trick based card game 
import operator
import random
import pdb 

    
#Some Constants
kNumPlayers = 4
kSuites = ["H","S","C","D"]

#In Manille the card order is not traditional, this dictionary maps the
#rank of a card vs it's display type
ranks = {0:'    8 ',
         1:'    7 ',
         2:'    9 ',
         3:' Jack ',
         4:'Queen ',
         5:' King ',
         6:'  Ace ',
         7:'   10 '}
#similar mapping but using the image name indexes for the GUI
rankIcon ={0:'08',
           1:'07',
           2:'09',
           3:'11',
           4:'12',
           5:'13',
           6:'01',
           7:'10'}

suites = {'H':'Hearts',
          'S':'Spades',
          'C':'Clubs',
          'D':'Diamonds'}

#Define an object to hold:
#  rank
#  suite
#  score value
# of each card
#
#Define:
# comparison
# string display
class Card:
    trump_suite =''
    suite_led   =''

    def __init__ (self, suite, rank):
        self.suite=suite
        self.rank=rank
        self.score=0
        if (self.rank>2):
            self.score = self.rank - 2
            
    def __str__ (self):
        #use the dictonaries to create a display string for printing
        return ranks[self.rank] + 'of ' + suites[self.suite]

    def __lt__ (self, other):
        # Should return a negative integer if self < other,
        # zero if self == other, a positive integer if self > other.
        #
        # Comparison accoring to the rules fo Manille:
        #  Trump suite is higher than any card in any other suite,
        #  rank within the trump suite determines which is greater
        #
        #  Any card that is not in the suite which was lead can not win
        #
        #  If there is no trump, rank within the suite which was lead
        #  determines which is greater
        if self.suite == Card.suite_led:
            if other.suite == Card.suite_led:
                return self.rank < other.rank
            elif other.suite == Card.trump_suite:
                return True
            else:
                return False
        elif self.suite == Card.trump_suite:
            if other.suite == Card.trump_suite:
                return self.rank < other.rank
            else:
                return False
        else:
            return True
    
#define a colleciton of cards
class Deck:
    def __init__ (self):
        #one card for each rank in each suite
        self.cards = [Card (rank=r,suite=s) for s in kSuites
                      for r in range(len(ranks))]

    def shuffle(self):
        random.shuffle(self.cards)
        
#define a player class with a basic AI        
class Player:
    def __init__(self):
        #keep track of current hand
        self.cards = []
        #keep trak of tricks won
        self.tricks = []
        #keep track of score across hands
        self.score = 0

    #build the current had during the deal
    def add_card(self, card):
        self.cards.append(card);
        
    #clear all the tricks collected for scoring at the end of hand
    def new_hand(self):
        self.tricks = []
    
    #sort the hand by suite and rank for ease of human player
    def sort_hand(self):
        self.cards = sorted(self.cards,key=lambda x: (x.suite, -x.rank))

    #provide a simple AI function which choses the trup suite if the
    #players is the dealer for the hand - uses the trivial heuristic of
    #which suite is the longest
    def chose_trump(self):
        nMax=0
        max_suite=''
        for s in kSuites:
            n=0
            for c in self.cards:
                if c.suite==s:
                    n += 1
            if n>nMax:
                max_suite=s
                nMax=n
        #set the trump suite on the card class
        Card.trump_suite=max_suite

    #Pick a card to open a trick
    #
    # There are no restrictions on card to be selected.
    #
    # AI is trivial and will select highest ranked card. This will
    # tend to clear out the trump suite fast!
    def open_trick(self):
        #select the card to play
        play = max(enumerate(self.cards), key = operator.itemgetter(1))[0]
        #return the selected card and remove it from the hand
        return self.cards.pop(play)

    #Determine the legal moves given the player's hand and the current
    #state of the trick
    #
    #rules which apply:
    #
    #  a player must follow suite if they can
    # 
    #  if the player's partener is not already winning the trick and
    #  the player has the option to win the trick they MUST do so
    # 
    def legal_moves(self, trick):
        #collect the cards that are in the suite which was lead
        in_suite = [i for i,c in enumerate(self.cards) if c.suite == trick[0].suite]
        #check who is winning and if we must win
        trick_win = max(enumerate(trick),key = operator.itemgetter(1))[0]
        must_win=True
        if len(trick)==2 and trick_win==0:
            must_win=False
        elif len(trick)==3 and trick_win==1:
            must_win=False
        #Apply rules
        if len(in_suite)>0:
            #we have cards in the lead suite
            if must_win:
                #we are required to win, so check if we can
                legal = [i for i in in_suite
                         if self.cards[i]>trick[trick_win]]
                if (len(legal)==0):
                    #could not win but must follow suite
                    legal=in_suite
            else:
                #parterner has hand, but we must follow suite
                legal = in_suite
        else:
            #we are void of suite
            if must_win:
                #check our hand for winning trump cards
                legal = [i for i,c in enumerate(self.cards)
                         if c > trick[trick_win]]
                if (len(legal)==0):
                    #can't win...play any
                    legal = list(range(len(self.cards)))
            else:
                #not required to win...play any
                legal = list(range(len(self.cards)))
        return legal

    #play a card which follows the rules with a simple AI to win if we
    #can and play the lowest card if we can't
    def play_card(self,trick):
        in_suite = list(filter(lambda c: c.suite == Card.suite_led,
                               self.cards))
        if (len(in_suite)>0):
            #required to play in suite
            max_card = max(in_suite)
            if any([card > max_card for card in trick]):
                #Best card in suite can't win, throw out the lowest
                min_card = min(in_suite)
                return self.cards.pop(self.cards.index(min_card))
            return self.cards.pop(self.cards.index(max_card))
        else:
            #no cards in suite
            in_trump = list(filter(lambda c: c.suite == Card.trump_suite,self.cards))
            if len(in_trump)>0:
                #todo - choose the trump smarter
                max_trump = max(in_trump)
                return self.cards.pop(self.cards.index(max_trump))
            else:
                #no trump cards no cards in suite
                #throw out lowest card
                smallest =  min(self.cards)
                return self.cards.pop(self.cards.index(smallest))

    #Add a trick the stack of winnings
    def take_trick(self,trick):
        self.tricks.append(trick)

    #count the points in the tricks won
    def score_tricks(self):
        hand_score=0
        for t in self.tricks:
            for c in t:
                hand_score+=c.score
        self.score += hand_score
        return hand_score


#Derive from the Player class and provide a command line UI for card selection    
class HumanPlayer(Player):

    #Allow user to pick any card to play
    def open_trick(self):
        #print a list of all the cards with the selection index to the left
        for i,c in enumerate(self.cards):
            print('{:>2d}'.format(i)+" "+str(c))
        #prompt for input
        n = int(input("Pick a card to lead the trick (trump is " + Card.trump_suite +")"))
        #require the input to be valid
        while not n in range(len(self.cards)):
            n = int(input ("Try again!:"))
        #remove the card from the hand and return it
        return self.cards.pop(n)

    #Allow user to pick a legal card to play
    def play_card(self,trick):
        #display the current state of the trick for the player to follow
        print("")
        print("Trick so far:")
        #find the current winner to highlight with a *
        max_idx = max(enumerate(trick), key=operator.itemgetter(1))[0]
        for i,c in enumerate(trick):
            if(i==max_idx):
                print(str(c) + " *")
            else:
                print(c)
        #determine the possible legal moves given the hand and state of the trick
        legal=self.legal_moves(trick)
        #print a list of all the cards with the selection index to the left legal moves
        #are highlighted with an @ symbol
        print("\nPlayer Hand:")
        for i,c in enumerate(self.cards):
            if i in legal:
                print('{:>2d}'.format(i)+" "+str(c)+ " @")
            else:
                print('{:>2d}'.format(i)+" "+str(c))
        #prompt for input and require it to be valid
        n = int(input("Pick a card to play (trump is " + Card.trump_suite +")"))
        while not n in legal:
            n = int(input ("Try again!:"))
        return self.cards.pop(n)

#manage the state of the game
class Game:
    def __init__(self):
        self.deck = []
        self.lead_player =0
        self.dealer=0
        #create 3 AI players and 1 humman
        self.players = []
        for i in range(3):
            self.players.append(Player())
        self.players.append(HumanPlayer())

    #create a set of cards and distribut them to teh players
    #this is done at the start of each hand
    def deal(self):
        self.deck = Deck()
        self.deck.shuffle()
        ncards = len(self.deck.cards)
        for p in self.players:
            p.new_hand()
            for c in range(ncards//4):
                p.add_card(self.deck.cards.pop())
            p.sort_hand()

    #play out a single trick by getting a card from each player and
    #determining the winning player
    def play_trick(self):
        #have the lead player pick any card and make the selected
        #card define the lead suite
        trick = [self.players[self.lead_player].open_trick()]
        Card.suite_led = trick[0].suite
        #have each of the following players follow suite
        for p in [(x + self.lead_player + 1)%4 for x in range(3)]:
            card = self.players[p].play_card(trick)
            trick.append(card)
        #determine the winner and have them take the trick
        winner = max(enumerate(trick), key=operator.itemgetter(1))[0]
        winner += self.lead_player
        winner %= 4
        self.players[winner].take_trick(trick)
        return (trick,winner)

    #play through a hand of manille, deal and run through all the tricks
    def play_hand(self):
        #have the dealer chose the trump card
        self.players[self.dealer].chose_trump()
        #set the dealer to be the first player
        self.lead_player = self.dealer
        self.dealer += 1
        #play through all the tricks
        while(len(self.players[0].cards)>0):
            trick,winner = self.play_trick()
            for i,c in enumerate(trick):
                print("Player " + str(1+((self.lead_player+i)%4))
                      + " " + str(c))
            print ("Player " + str(1+winner) + " takes trick")
            print ("")
            self.lead_player = winner
        #display the scores
        print("Hand Ends")
        for i,p in enumerate(self.players):
            p.score_tricks()
            print ("Player "+ str(i+1) + " score " + str(p.score))


def RUNIT():
    g=Game()
    g.deal()
    g.play_hand()
            
if __name__ == "__main__":                
    RUNIT()
    
