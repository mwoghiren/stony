from __future__ import unicode_literals

# A list of outputs; append to this list to send a message.
outputs = []

# Lists of jewels and sand for the current game.
jewels = []
sand = []

# This function is called whenever a message is received.
def process_message(data):
  # Get the text.
  message_text = data['text']

  # This bot only cares about messages that start with "jits".
  if not message_text.startswith('jits'):
    return

  # Get the channel and make your presence known!
  channel = data['channel']
  outputs.append([channel, 'Jewels in the Sand is fun!'])
