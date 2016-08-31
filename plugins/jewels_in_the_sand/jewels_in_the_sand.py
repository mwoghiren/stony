###
# Imports
###

from __future__ import unicode_literals


###
# Global Variables
###

# A list of outputs; append to this list to send a message.
outputs = []

# Lists of jewels and sand for the current game.
jewel_list = []
sand_list = []


###
# Bot Utility Functions
###

def send_message(channel, message):
  outputs.append([channel, message])


###
# Game Functions
###

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
  # Add the given jewel to the list of jewels.
  jewel_list.append(jewel)

  # Let everyone know.
  message = '*\'' + jewel + '\'* is a jewel.'
  send_message(channel, message)

def add_sand(sand, channel):
  # Add the given sand to the list of sand.
  sand_list.append(sand)

  # Let everyone know.
  message = '*\'' + sand + '\'* is sand.'
  send_message(channel, message)

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


###
# Bot Main Functions
###

# This function is called whenever a message is received.
def process_message(data):
  # Get the text.
  message_text = data['text']

  # This bot only cares about messages that start with "jits".
  if not message_text.startswith('jits'):
    return

  # Retrieve the channel.
  channel = data['channel']

  # Retrieve the command.
  message_tokens = message_text.split()
  command = message_tokens[1]

  # Execute the command!
  if command == 'list':
    list_jewels_and_sand(channel)
  elif command == 'jewel':
    if len(message_tokens) < 3:
      handle_missing_params(command, channel)
    else:
      jewel = " ".join(message_tokens[2:])
      add_jewel(jewel, channel)
  elif command == 'sand':
    if len(message_tokens) < 3:
      handle_missing_params(command, channel)
    else:
      sand = " ".join(message_tokens[2:])
      add_sand(sand, channel)
  elif command == 'restart':
    restart_game(channel)
  else:
    # We don't understand the command, so we say so.
    handle_unknown_command(command, channel)
