from __future__ import unicode_literals
# don't convert to ascii in py2.7 when creating string to return

crontable = []
outputs = []

state = {}


def process_message(data):

    channel = data['channel']
    if channel not in state.keys():
        state[channel] = {'count': 0, 'clue': ''}

    st = state[channel]

    # Count the number of messages we have seen in this channel since
    # stony last repeated a clue.
    st['count'] = st['count'] + 1

    if data['text'].startswith('&gt;'):
        st['clue'] = data['text']
        st['count'] = 1
    else:
        if st['count'] % 10 == 0:
            outputs.append([channel, st['clue']])
