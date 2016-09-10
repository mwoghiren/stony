###
# Imports
###

from __future__ import unicode_literals
from slackclient import SlackClient

import yaml

###
# Classes
###

class Command:
    def __init__(self, name, function, num_args=0):
        self.name = name
        self.function = function
        self.num_args = num_args

class Player:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.im_id = get_im_id_for_user_id(self.id)
        self.current_word = None

class Game:
    def __init__(self, players):
        self.players = players
        self.current_round = 1
        self.words = {player.id: [] for player in players}

    def get_partner(self, player):
        if self.players[0].id == player.id:
            return self.players[1]
        return self.players[0]


###
# Global Variables
###

config = yaml.load(file('stony.conf', 'r'))
slack_client = SlackClient(config['SLACK_TOKEN'])

outputs = []

# A map from user id to Game.
user_id_to_game = {}

# A map from user id to Player.
user_id_to_player = {}


###
# Error Handling Functions
###

def handle_missing_params(channel, command):
    message = 'I need more parameters for the command *\'' + command + '\'*.'
    send_message(channel, message)

def handle_unknown_command(channel, command):
    message = 'I do not understand the command *\'' + command + '\'*.'
    send_message(channel, message)

def handle_invalid_username(channel, username):
    message = 'I can\'t find the user *\'' + username + '\'*.'
    send_message(channel, message)


###
# Bot Utility Functions
###

def send_message(channel, message):
    outputs.append([channel, '>>>' + message])

def get_im_id_for_user_id(user_id):
    api_call = slack_client.api_call('im.open', user=user_id)
    if api_call.get('ok'):
        return api_call.get('channel').get('id')
    return None

def get_id_for_username(username):
    api_call = slack_client.api_call('users.list')
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == username:
                return user.get('id')
    return None

def get_username_for_id(user_id):
    api_call = slack_client.api_call('users.info', user=user_id)
    if api_call.get('ok'):
        return api_call.get('user').get('name')
    return None


###
# Bot Helper Functions
###

def get_player_for_user_id(user_id):
    player = user_id_to_player.get(user_id)
    if player is None:
        username = get_username_for_id(user_id)
        player = Player(user_id, username)
        user_id_to_player[user_id] = player
    return player


###
# Game Functions
###

def start_game(channel, player, new_partner_name):
    if player.name == new_partner_name:
        message = 'Sorry!  This game can\'t be played solo.'
        send_message(channel, message)
        return

    existing_game = user_id_to_game.get(player.id)
    if existing_game != None:
        existing_partner = existing_game.get_partner(player)
        message = 'You\'re already in a game with *' + existing_partner.name + '*.'
        send_message(channel, message)
        return

    new_partner_id = get_id_for_username(new_partner_name)
    new_partner_existing_game = user_id_to_game.get(new_partner_id)
    if new_partner_existing_game != None:
        message = 'Oops!  ' + new_partner_name + ' is already in a game.'
        send_message(channel, message)
        return

    new_partner = get_player_for_user_id(new_partner_id)
    new_game = Game([player, new_partner])
    user_id_to_game[player.id] = new_game
    message = 'You\'re now in a game of _One, Two, Three_ with *' + new_partner_name + '*.\n'
    message += 'Please enter a starting word using `123 word [your_word]`.'
    send_message(channel, message)

    user_id_to_game[new_partner.id] = new_game
    message = 'You\'re now in a game of _One, Two, Three_ with *' + player.name + '*.\n'
    message += 'Please enter a starting word using `123 word [your_word]`.'
    send_message(new_partner.im_id, message)

def register_word(channel, player, word):
    existing_game = user_id_to_game.get(player.id)
    if existing_game == None:
        message = 'You\'re not currently in a game of _One, Two, Three_.'
        send_message(channel, message)
        return

    if player.current_word != None:
        message = 'You\'ve already registered the word *\'' + player.current_word + '\'*.'
        send_message(channel, message)
        return

    player.current_word = word.lower()
    existing_game.words[player.id].append(word)
    message = 'Your word, *\'' + player.current_word + '\'*, is now registered.  Please wait for ' + existing_game.get_partner(player).name + '.'
    send_message(channel, message)

    for existing_player in existing_game.players:
        if existing_player.current_word == None:
            return

    start_next_round(channel, existing_game)

def start_next_round(channel, game):
    if game.players[0].current_word == game.players[1].current_word:
        for player in game.players:
            partner = game.get_partner(player)
            message = 'Congratulations!  You and ' + partner.name + ' both guessed *\'' + player.current_word + '\'* after ' + str(game.current_round) + ' round' + ('' if game.current_round == 1 else 's') + '.  Nicely done!'
            send_message(player.im_id, message)
            user_id_to_game[player.id] = None
        return

    game.current_round += 1
    for player in game.players:
        partner = game.get_partner(player)
        message = 'The words are in: ' + partner.name + ' guessed *\'' + partner.current_word + '\'*.\n'
        message += 'Please enter a new word for pair *[' + player.current_word + ', ' + partner.current_word + ']* using `123 word [your_word]`.'
        send_message(player.im_id, message)

    for player in game.players:
        player.current_word = None

def quit_game(channel, player):
    existing_game = user_id_to_game.get(player.id)
    if existing_game == None:
        message = 'You\'re not currently in a game of _One, Two, Three_.'
        send_message(channel, message)
        return

    for existing_player in existing_game.players:
        user_id_to_game[existing_player.id] = None
        message = ('You have ' if player.id == existing_player.id else player.name + ' has ') + 'quit the game.'
        send_message(existing_player.im_id, message)

###
# Available Commands
###

AVAILABLE_COMMANDS = [
  Command('play', start_game, num_args=1),
  Command('word', register_word, num_args=1),
  Command('quit', quit_game, num_args=0),
]


###
# Bot Main Functions
###

def process_message(data):
    message_text = data['text']

    # We only care about messages starting with '123'.
    if not message_text.startswith('123'):
        return

    # Get the sender's Player object, creating it if necessary.
    message_sender_id = data['user']
    player = get_player_for_user_id(message_sender_id)

    # Ensure this is the player's IM channel.
    channel = data['channel']
    if channel != player.im_id:
        return

    # Retrieve the command.
    message_tokens = message_text.split()
    command = message_tokens[1]
    args = message_tokens[2:]

    cmd = None
    for c in AVAILABLE_COMMANDS:
        if c.name == command:
            cmd = c

    if not cmd:
        handle_unknown_command(channel, command)
        return

    # Ensure we received the required number of arguments.
    if len(args) != cmd.num_args:
        handle_missing_params(channel, command)
        return

    # Execute the command!
    if cmd.num_args == 0:
        cmd.function(channel, player)
    else:
        cmd.function(channel, player, *args)
