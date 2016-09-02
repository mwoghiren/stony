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

COMMAND_ADD_GUESS = 'guess'
COMMAND_ADD_JEWEL = 'jewel'
COMMAND_ADD_SAND = 'sand'
COMMAND_HELP = 'help'
COMMAND_LIST = 'list'
COMMAND_REMOVE_JEWEL = 'unjewel'
COMMAND_REMOVE_SAND = 'unsand'
COMMAND_RESTART_GAME = 'restart'
COMMAND_SULTAN = 'sultan'
COMMAND_SULTANESS = 'sultaness'

AVAILABLE_COMMANDS = [COMMAND_ADD_GUESS, COMMAND_ADD_JEWEL, COMMAND_ADD_SAND, COMMAND_HELP, COMMAND_LIST, COMMAND_REMOVE_JEWEL, COMMAND_REMOVE_SAND, COMMAND_RESTART_GAME, COMMAND_SULTAN, COMMAND_SULTANESS]

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
  message += '`jits [sultan|sultaness] [username]` will specify a new Sultan or Sultaness.\n'
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
    handle_invalid_username(new_sultan_name, channel)
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

def add_word(word, type, channel):
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

def add_jewel(jewel, channel):
  add_word(jewel, TYPE_JEWEL, channel)

def add_sand(sand, channel):
  add_word(sand, TYPE_SAND, channel)

def remove_word(word, type, channel):
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

def remove_jewel(jewel, channel):
  remove_word(jewel, TYPE_JEWEL, channel)

def remove_sand(sand, channel):
  remove_word(sand, TYPE_SAND, channel)

def register_guess(guess, channel):
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

def handle_missing_params(command, channel):
  message = 'I need more parameters for the command *\'' + command + '\'*.'
  send_message(channel, message)

def handle_unknown_command(command, channel):
  message = 'I do not understand the command *\'' + command + '\'*.'
  send_message(channel, message)

def handle_invalid_username(username, channel):
  message = 'I can\'t find the user *\'' + username + '\'*.'
  send_message(channel, message)

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

  # Retrieve the command.
  message_tokens = message_text.split()
  command = message_tokens[1]

  # Check whether we understand the command.
  if command not in AVAILABLE_COMMANDS:
    # We don't understand the command, so we say so.
    handle_unknown_command(command, channel)
    return

  # Execute the command!
  # First, we check for commands that can be run by anyone.
  if command == COMMAND_LIST:
    list_jewels_and_sand(channel)
  elif command == COMMAND_SULTAN:
    if len(message_tokens) < 3:
      get_sultan(channel)
    else:
      new_sultan = message_tokens[2]
      set_sultan(channel, new_sultan, False)
  elif command == COMMAND_SULTANESS:
    if len(message_tokens) < 3:
      get_sultan(channel)
    else:
      new_sultan = message_tokens[2]
      set_sultan(channel, new_sultan, True)
  elif command == COMMAND_ADD_GUESS:
    if len(message_tokens) < 3:
      handle_missing_params(command, channel)
    else:
      guess = " ".join(message_tokens[2:])
      register_guess(guess, channel)
  elif command == COMMAND_HELP:
    print_help(channel)

  # Now, we return if the person who sent the message is not the Sultan.
  message_sender_id = data['user']
  if message_sender_id != current_sultan_id:
    return

  # The Sultan has issued a command!  Execute it, if possible.
  if command == COMMAND_ADD_JEWEL:
    if len(message_tokens) < 3:
      handle_missing_params(command, channel)
    else:
      jewel = " ".join(message_tokens[2:])
      add_jewel(jewel, channel)
  elif command == COMMAND_ADD_SAND:
    if len(message_tokens) < 3:
      handle_missing_params(command, channel)
    else:
      sand = " ".join(message_tokens[2:])
      add_sand(sand, channel)
  elif command == COMMAND_REMOVE_JEWEL:
    if len(message_tokens) < 3:
      handle_missing_params(command, channel)
    else:
      jewel = " ".join(message_tokens[2:])
      remove_jewel(jewel, channel)
  elif command == COMMAND_REMOVE_SAND:
    if len(message_tokens) < 3:
      handle_missing_params(command, channel)
    else:
      sand = " ".join(message_tokens[2:])
      remove_sand(sand, channel)
  elif command == COMMAND_RESTART_GAME:
    restart_game(channel)
