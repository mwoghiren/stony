###
# Imports
###

from __future__ import unicode_literals
from slackclient import SlackClient

import yaml

###
# Global Variables
###

# The Slack API client.
config = yaml.load(file('stony.conf', 'r'))
slack_client = SlackClient(config['SLACK_TOKEN'])

# A list of outputs; append to this list to send a message.
outputs = []

# A map of stored inputs.
inputs = {}

###
# Constants
###

REVEAL_COMMAND = 'REVEAL'
INPUT_COMMAND = 'in'

###
# Bot Utility Functions
###

def send_message(message, channel):
    outputs.append([channel, '>>>' + message])

def get_im_id_for_user_id(user_id):
    api_call = slack_client.api_call('im.open', user=user_id)
    if api_call.get('ok'):
        return api_call.get('channel').get('id')
    return ''

def get_username_for_user_id(user_id):
    api_call = slack_client.api_call('users.info', user=user_id)
    if api_call.get('ok'):
        return api_call.get('user').get('name')
    return ''

###
# Game Functions
###

def reveal_inputs(channel):
    global inputs
    if len(inputs) == 0:
        send_message('Nothing to reveal!', channel)
        return

    message = ''
    for user_id, input in inputs.iteritems():
        message += '*' + user_id + '*: ' + input + '\n'
    send_message(message, channel)
    inputs = {}

###
# Bot Main Functions
###

# This function is called whenever a message is received.
def process_message(data):
    global inputs

    # Get the text and the channel.
    message_text = data['text']
    channel = data['channel']

    # If it's a REVEAL message, spill the beans.
    if message_text == REVEAL_COMMAND:
        reveal_inputs(channel)
        return

    # Aside from REVEALs, this bot only accepts PMs.
    message_sender_id = data['user']
    message_sender_im_id = get_im_id_for_user_id(message_sender_id)
    if channel != message_sender_im_id:
        return

    # In PMs, this bot only cares about inputs.
    if not message_text.lower().startswith(INPUT_COMMAND + ' '):
        return

    # Chop off the input command token.
    message_text = message_text.split(' ', 1)[1];

    # Store the pairing in the map.
    username = get_username_for_user_id(message_sender_id)
    inputs[username] = message_text
    send_message('Got it!', channel)
