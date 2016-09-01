###
# Imports
###

from __future__ import unicode_literals
from slackclient import SlackClient

import yaml

###
# Constants
###

COMMAND_LIST = 'list'
COMMAND_ADD_JEWEL = 'jewel'
COMMAND_ADD_SAND = 'sand'
COMMAND_RESTART_GAME = 'restart'
COMMAND_SULTAN = 'sultan'
COMMAND_SULTANESS = 'sultaness'

AVAILABLE_COMMANDS = [COMMAND_LIST, COMMAND_ADD_JEWEL, COMMAND_ADD_SAND, COMMAND_RESTART_GAME, COMMAND_SULTAN, COMMAND_SULTANESS]

###
# Global Variables
###

# The Slack API client.
config = yaml.load(file('stony-dev-hale.conf', 'r'))
slack_client = SlackClient(config['SLACK_TOKEN'])

# A list of outputs; append to this list to send a message.
outputs = []

# Lists of jewels and sand for the current game.
jewel_list = []
sand_list = []

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
  outputs.append([channel, message])

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
  message = '>>>'
  message += '*Jewels:* '
  message += ', '.join(jewel_list)
  message += '\n'
  message += '*Sand:* '
  message += ', '.join(sand_list)

  # Send the message!
  send_message(channel, message)

def add_jewel(jewel, channel):
  # Check whether the jewel already exists as sand.
  if jewel in sand_list:
    # The word already exists as sand.
    message = '*\'' + jewel + '\'* is already sand!'
    send_message(channel, message);
    return

  # Add the given jewel to the list of jewels.
  if jewel not in jewel_list:
    jewel_list.append(jewel)

  # Let everyone know.
  message = '*\'' + jewel + '\'* is a jewel.'
  send_message(channel, message)

  # Show the list of jewels and sand.
  list_jewels_and_sand(channel)

def add_sand(sand, channel):
  # Check whether the sand already exists as a jewel.
  if sand in jewel_list:
    # The word already exists as a jewel.
    message = '*\'' + sand + '\'* is already a jewel!'
    send_message(channel, message);
    return

  # Add the given sand to the list of sand.
  if sand not in sand_list:
    sand_list.append(sand)

  # Let everyone know.
  message = '*\'' + sand + '\'* is sand.'
  send_message(channel, message)

  # Show the list of jewels and sand.
  list_jewels_and_sand(channel)

def restart_game(channel):
  # Specify the global jewel and sand lists.
  global jewel_list
  global sand_list

  # Clear the jewel and sand lists.
  jewel_list = []
  sand_list = []

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
  elif command == COMMAND_RESTART_GAME:
    restart_game(channel)
