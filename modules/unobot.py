#!/usr/bin/env python2
"""
Copyright 2010 Tamas Marki. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY TAMAS MARKI ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL TAMAS MARKI OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


[18:03] <Lako> .play w 3
[18:03] <unobot> TopMobil's turn. Top Card: [*]
[18:03] [Notice] -unobot- Your cards: [4][9][4][8][D2][D2]
[18:03] [Notice] -unobot- Next: hatcher (5 cards) - Lako (2 cards)
[18:03] <TopMobil> :O
[18:03] <Lako> :O
"""

import os
import random
from datetime import datetime, timedelta
import time
import itertools
import yaml
import operator

away_last = 0

# Remember to change these 3 lines or nothing will work
CHANNEL = '##uno'
OLD_SCOREFILE = os.path.expanduser("~/.jenni/unoscores.txt")
SCOREFILE = os.path.expanduser("~/.jenni/unoscores.yml")
# Only the owner (starter of the game) can call .unostop to stop the game.
# But this calls for a way to allow others to stop it after the game has been idle for a while.
# After this set time, anyone can stop the game via .unostop
# Set the time ___in minutes___ here: (default is 5 mins)
INACTIVE_TIMEOUT = 3

STRINGS = {
    'ALREADY_STARTED': '\x0300,01Game already started by %s! Type ".join" to join!',
    'GAME_STARTED': '\x0300,01IRC-UNO started by %s - Type ".join" to join!',
    'GAME_STOPPED': '\x0300,01Game stopped.',
    'CANT_STOP': '\x0300,01%s is the game owner, you can\'t stop it! To force stop the game, please wait %s seconds.',
    'DEALING_IN': '\x0300,01Dealing %s into the game as player #%s!',
    'JOINED': '\x0300,01Dealing %s into the game as player #%s!',
    'ALREADY_JOINED': '\x0300,01Player, %s, is already in the game as player #%s!',
    'ENOUGH': '\x0300,01There are enough players, type .deal to start!',
    'NOT_STARTED': '\x0300,01Game not started, type .uno to start!',
    'NOT_ENOUGH': '\x0300,01Not enough players to deal yet.',
    'NEEDS_TO_DEAL': '\x0300,01%s needs to deal.',
    'ALREADY_DEALT': '\x0300,01Already dealt.',
    'ON_TURN': '\x0300,01It\'s the turn of %s',
    'DONT_HAVE': '\x0300,01You don\'t have that card, %s',
    'DOESNT_PLAY': '\x0300,01That card does not play, %s',
    'UNO': '\x0300,01UNO! %s has ONE card left!',
    'WIN': '\x0300,01We have a winner! %s!!!! This game took %s',
    'DRAWN_ALREADY': '\x0300,01You\'ve already drawn, either .pass or .play!',
    'DRAWS': '\x0300,01%s draws a card',
    'DRAWN_CARD': '\x0300,01Drawn card: %s',
    'DRAW_FIRST': '\x0300,01%s, you need to draw first!',
    'PASSED': '\x0300,01%s passed!',
    'NO_SCORES': '\x0300,01No scores yet',
    'TOP_CARD': '\x0300,01It\'s the turn of %s | Top Card: %s',
    'YOUR_CARDS': '\x0300,01Your cards: %s',
    'NEXT_START': '\x0300,01Next: ',
    'NEXT_PLAYER': '\x0300,01%s (%s cards)',
    'D2': '\x0300,01%s draws two and is skipped!',
    'CARDS': '\x0300,01Cards: %s',
    'WD4': '\x0300,01%s draws four and is skipped!',
    'WD40': '\x0300,01%s draws forty and is skipped!',
    'SKIPPED': '\x0300,01%s is skipped!',
    'REVERSED': '\x0300,01Order reversed!',
    'GAINS': '\x0300,01%s gains %s points!',
    'SCORE_ROW': '\x0300,01#%(rank)s %(nick)s (%(points)s points, won %(wins)s of %(games)s games, %(points_per_game)0.2f points per game, %(percent_wins)0.2f percent wins)',
    'GAME_ALREADY_DEALT': '\x0300,01Game has already been dealt, please wait until game is over or stopped.',
    'PLAYER_COLOR_ENABLED': '\x0300,01Hand card colors \x0309,01enabled\x0300,01! Format: <COLOR>/[<CARD>].  Example: R/[D2] is a red Draw Two. Type \'.uno-help\' for more help.',
    'PLAYER_COLOR_DISABLED': '\x0300,01Hand card colors \x0304,01disabled\x0300,01.',
    'DISABLED_PCE': '\x0300,01Hand card colors is \x0304,01disabled\x0300,01 for %s. To enable, \'.pce-on\'',
    'ENABLED_PCE': '\x0300,01Hand card colors is \x0309,01enabled\x0300,01 for %s. To disable, \'.pce-off\'',
    'PCE_CLEARED': '\x0300,01All players\' hand card color setting is reset by %s.',
    'PLAYER_LEAVES': '\x0300,01Player %s has left the game.',
    'OWNER_CHANGE': '\x0300,01Owner %s has left the game. New owner is %s.',
    'STAT_TYPE_ERROR': '\x0300,01Supported rankings are %s.',
    'FORCE_PLAY': '\x0300,01Forcing %s to play.',
    'CANT_FORCE_PLAY': '\x0300,01You can\'t force %s to play yet; wait another %s seconds.',
    'CANT_FORCE_LEAVE': '\x0300,01You can\'t force %s to leave the game yet; wait another %s seconds.',
    'PLAYS': '\x0300,01%s plays %s.',
    'BOT_PLAY_ON': '\x0300,01%s has turned on autopilot.',
    'BOT_PLAY_OFF': '\x0300,01%s has turned off autopilot.',
}

def parse_old_scores(filename):
    scores = {}
    # Old file format was <nick> <games> <wins> <points> [time]
    for line in open(filename):
        parts = line.strip('\n').split(' ')
        if len(parts) < 5:
            parts.append('0')
        player = parts[0]
        games, wins, points, duration = [int(x) for x in parts[1:]]
        scores[player] = {
            'games': games,
            'time': duration,
            'wins': wins,
            'points': points,
        }
    return scores


class ScoreBoard(object):
    def __init__(self, filename, old_filename):
        self.filename = filename
        self.old_filename = old_filename
        try:
            self.scores = yaml.load(open(self.filename, 'r'))
        except Exception:
            try:
                self.scores = parse_old_scores(old_filename)
            except Exception:
                self.scores = {}

    def save(self):
        try:
            yaml.dump(self.scores, open(self.filename, 'w'))
        except Exception, e:
            print 'Failed to write score file %s' % e

    def update(self, players, winner, score, time):
        for player in players:
            player = player.lower()
            player_stats = self.scores.setdefault(player, {})
            player_stats['games'] = player_stats.get('games', 0) + 1
            player_stats['time'] = player_stats.get('time', 0) + time

        winner_stats = self.scores[winner]
        winner_stats['wins'] = winner_stats.get('wins', 0) + 1
        winner_stats['points'] = winner_stats.get('points', 0) + score

    def stats(self):
        for player, player_stats in self.scores.items():
            stats = {
                'nick': player,
                'games': 0,
                'time': 0,
                'wins': 0,
                'points': 0,
            }
            stats.update(player_stats)
            if stats['wins']:
                stats['points_per_game'] = float(stats['points']) / stats['games']
            else:
                stats['points_per_game'] = 0
            stats['percent_wins'] = 100*float(stats['wins'])/stats['games']
            yield stats

    def _stats_by(self, key):
        return sorted(self.stats(), key=operator.itemgetter(key), reverse=True)

    def stats_by_percent_wins(self):
        return self._stats_by('percent_wins')

    def stats_by_points_per_game(self):
        return self._stats_by('points_per_game')

    def stats_by_points(self):
        return self._stats_by('points')

    def stats_by_wins(self):
        return self._stats_by('wins')

    def stats_by_games(self):
        return self._stats_by('games')


def tokenize(bot_input):
    """Returns list of capitalized words from the input."""
    return bot_input.upper().split()


class UnoBot:
    def __init__(self):
        self.colored_card_nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'R', 'S', 'D2']
        self.card_scores = dict((str(n), n) for n in range(10))
        self.card_scores.update({'R' : 20, 'S' : 20, 'D2' : 20, 'W' : 50, 'WD4' : 50, 'WD40' : 150})
        self.colors = 'RGBY'
        self.special_cards = ['W', 'WD4']
        self.extra_special_cards = ['WD40']
        self.all_special_cards = self.special_cards + self.extra_special_cards
        self.all_cards = self.colored_card_nums + self.all_special_cards
        self.players = dict()
        self.owners = dict()
        self.players_pce = dict()  # Player color enabled hash table
        self.playerOrder = list()
        self.game_on = False # Used as both a flag to represent if the game is started, and the name of the owner of the game
        self.currentPlayer = 0
        self.topCard = None
        self.way = 1
        self.drawn = False
        self.scoreFile = SCOREFILE
        self.deck = list()
        self.dealt = False
        self.lastActive = datetime.now()
        self.timeout = timedelta(minutes=INACTIVE_TIMEOUT)
        self.nonstartable_cards = set(itertools.product(self.colors, ['R', 'S', 'D2'])) | set(('*', face) for face in self.all_special_cards)
        self.use_extra_special = 0
        self.scores = ScoreBoard(SCOREFILE, OLD_SCOREFILE)
        self.bot_players = set()

    def _activity(self):
        self.lastActive = datetime.now()

    def start(self, jenni, owner):
        owner = owner.lower()
        if self.game_on:
            jenni.msg(CHANNEL, STRINGS['ALREADY_STARTED'] % self.game_on)
        else:
            self._activity()
            self.game_on = owner
            self.deck = list()
            jenni.msg(CHANNEL, STRINGS['GAME_STARTED'] % owner)
            self.players = dict()
            self.players[owner] = list()
            self.playerOrder = [owner]
            self.bot_players = set()
            jenni.msg(CHANNEL, STRINGS['JOINED'] % (owner, self.playerOrder.index(owner) + 1))
            if self.players_pce.get(owner, 0):
                jenni.notice(owner, STRINGS['ENABLED_PCE'] % owner)

    def stop(self, jenni, input):
        nickk = (input.nick).lower()
        tmptime = datetime.now()
        if nickk == self.game_on or tmptime - self.lastActive > self.timeout:
            jenni.msg(CHANNEL, STRINGS['GAME_STOPPED'])
            self.game_on = False
            self.dealt = False
        elif self.game_on:
            jenni.msg(CHANNEL, STRINGS['CANT_STOP'] % (self.game_on, self.timeout.seconds - (tmptime - self.lastActive).seconds))

    def join(self, jenni, input):
        #print dir(jenni)
        #print dir(input)
        nickk = (input.nick).lower()
        self._add_player(jenni, nickk)

    def join_bot(self, jenni, input):
        tokens = tokenize(input)
        name = tokens[1].lower()
        self._add_player(jenni, name)
        self.bot_players.add(name)

    def bot_me_on(self, jenni, input):
        player = input.nick.lower()
        self.bot_players.add(player)
        jenni.msg(CHANNEL, STRINGS['BOT_PLAY_ON'] % player)
        if self.get_current_player() == player:
            self._play_bots(jenni)

    def bot_me_off(self, jenni, input):
        player = input.nick.lower()
        self.bot_players.discard(player)
        jenni.msg(CHANNEL, STRINGS['BOT_PLAY_OFF'] % player)

    def _add_player(self, jenni, player):
        if self.game_on:
            if not self.dealt:
                if player not in self.players:
                    self.players[player] = list()
                    self.playerOrder.append(player)
                    self._activity()
                    if self.players_pce.get(player, 0):
                        jenni.notice(player, STRINGS['ENABLED_PCE'] % player)
                    if self.deck:
                        for i in xrange(0, 7):
                            self.players[player].append(self.getCard())
                        jenni.msg(CHANNEL, STRINGS['DEALING_IN'] % (player, self.playerOrder.index(player) + 1))
                    else:
                        jenni.msg(CHANNEL, STRINGS['JOINED'] % (player, self.playerOrder.index(player) + 1))
                        if len (self.players) == 2:
                            jenni.msg(CHANNEL, STRINGS['ENOUGH'])
                else:
                    jenni.msg(CHANNEL, STRINGS['ALREADY_JOINED'] % (player, self.playerOrder.index(player) + 1))
            else:
                jenni.msg(CHANNEL, STRINGS['GAME_ALREADY_DEALT'])
        else:
            jenni.msg(CHANNEL, STRINGS['NOT_STARTED'])

    def deal(self, jenni, input):
        nickk = (input.nick).lower()
        if not self.game_on:
            jenni.msg(CHANNEL, STRINGS['NOT_STARTED'])
            return
        if len(self.players) < 2:
            jenni.msg(CHANNEL, STRINGS['NOT_ENOUGH'])
            return
        if nickk != self.game_on:
            jenni.msg(CHANNEL, STRINGS['NEEDS_TO_DEAL'] % self.game_on)
            return
        if len(self.deck):
            jenni.msg(CHANNEL, STRINGS['ALREADY_DEALT'])
            return

        tok = tokenize(input)
        if len(tok) > 1 and tok[1] == 'X': # .deal x [optional count]
            self.use_extra_special = len(self.playerOrder)
            if len(tok) > 2:
                self.use_extra_special = int(tok[2])
        else:
            self.use_extra_special = 0

        self.startTime = datetime.now()
        self._activity()
        self.deck = self.createnewdeck()
        for i in xrange(0, 7):
            for p in self.players:
                self.players[p].append(self.getCard ())
        self.topCard = self.getCard()
        while self.topCard in self.nonstartable_cards:
           self.topCard = self.getCard()
        self.dealt = True
        self.currentPlayer = 0
        self.cardPlayed(jenni, self.topCard)
        self._end_turn(jenni)

    def _play_card(self, jenni, player, card):
        """The card has already been removed from the player's hand; finishes
        the turn, or even the game, if someone won.  Wild cards have their
        color already set.
        """
        jenni.msg(CHANNEL, STRINGS['PLAYS'] % (player, self.renderCards(player, [card], True)))
        self.cardPlayed(jenni, card)
        if len(self.players[player]) == 1:
            jenni.msg(CHANNEL, STRINGS['UNO'] % player)
        elif len(self.players[player]) == 0:
            jenni.msg(CHANNEL, STRINGS['WIN'] % (player, (datetime.now() - self.startTime)))
            self.gameEnded(jenni, player)
            return
        self._end_turn(jenni)

    def _pass(self, jenni, player):
        jenni.msg(CHANNEL, STRINGS['PASSED'] % self.playerOrder[self.currentPlayer])
        self._end_turn(jenni)

    def play(self, jenni, input):
        player = (input.nick).lower()
        if not self.game_on or not self.deck:
            return
        if player != self.get_current_player():
            jenni.msg(CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        tok = tokenize(input)
        if len(tok) != 3:
            return
        face, color = tok[1:]
        # Allow face and color in reverse order
        if (color not in self.colors or face not in self.all_cards) and color in self.all_cards and face in self.colors:
            face, color = color, face

        playcard = (color, face)
        if color not in self.colors:
            jenni.msg(CHANNEL, STRINGS['DOESNT_PLAY'] % player)
        if face not in self.all_cards:
            jenni.msg(CHANNEL, STRINGS['DOESNT_PLAY'] % player)
        if not self.cardPlayable(playcard):
            jenni.msg(CHANNEL, STRINGS['DOESNT_PLAY'] % self.playerOrder[self.currentPlayer])
            return

        if face in self.all_special_cards:
            searchcard = ('*', face)
        else:
            searchcard = (color, face)

        cards = self.get_players_cards(player)
        try:
            cards.remove(searchcard)
        except ValueError:
            jenni.notice(player, STRINGS['DONT_HAVE'] % player)
            return

        self._play_card(jenni, player, playcard)

    def auto_play(self, jenni, input):
        nickk = (input.nick).lower()
        if not self.game_on or not self.deck:
            return
        if nickk != self.playerOrder[self.currentPlayer]:
            jenni.msg(CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        self._auto_play(jenni, nickk)

    def _auto_play(self, jenni, player):
        playable_cards = [c for c in self.players[player] if self.cardPlayable(c)]
        if not playable_cards:
            self._draw(jenni, player)
        playable_cards = [c for c in self.players[player] if self.cardPlayable(c)]
        if playable_cards:
            # If we have a non-wild card that plays, choose from those
            non_wilds = [c for c in playable_cards if c[0] != '*']
            if non_wilds:
                playable_cards = non_wilds
            # random card
            card = random.choice(playable_cards)
            self.players[player].remove(card)
            color, face = card
            # if it's wild, random color
            if color == '*':
                colors_in_hand = [c for c,f in self.players[player] if c != '*']
                if not colors_in_hand: # nothin', or nothin' but wilds
                    colors_in_hand = 'BGRY'
                color = random.choice(colors_in_hand)
            card = (color, face)
            self._play_card(jenni, player, card)
        else:
            self._pass(jenni, player)

    def force_play(self, jenni, input):
        now = datetime.now()
        player = self.playerOrder[self.currentPlayer]
        if now - self.lastActive > self.timeout:
            jenni.msg(CHANNEL, STRINGS['FORCE_PLAY'] % player)
            self._auto_play(jenni, player)
        else:
            jenni.msg(CHANNEL, STRINGS['CANT_FORCE_PLAY'] % (player, self.timeout.seconds - (now - self.lastActive).seconds))

    def _draw(self, jenni, player):
        self.drawn = True
        jenni.msg(CHANNEL, STRINGS['DRAWS'] % player)
        card = self.getCard()
        self.players[player].append(card)
        self._activity()
        jenni.notice(player, STRINGS['DRAWN_CARD'] % self.renderCards(player, [card], 0))

    def draw(self, jenni, input):
        player = input.nick.lower()
        if not self.game_on or not self.deck:
            return
        if player != self.playerOrder[self.currentPlayer]:
            jenni.msg(CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        if self.drawn:
            jenni.msg(CHANNEL, STRINGS['DRAWN_ALREADY'])
            return
        self._draw(jenni, player)

    # this is not a typo, avoiding collision with Python's pass keyword
    def passs(self, jenni, input):
        player = input.nick.lower()
        if not self.game_on or not self.deck:
            return
        if player != self.playerOrder[self.currentPlayer]:
            jenni.msg(CHANNEL, STRINGS['ON_TURN'] % self.get_current_player())
            return
        if not self.drawn:
            jenni.msg(CHANNEL, STRINGS['DRAW_FIRST'] % player)
            return
        self._pass(jenni, player)

    def _end_turn(self, jenni):
        self.incPlayer()
        self._activity()
        self.showOnTurn(jenni)
        self._play_bots(jenni)

    def _play_bots(self, jenni):
        # handle bot players
        player = self.get_current_player()
        if player in self.bot_players:
            self._auto_play(jenni, player)

    def scores_messages(self, ranked_scores):
        for n, score in enumerate(ranked_scores, 1):
            score['rank'] = n
            yield STRINGS['SCORE_ROW'] % score

    def top10(self, jenni, input):
        nickk = input.nick.lower()
        for message in self.scores_messages(self.scores.stats_by_points_per_game()):
            jenni.msg(nickk, message)

    def createnewdeck(self):
        deck = []
        for i in range(2):
            for face in self.colored_card_nums:
                for color in self.colors:
                    if i > 0 and face == '0':
                        continue
                    deck.append((color, face))
        for a in self.special_cards:
            for i in range(4):
                deck.append(('*', a))
        if len(self.playerOrder) > 4:
            deck *= 2
        # Deal up to two sets of extra special cards per new deck
        for i in range(2):
            if self.use_extra_special > 0:
                deck.extend(('*', c) for c in self.extra_special_cards)
                self.use_extra_special -= 1

        random.shuffle(deck)
        return deck

    def getCard(self):
        ret = self.deck[0]
        self.deck.pop(0)
        if not self.deck:
            self.deck = self.createnewdeck()
        return ret

    def showOnTurn(self, jenni):
        jenni.msg(CHANNEL, STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))
        self.showCards(jenni, self.playerOrder[self.currentPlayer])

    def showCards(self, jenni, user):
        user = user.lower()
        if not self.game_on or not self.deck:
            return
        msg = STRINGS['NEXT_START']

        future_play_order = self.playerOrder[self.currentPlayer+1:] + self.playerOrder[:self.currentPlayer]
        if self.way == -1:
            future_play_order.reverse()
        players_and_card_counts = [STRINGS['NEXT_PLAYER'] % (player, len(self.get_players_cards(player))) for player in future_play_order]

        msg += ' - '.join(players_and_card_counts)
        if user not in self.players:
            jenni.notice(user, msg)
        else:
            jenni.notice(user, STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))
            # Show up to 15 cards per message
            cards = sorted(list(self.players[user]))
            while cards:
                jenni.notice(user, STRINGS['YOUR_CARDS'] % self.renderCards(user, cards[:15], 0))
                cards = cards[15:]
            jenni.notice(user, msg)

    def renderCards(self, nick, cards, is_chan):
        irc_colors = {
            '*': '\x0300,01',
            'B': '\x0311,01',
            'G': '\x0309,01',
            'R': '\x0304,01',
            'Y': '\x0308,01',
        }
        nickk = nick
        if nick:
            nickk = (nick).lower()
        rendered_cards = []
        for color, face in sorted(cards):
            # Might consider this format: "%s[%s%s]" % (irc_colors[color], color, face))
            if not is_chan:
                if self.players_pce.get(nickk, 0):
                    rendered = '%s%s/[%s] ' % (irc_colors[color], color, face)
                else:
                    rendered = '%s[%s]' % (irc_colors[color], face)
            else:
                rendered = '%s(%s) [%s]' % (irc_colors[color], color, face)
            rendered_cards.append(rendered)
        rendered_cards.append(irc_colors['*'])
        return ''.join(rendered_cards)

    def cardPlayable(self, card):
        color, face = card
        if face in self.all_special_cards:
            return True
        top_color, top_face = self.topCard
        if color == top_color:
            return True
        if face == top_face:
            return True
        return False

    def cardPlayed(self, jenni, card):
        target_player = self.get_next_player()
        color, face = card
        if face == 'D2':
            jenni.msg(CHANNEL, STRINGS['D2'] % target_player)
            z = [self.getCard(), self.getCard()]
            jenni.notice(target_player, STRINGS['CARDS'] % self.renderCards(target_player, z, 0))
            self.players[target_player].extend (z)
            self.incPlayer()
        elif face in ['WD4', 'WD40']:
            num = int(face[2:])
            jenni.msg(CHANNEL, STRINGS['WD%s' % num] % target_player)
            z = [self.getCard() for _ in range(num)]
            jenni.notice(target_player, STRINGS['CARDS'] % self.renderCards(target_player, z, 0))
            self.players[target_player].extend(z)
            self.incPlayer()
        elif face == 'S':
            jenni.msg(CHANNEL, STRINGS['SKIPPED'] % target_player)
            self.incPlayer()
        elif face == 'R':
            jenni.msg(CHANNEL, STRINGS['REVERSED'])
            if len(self.players) == 2:
                self.incPlayer()
            self.way = -self.way
        self.topCard = card

    def gameEnded(self, jenni, winner):
        try:
            score = 0
            for player in self.players:
                score += sum(self.card_scores[face] for color, face in self.players[player])
            jenni.msg(CHANNEL, STRINGS['GAINS'] % (winner, score))
            self.saveScores(self.players.keys(), winner, score, (datetime.now() - self.startTime).seconds)
        except Exception, e:
            print 'Score error: %s' % e
        self.players = dict()
        self.playerOrder = list()
        self.game_on = False
        self.currentPlayer = 0
        self.topCard = None
        self.way = 1
        self.dealt = False

    def get_current_player(self):
        return self.playerOrder[self.currentPlayer]

    def get_players_cards(self, player):
        return self.players[player]

    def next_player_number(self):
        return (self.currentPlayer + self.way) % len(self.players)

    def incPlayer(self):
        self.drawn = False
        self.currentPlayer = self.next_player_number()

    def get_next_player(self):
        return self.playerOrder[self.next_player_number()]

    def saveScores(self, players, winner, score, time):
        self.scores.update(players, winner, score, time)
        self.scores.save()

    # Custom added functions ============================================== #

    def showTopCard_demand(self, jenni):
        if not self.game_on or not self.deck:
            return
        jenni.say(STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))

    def leave(self, jenni, input):
        nickk = (input.nick).lower()
        self.remove_player(jenni, nickk)

    def force_leave(self, jenni, input):
        now = datetime.now()
        player = self.playerOrder[self.currentPlayer]
        if now - self.lastActive > self.timeout:
            self.remove_player(jenni, player)
        else:
            jenni.msg(CHANNEL, STRINGS['CANT_FORCE_LEAVE'] % (player, self.timeout.seconds - (now - self.lastActive).seconds))

    def remove_player(self, jenni, nick):
        if not self.game_on:
            return

        user = self.players.get(nick, None)
        if user is not None:
            player = self.get_current_player()
            poke_bots = False
            if nick == player:
                self.incPlayer()
                player = self.get_current_player()
                poke_bots = True
            self.playerOrder.remove(nick)
            del self.players[nick]
            self.currentPlayer = self.playerOrder.index(player)

            jenni.msg(CHANNEL, STRINGS['PLAYER_LEAVES'] % nick)
            numPlayers = len(self.playerOrder)
            if numPlayers == 1 and self.dealt or numPlayers == 0:
                jenni.msg(CHANNEL, STRINGS['GAME_STOPPED'])
                self.game_on = None
                self.dealt = None
                return

            if self.game_on == nick:
                self.game_on = self.playerOrder[0]
                jenni.msg(CHANNEL, STRINGS['OWNER_CHANGE'] % (nick, self.playerOrder[0]))

            if self.dealt:
                jenni.msg(CHANNEL, STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))

            if poke_bots:
                self._play_bots(jenni)

    def enablePCE(self, jenni, nick):
        nickk = nick.lower()
        if not self.players_pce.get(nickk, 0):
            self.players_pce.update({ nickk : 1})
            jenni.notice(nickk, STRINGS['PLAYER_COLOR_ENABLED'])
        else:
            jenni.notice(nickk, STRINGS['ENABLED_PCE'] % nickk)

    def disablePCE(self, jenni, nick):
        nickk = nick.lower()
        if self.players_pce.get(nickk, 0):
            self.players_pce.update({ nickk : 0})
            jenni.notice(nickk, STRINGS['PLAYER_COLOR_DISABLED'])
        else:
            jenni.notice(nickk, STRINGS['DISABLED_PCE'] % nickk)

    def isPCEEnabled(self, jenni, nick):
        nickk = nick.lower()
        if not self.players_pce.get(nickk, 0):
            jenni.notice(nickk, STRINGS['DISABLED_PCE'] % nickk)
        else:
            jenni.notice(nickk, STRINGS['ENABLED_PCE'] % nickk)

    def PCEClear(self, jenni, nick):
        nickk = nick.lower()
        if not self.owners.get(nickk, 0):
            self.players_pce.clear()
            jenni.msg(CHANNEL, STRINGS['PCE_CLEARED'] % nickk)

    def unostat(self, jenni, input):
        ranking_types = {
            'ppg': self.scores.stats_by_points_per_game,
            'pw': self.scores.stats_by_percent_wins,
            'w': self.scores.stats_by_wins,
            'p': self.scores.stats_by_points,
            'g': self.scores.stats_by_games,
        }
        text = input.group().lower().split()

        if len(text) > 1:
            rank_type = text[1].lower()
        else:
            rank_type = 'ppg'
        try:
            ranking = ranking_types[rank_type]
        except KeyError:
            jenni.reply(STRINGS['STAT_TYPE_ERROR'] % ', '.join(ranking_types.keys()))
            return
        limit = None
        try:
            limit = int(text[2])
        except (IndexError, ValueError):
            pass

        messages = list(self.scores_messages(ranking()))
        if limit:
            messages = messages[:limit]
        if messages:
            for message in messages:
                jenni.reply(message)
        else:
            jenni.reply(STRINGS['NO_SCORES'])

unobot = UnoBot()

def uno(jenni, input):
    if input.sender != CHANNEL:
        jenni.reply("Please join %s to play uno!" % (CHANNEL))
    elif input.sender == CHANNEL:
        unobot.start(jenni, input.nick)
uno.commands = ['uno']
uno.priority = 'low'
uno.thread = False
uno.rate = 0

def unostop(jenni, input):
    if not (input.sender).startswith('#'):
        return
    unobot.stop(jenni, input)
unostop.commands = ['unostop']
unostop.priority = 'low'
unostop.thread = False
unostop.rate = 0

def unojoin(jenni, input):
    if not (input.sender).startswith('#'):
        return
    if input.sender == CHANNEL:
        unobot.join(jenni, input)
unojoin.commands = ['ujoin', 'join']
unojoin.priority = 'low'
unojoin.thread = False
unojoin.rate = 0

def unobotjoin(jenni, input):
    if not (input.sender).startswith('#'):
        return
    if input.sender == CHANNEL:
        unobot.join_bot(jenni, input)
unobotjoin.commands = ['joinbot', 'join_bot']
unobotjoin.priority = 'low'
unobotjoin.thread = False
unobotjoin.rate = 0

def deal(jenni, input):
    if not (input.sender).startswith('#'):
        return
    unobot.deal(jenni, input)
deal.commands = ['deal']
deal.priority = 'low'
deal.thread = False
deal.rate = 0

def bot_me_on(jenni, input):
    if not (input.sender).startswith('#'):
        return
    unobot.bot_me_on(jenni, input)
bot_me_on.commands = ['bot_me_on', 'bot-on']
bot_me_on.priority = 'low'
bot_me_on.thread = False
bot_me_on.rate = 0

def bot_me_off(jenni, input):
    if not (input.sender).startswith('#'):
        return
    unobot.bot_me_off(jenni, input)
bot_me_off.commands = ['bot_me_off', 'bot-off']
bot_me_off.priority = 'low'
bot_me_off.thread = False
bot_me_off.rate = 0

def play(jenni, input):
    unobot.play(jenni, input)
play.commands = ['play', 'p']
play.priority = 'low'
play.thread = False
play.rate = 0

def auto_play(jenni, input):
    unobot.auto_play(jenni, input)
auto_play.commands = ['auto_play', 'ap']
auto_play.priority = 'low'
auto_play.thread = False
auto_play.rate = 0

def force_play(jenni, input):
    if not (input.sender).startswith('#'):
        return
    unobot.force_play(jenni, input)
force_play.commands = ['force_play']
force_play.priority = 'low'
force_play.thread = False
force_play.rate = 0

def draw(jenni, input):
    unobot.draw(jenni, input)
draw.commands = ['draw', 'd', 'dr']
draw.priority = 'low'
draw.thread = False
draw.rate = 0

def passs(jenni, input):
    if not (input.sender).startswith('#'):
        return
    unobot.passs(jenni, input)
passs.commands = ['pass', 'pa']
passs.priority = 'low'
passs.thread = False
passs.rate = 0

def unotop10(jenni, input):
    unobot.top10(jenni, input)
unotop10.commands = ['unotop10']
unotop10.priority = 'low'
unotop10.thread = False
unotop10.rate = 0

def show_user_cards(jenni, input):
    unobot.showCards(jenni, input.nick)
show_user_cards.commands = ['cards']
show_user_cards.priority = 'low'
show_user_cards.thread = False
show_user_cards.rate = 0

def top_card(jenni, input):
    if not (input.sender).startswith('#'):
        return
    unobot.showTopCard_demand(jenni)
top_card.commands = ['top']
top_card.priority = 'low'
top_card.thread = False
top_card.rate = 0

def leave(jenni, input):
    if not (input.sender).startswith('#'):
        return
    unobot.leave(jenni, input)
leave.commands = ['leave', 'ragequit', 'rage_quit']
leave.priority = 'low'
leave.thread = False
leave.rate = 0

def force_leave(jenni, input):
    if not (input.sender).startswith('#'):
        return
    unobot.force_leave(jenni, input)
force_leave.commands = ['force_leave', 'force_quit']
force_leave.priority = 'low'
force_leave.thread = False
force_leave.rate = 0

def remove_on_part(jenni, input):
    if input.sender == CHANNEL:
        unobot.remove_player(jenni, (input.nick).lower())
remove_on_part.event = 'PART'
remove_on_part.rule = '.*'
remove_on_part.priority = 'low'
remove_on_part.thread = False
remove_on_part.rate = 0

def remove_on_quit(jenni, input):
    if input.sender == CHANNEL:
        unobot.remove_player(jenni, (input.nick).lower())
remove_on_quit.event = 'QUIT'
remove_on_quit.rule = '.*'
remove_on_quit.priority = 'low'
remove_on_quit.thread = False
remove_on_quit.rate = 0

def remove_on_kick(jenni, input):
    if input.sender == CHANNEL:
        unobot.remove_player(jenni, (input.args[1].lower()))
remove_on_kick.event = 'KICK'
remove_on_kick.rule = '.*'
remove_on_kick.priority = 'low'
remove_on_kick.thread = False
remove_on_kick.rate = 0

def remove_on_nickchg(jenni, input):
    unobot.remove_player(jenni, (input.nick).lower())
remove_on_nickchg.event = 'NICK'
remove_on_nickchg.rule = '.*'
remove_on_nickchg.priority = 'low'
remove_on_nickchg.thread = False
remove_on_nickchg.rate = 0

def unostats(jenni, input):
    unobot.unostat(jenni, input)
unostats.commands = ['unostats']
unostats.priority = 'low'
unostats.thread = False
unostats.rate = 0

def uno_help(jenni, input):
    nick = input.group(2)
    txt = 'For rules, examples, and getting started: https://is.gd/4YxydS'
    if nick:
        nick = (nick).strip()
        output = "%s: %s" % (nick, txt)
    else:
        output = txt
    jenni.say(output)
uno_help.commands = ['uno-help', 'unohelp']
uno_help.priority = 'low'
uno_help.thread = False
uno_help.rate = 0

def uno_pce_on(jenni, input):
    unobot.enablePCE(jenni, input.nick)
uno_pce_on.commands = ['pce-on']
uno_pce_on.priority = 'low'
uno_pce_on.thread = False
uno_pce_on.rate = 0

def uno_pce_off(jenni, input):
    unobot.disablePCE(jenni, input.nick)
uno_pce_off.commands = ['pce-off']
uno_pce_off.priority = 'low'
uno_pce_off.thread = False
uno_pce_off.rate = 0

def uno_ispce(jenni, input):
    unobot.isPCEEnabled(jenni, input.nick)
uno_ispce.commands = ['pce']
uno_ispce.priority = 'low'
uno_ispce.thread = False
uno_ispce.rate = 0

def uno_pce_clear(jenni, input):
    unobot.PCEClear(jenni, input.nick)
uno_pce_clear.commands = ['.pce-clear']
uno_pce_clear.priority = 'low'
uno_pce_clear.thread = False
uno_pce_clear.rate = 0

user_triggered = False

def uno_names(jenni, input, override=False):
    global away_last
    global user_triggered
    if input.sender != CHANNEL:
        return jenni.reply('Try: "/ctcp %s ping" or simply "%s!"' % (jenni.nick, jenni.nick))
    if time.time() - away_last < 480 and not override:
        jenni.notice(input.nick, 'This command is throttled due to abuse.')
        return
    away_last = time.time()

    if input.sender != CHANNEL:
        return
    jenni.write(['NAMES'], CHANNEL, raw=False)
    user_triggered = True
uno_names.commands = ['ping']

def uno_get_names(jenni, input):
    global user_triggered
    incoming = input.args
    if incoming and len(incoming) >= 2 and incoming[2] != CHANNEL:
        return
    txt = input.group()
    txt = txt.replace('+', '')
    txt = txt.replace('@', '')
    names = txt.split()
    new_list = list()
    away_list = load_away()
    for x in names:
        if x not in away_list:
            new_list.append(x)
    new_list.remove(jenni.config.nick)
    if 'ChanServ' in new_list:
        new_list.remove('ChanServ')
    if 'AntiSpamMeta' in new_list:
        new_list.remove('AntiSpamMeta')
    new_list.sort()
    final_string = ', '.join(new_list)
    if user_triggered:
        jenni.write(['PRIVMSG ' + CHANNEL], 'PING! ' + final_string,
                raw=True)
    user_triggered = False
uno_get_names.event = '353'
uno_get_names.rule = '.*'

def load_away():
    try:
        f = open('uno_away.txt', 'r')
        lines = f.readlines()
        f.close()
    except:
        f = open('uno_away.txt', 'w')
        f.write('ChanServ\n')
        f.close()
        lines = ['ChanServ']
    return [x.strip() for x in lines]

def save_away(jenni, aways):
    f = open('uno_away.txt', 'w')
    for nick in aways:
        f.write(nick)
        f.write('\n')
    f.close()

def uno_away(jenni, input):
    if input.sender != CHANNEL:
        return
    nickk = input.nick
    away_list = load_away()
    if nickk in away_list:
        away_list.remove(nickk)
        save_away(jenni, away_list)
        jenni.reply('You are now marked as available!')
    else:
        away_list.append(nickk)
        save_away(jenni, away_list)
        jenni.reply('You are now marked as away!')
    test_list = load_away()
uno_away.commands = ['away']
uno_away.rate = 0

def uno_ping_force(jenni, input):
    if input.admin:
        uno_names(jenni, input, True)
uno_ping_force.commands = ['fping']

if __name__ == '__main__':
    print __doc__.strip()
