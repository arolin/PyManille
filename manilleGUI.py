import sys
from PyQt4 import QtCore, QtGui
from manille_ui import *
from manille import *
import time
import threading

#qt string stuff
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

#necessary for debugging in qt        
def debug_trace():
    '''Set a tracepoint in the Python debugger that works with Qt'''
    from PyQt4.QtCore import pyqtRemoveInputHook
    from pdb import set_trace
    pyqtRemoveInputHook()
    set_trace()
    
#threading event for waiting on a card click
card_clicked_event = threading.Event()


#Derive form the Player class to handle play through the GUI
class GUIPlayer(Player):

    #Allow the user to select the trump suite if they have the deal
    def chose_trump(self):
        GUI.status_disp('Pick the trump suite')
        #wait for the gui to notify card clicking
        card_clicked_event.wait()
        card_clicked_event.clear()
        while not self.selected_card in range(len(self.cards)):
            card_clicked_event.wait()
            card_clicked_event.clear()
        #set the selected card's suite as the trump suite in the card class
        Card.trump_suite = self.cards[self.selected_card].suite

    
    #Allow the user to play the opening move to a trick
    def open_trick(self):
        global card_clicked_event
        GUI.status_disp('Player 1, please select a leading card.')
        #wait for the gui to notify card clicking
        card_clicked_event.wait()
        card_clicked_event.clear()
        #make sure the user clicked a valid card
        while not self.selected_card in range(len(self.cards)):
            card_clicked_event.wait()
            card_clicked_event.clear()
        #pop the card from the hand and return it
        card = self.cards.pop(self.selected_card)
        #tell the GUI to update the display of the hand
        GUI.display_hand()
        #return the selected card
        return card

    #Allow the user to follow in a trick
    #remarkable similar to opening a trick except
    #legal moves are reduced
    def play_card(self,trick):
        GUI.display_trick(trick)
        GUI.status_disp("Pick a card.\t\t" + suites[trick[0].suite] + " was lead.")
        legal=self.legal_moves(trick)
        #wait for the gui to notify card clicking
        card_clicked_event.wait()
        card_clicked_event.clear()
        #make sure the user clicked a valid card
        while not self.selected_card in legal:
            GUI.status_disp("That card can not be played! Pick a legal card.\t\t" + suites[trick[0].suite] + " was lead.")
            card_clicked_event.wait()
            card_clicked_event.clear()
        #pop the card from the hand and return it
        card = self.cards.pop(self.selected_card)
        #tell the GUI to update the display of the hand
        GUI.display_hand()
        #return the selected card
        return card
            
    

class ManilleGUI(QtGui.QMainWindow):
    #triggers to make GUI updates
    trigger_trick_disp = QtCore.pyqtSignal(object)
    trigger_hand_disp = QtCore.pyqtSignal()
    trigger_trump_disp = QtCore.pyqtSignal()
    trigger_status_disp = QtCore.pyqtSignal(object)
    hide_next = QtCore.pyqtSignal()
    show_next = QtCore.pyqtSignal()

    #event to wait on to wait for user to click next at end of trick
    next_hand_event = threading.Event()

    #slot for next being clicked - sets the event that gets waited on
    def clicked_next(self):
        self.next_hand_event.set()

    def trump_disp(self):
        trump_img = "GreyWyvern/cardset/" + Card.trump_suite +".gif"
        self.ui.trump_disp.setPixmap(QtGui.QPixmap(_fromUtf8(trump_img)))

    def play_game(self):
        self.hide_next.emit()
        while 1:
            self.deal()
            self.display_hand()
            self.play_hand()
        
    #play through a hand of manille, deal and run through all the tricks
    def play_hand(self):
        #have the dealer chose the trump card
        self.players[self.dealer].chose_trump()
        #have the GUI updated the trump card
        self.trigger_trump_disp.emit()
        #set the dealer to be ther first player and increment the
        #dealer for the next hand
        self.lead_player = (self.dealer + 1)%kNumPlayers
        self.dealer += 1
        self.dealer %=kNumPlayers
        #while there are cards left in the hand play each trick
        while(len(self.players[0].cards)>0):
            #clear the display of the current trick
            self.trigger_trick_disp.emit([])
            #play the trick
            trick,winner = self.play_trick()
            #display the finished trick and wait for the user to
            #acknowledge
            self.trigger_trick_disp.emit(trick)
            #announce the results of the trick
            points = sum([c.score for c in trick])
            points = 'There were ' + str(points) + ' points in the trick.'
            if (winner==0):
                self.status_disp( 'You won the trick! ' + points)
            elif (winner==2):
                self.status_disp( 'Your partner, Player 3, won the trick! '+ points)
            else:
                self.status_disp( 'Your opponent, Player ' + str(winner+1) +', won the trick. '+ points)
            #prompt the user to start the next trick
            self.show_next.emit()
            self.next_hand_event.wait()
            self.next_hand_event.clear()
            self.hide_next.emit()
            #set the winner of the trick to start the next trick
            self.lead_player = winner
        #Report the scores for the hand
        scores = [p.score_tricks() for p in self.players]
        score_str=''
        for i,score in enumerate(scores):
            score_str += 'Player ' + str(i+1) +':' + str(score) + '/'
        score_str +='\tYour team :' + str(self.players[0].score+self.players[2].score)
        score_str +='\tTheir team :' + str(self.players[1].score+self.players[3].score)
        self.status_disp(score_str)


    #This is the relay from each of the clicked cards to set the card
    #that was clicked and notify the human player object
    def clicked_card(self, n):
        self.human.selected_card=n
        global card_clicked_event
        card_clicked_event.set()
            
    
    #each of the cards is given is own slot which forwards the call to
    #the clicked_card method - @TODO - this is probably not the slickest way!
    def card0(self): self.clicked_card(0)
    def card1(self): self.clicked_card(1)
    def card2(self): self.clicked_card(2)
    def card3(self): self.clicked_card(3)
    def card4(self): self.clicked_card(4)
    def card5(self): self.clicked_card(5)
    def card6(self): self.clicked_card(6)
    def card7(self): self.clicked_card(7)


    #setup all the connections and other qt necesaries
    def setup_ui(self):
        self.ui = Ui_manille()
        self.ui.setupUi(self)
        #Map the hand display to an array
        #there's probably a nicer way to do this!
        self.cardsUI = [self.ui.card0,
                        self.ui.card1,
                        self.ui.card2,
                        self.ui.card3,
                        self.ui.card4,
                        self.ui.card5,
                        self.ui.card6,
                        self.ui.card7]
        #map each of the trick display slots to an array
        self.trickUI = [self.ui.T0,
                        self.ui.T1,
                        self.ui.T2,
                        self.ui.T3]
        #connect each of the card objects to a relay slot
        QtCore.QObject.connect(self.ui.card0,QtCore.SIGNAL("clicked()"),self.card0)
        QtCore.QObject.connect(self.ui.card1,QtCore.SIGNAL("clicked()"),self.card1)
        QtCore.QObject.connect(self.ui.card2,QtCore.SIGNAL("clicked()"),self.card2)
        QtCore.QObject.connect(self.ui.card3,QtCore.SIGNAL("clicked()"),self.card3)
        QtCore.QObject.connect(self.ui.card4,QtCore.SIGNAL("clicked()"),self.card4)
        QtCore.QObject.connect(self.ui.card5,QtCore.SIGNAL("clicked()"),self.card5)
        QtCore.QObject.connect(self.ui.card6,QtCore.SIGNAL("clicked()"),self.card6)
        QtCore.QObject.connect(self.ui.card7,QtCore.SIGNAL("clicked()"),self.card7)
        #connect the next button
        QtCore.QObject.connect(self.ui.next ,QtCore.SIGNAL("clicked()"),self.clicked_next)
        #connect the triggers which relay the UI update calls
        self.trigger_trick_disp.connect(self.display_trick_)
        self.trigger_hand_disp.connect(self.display_hand_)
        self.trigger_trump_disp.connect(self.trump_disp)
        self.trigger_status_disp.connect(self.status_disp_)
        self.hide_next.connect(self.ui.next.hide)
        self.show_next.connect(self.ui.next.show)
        

            
    def __init__(self, parent=None):
        #Take care of loading the Qt GUI
        QtGui.QWidget.__init__(self, parent)
        self.setup_ui()
        #Create the Game elements
        self.deck = []
        self.players = []
        #create human player 1
        self.human=GUIPlayer()
        self.players.append(self.human)
        #create 3 AI players
        for i in range(3):
            self.players.append(Player())
        #set the human as the first dealer
        self.dealer=1
        self.lead_player = self.dealer + 1
       

    def start_game(self):
        #create a thread to run the game
        self.game_thread = threading.Thread(target=self.play_game)
        self.game_thread.start()
        
    #deal the cards to each player
    def deal(self):
        self.deck = Deck()
        self.deck.shuffle()
        ncards = len(self.deck.cards)
        for p in self.players:
            p.new_hand()
            for c in range(ncards//4):
                p.add_card(self.deck.cards.pop())
                p.sort_hand()

    #relay the call to display by using emit to notify the GUI thread
    def display_hand(self):
        self.trigger_hand_disp.emit()

    #perform the actual display update in the GUI thread - DO NOT CALL DIRECTLY
    def display_hand_(self):
        icon = QtGui.QIcon()
        #load the image for each card in the hand into the appropriate slot
        for i,c in enumerate(self.human.cards):
            gifname =  rankIcon[c.rank]+c.suite.lower()
            icon.addPixmap(QtGui.QPixmap(_fromUtf8("GreyWyvern/cardset/"+gifname+".gif")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.cardsUI[i].setIcon(icon)
        #make sure that any empty slots are cleared
        for i in range(len(self.human.cards),8):
            icon.addPixmap(QtGui.QPixmap(_fromUtf8("GreyWyvern/cardset/bottom01-n.gif")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.cardsUI[i].setIcon(icon)

    #relay the call to display the trick using emit to notify the GUI thread
    def display_trick(self, trick):
        self.trigger_trick_disp.emit(trick)

    #performe the actual display update in the GUI thread -  DO NOT CALL DIRECTLY
    def display_trick_(self, trick):
        #clear the last trick
        for i in range(4):
            self.trickUI[i].setPixmap(QtGui.QPixmap(_fromUtf8("GreyWyvern/cardset/bottom01-n.gif")))
        #display new trick
        for i,c in enumerate(trick):
            ip = (self.lead_player + i)%4
            gifname =  rankIcon[c.rank]+c.suite.lower()
            self.trickUI[ip].setPixmap(QtGui.QPixmap(_fromUtf8("GreyWyvern/cardset/"+
                                                               gifname+".gif")))

    #run through each player in the trick and find a winner
    def play_trick(self):
        #Have either the dealer or the last winner (lead_player)
        #open the trick and define the leade suite
        trick = [self.players[self.lead_player].open_trick()]
        Card.suite_led = trick[0].suite
        #Have the following 3 players follow suite
        for p in [(x + self.lead_player + 1)%4 for x in range(3)]:
            card = self.players[p].play_card(trick)
            trick.append(card)
        #Determine the trick winner and add the trick to the player's loot
        winner = max(enumerate(trick), key=operator.itemgetter(1))[0]
        winner += self.lead_player
        winner %= 4
        self.players[winner].take_trick(trick)
        return (trick,winner)

    def status_disp(self,msg):
        self.trigger_status_disp.emit(msg)
    
    def status_disp_(self, msg):
        self.ui.statusBar.showMessage(msg)
    


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    GUI = ManilleGUI()
    GUI.show()
    GUI.start_game()
    sys.exit(app.exec_())
    GUI.game_thread.join()
