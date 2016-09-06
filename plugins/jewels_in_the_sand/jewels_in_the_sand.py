###
# Imports
###

from __future__ import unicode_literals
from slackclient import SlackClient

import yaml

###
# Constants
###

TYPE_JEWEL = 'jewel'
TYPE_SAND = 'sand'

###
# Global Variables
###

# The Slack API client.
config = yaml.load(file('stony.conf', 'r'))
slack_client = SlackClient(config['SLACK_TOKEN'])

# A list of outputs; append to this list to send a message.
outputs = []

# Lists of jewels and sand for the current game.
jewel_list = []
sand_list = []

# A list of outstanding guesses.
guess_list = []

# The id and username of the current Sultan.
# Some commands can only be run by the Sultan.
# TODO: Bundle this into an object.
current_sultan_id = ''
current_sultan_name = ''
current_is_sultaness = False

###
# Bot Utility Functions
###

def send_message(channel, message):
    outputs.append([channel, '>>>' + message])

def get_id_for_username(username):
    api_call = slack_client.api_call('users.list')
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == username:
                return user.get('id')
    return ''


###
# Game Functions
###

def print_help(channel):
    message = '`jits` is the command for Jewels in the Sand.  Run `jits [command]` to do things.\n\n'
    message += '*General Commands*\n\n'
    message += '`jits [sultan|sultaness]` will list the current Sultan or Sultaness.\n'
    message += '`jits [sultan|sultaness] [username]` will specify a new Sultan or Sultaness.\n'
    message += '`jits guess [word]` will add the given word to the guess list.\n'
    message += '`jits list` will list the current jewels and sand.\n'
    message += '`jits restart` will restart the game.\n'
    message += '`jits help` will bring up this message.\n\n'
    message += '*Sultan Commands*\n\n'
    message += '`jits [jewel|sand] [word]` will add the given word to the appropriate list.\n'
    message += '`jits [unjewel|unsand] [word]` will remove the given word from the appropriate list.\n'
    send_message(channel, message)

def set_sultan(channel, new_sultan_name, is_sultaness):
    # Specify the global Sultan variables.
    global current_sultan_id
    global current_sultan_name
    global current_is_sultaness

    # Get the new Sultan id.
    new_sultan_id = get_id_for_username(new_sultan_name)

    # Handle the case where the proposed Sultan can't be found.
    if new_sultan_id == '':
        handle_invalid_username(channel, new_sultan_name)
        return

    # Set the new Sultan.
    current_sultan_id = new_sultan_id
    current_sultan_name = new_sultan_name
    current_is_sultaness = is_sultaness

    # Let everyone know.
    message = 'All hail *' + new_sultan_name + '*, the new Sultan'
    if is_sultaness:
        message += 'ess'
    message += '!'
    send_message(channel, message)

def get_sultan(channel):
    if current_sultan_name == '':
        message = 'There is currently no Sultan or Sultaness.'
    else:
        message = 'The current Sultan'
        if current_is_sultaness:
            message += 'ess'
        message += ' is ' + current_sultan_name + '.  Long may '
        if current_is_sultaness:
            message += 's'
        message += 'he live!'
    send_message(channel, message)

def list_jewels_and_sand(channel):
    # Create the message using the jewels and sand.
    message = '*Jewels:* '
    message += ', '.join(jewel_list)
    message += '\n'
    message += '*Sand:* '
    message += ', '.join(sand_list)
    if len(guess_list) > 0:
        message += '\n'
        message += '*Outstanding Guesses:* '
        message += ', '.join(guess_list)

    # Send the message!
    send_message(channel, message)

def add_word(channel, word, type):
    # Grab the appropriate list.
    if type == TYPE_JEWEL:
        list = jewel_list
        other_list = sand_list
    elif type == TYPE_SAND:
        list = sand_list
        other_list = jewel_list
    else:
        return

    # Check whether the word already exists in the other list.
    if word in other_list:
        # The word already exists in the other list.
        message = '*\'' + word + '\'* is already '
        if type == TYPE_SAND:
            message += 'a ' + TYPE_JEWEL
        elif type == TYPE_JEWEL:
            message += TYPE_SAND
        else:
            return
        message += '!'
        send_message(channel, message);
        return

    # Add the given word to the given list.
    if word not in list:
        list.append(word)

    # Remove the word form the guess list, if it's there.
    guess_list.remove(word)

    # Let everyone know.
    message = '*\'' + word + '\'* is '
    if type == TYPE_JEWEL:
        message += 'a '
    message += type + '.'
    send_message(channel, message)

    # Show the list of jewels and sand.
    list_jewels_and_sand(channel)

def add_jewel(channel, jewel):
    add_word(channel, jewel, TYPE_JEWEL)

def add_sand(channel, sand):
    add_word(channel, sand, TYPE_SAND)

def remove_word(channel, word, type):
    # Grab the appropriate list.
    if type == TYPE_JEWEL:
        list = jewel_list
    elif type == TYPE_SAND:
        list = sand_list
    else:
        return

    # Ensure the word is in the list.
    if word not in list:
        message = '*\'' + word + '\'* is not specified as '
        if type == TYPE_JEWEL:
            message += 'a '
        message += type + '.'
        send_message(channel, message)
        return

    list.remove(word)
    message = '*\'' + word + '\'* removed from the list of ' + type
    if type == TYPE_JEWEL:
        message += 's'
    message += '.'
    send_message(channel, message)

    # Show the list of jewels and sand.
    list_jewels_and_sand(channel)

def remove_jewel(channel, jewel):
    remove_word(channel, jewel, TYPE_JEWEL)

def remove_sand(channel, sand):
    remove_word(channel, sand, TYPE_SAND)

def register_guess(channel, guess):
    # Check if the guess already exists in the jewel, sand, or guess lists.
    message = ''
    if guess in jewel_list:
        message = '*\'' + guess + '\'* is a jewel.'
    elif guess in sand_list:
        message = '*\'' + guess + '\'* is sand.'
    elif guess in guess_list:
        message = '*\'' + guess + '\'* is already a pending guess.'

    if message != '':
        send_message(channel, message)
        return

    # We have a new guess!  Add it to the list.
    guess_list.append(guess)

    # Let everyone know.
    message = 'The guess *\'' + guess + '\'* is now registered.\n'
    message += '*Outstanding Guesses:* ' + ', '.join(guess_list)
    send_message(channel, message)

def restart_game(channel):
    # Specify the global jewel and sand lists.
    global jewel_list
    global sand_list
    global guess_list

    # Clear the jewel, sand, and guess lists.
    jewel_list = []
    sand_list = []
    guess_list = []

    # Let everyone know.
    message = 'The game has been restarted.'
    send_message(channel, message)


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
# Available commands for this bot
###

class Command:

    def __init__(self, name, function, num_args=0,
                 collapse_args=False,requires_sultan=False,
                 extra_args={}):
        self.name = name
        self.function = function
        self.num_args = num_args
        self.collapse_args = collapse_args
        self.requires_sultan = requires_sultan
        self.extra_args = extra_args

AVAILABLE_COMMANDS = [
  Command('help', print_help),
  Command('list', list_jewels_and_sand),
  Command('guess', register_guess,
          num_args=1, collapse_args=True),
  Command('jewel', add_jewel,
          num_args=1, collapse_args=True, requires_sultan=True),
  Command('sand', add_sand,
          num_args=1, collapse_args=True, requires_sultan=True),
  Command('unjewel', remove_jewel,
          num_args=1, collapse_args=True, requires_sultan=True),
  Command('unsand', remove_sand,
          num_args=1, collapse_args=True, requires_sultan=True),
  Command('restart', restart_game,
          requires_sultan=True),
  Command('sultan', get_sultan, num_args=0),
  Command('sultan', set_sultan, num_args=1,
          extra_args={"is_sultaness": False}),
  Command('sultaness', get_sultan, num_args=0),
  Command('sultaness', set_sultan, num_args=1,
          extra_args={"is_sultaness": True}),
]

###
# Bot Main Functions
###

# This function is called whenever a message is received.
def process_message(data):
    # Get the text.
    message_text = data['text']

    # This bot only cares about messages that start with "jits".
    if not message_text.lower().startswith('jits'):
        return

    # Retrieve the channel.
    channel = data['channel']

    # Retrieve the sender
    message_sender_id = data['user']

    # Retrieve the command.
    message_tokens = message_text.split()
    command = message_tokens[1]
    args = message_tokens[2:]

    # Find the command
    cmd = None
    for c in AVAILABLE_COMMANDS:
        if c.name == command:
            # Some commands appear in the list twice with different numbers
            # of arguments. A command with a matching number of arguments takes
            # precendence over a command with a mis-match.
            if not cmd or len(args) == c.num_args:
                cmd = c

    # Report for unknown commands
    if not cmd:
        handle_unknown_command(channel, command)
        return

    # Collapse arguments if the command needs that
    if cmd.collapse_args:
        args = [" ".join(args)]

    # Ensure we received the required number of arguments
    if len(args) != cmd.num_args:
        handle_missing_params(channel, command)

    # Do nothing if a non-Sultan attempt a Sultan-only command
    if cmd.requires_sultan and message_sender_id != current_sultan_id:
        send_message(channel, "Sorry {} is not the sultan ({})".format(message_sender_id, current_sultan_in))
        return

    # Execute the command!
    if cmd.num_args == 0:
        cmd.function(channel)
    else:
        cmd.function(channel, *args, **cmd.extra_args)
