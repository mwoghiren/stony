from __future__ import unicode_literals
import re

crontable = []
outputs = []

state = {}


class ClueState:

    def __init__(self):
        self.count = 0
        self.clue = ''

def process_message(data):

    channel = data['channel']
    if channel not in state.keys():
        state[channel] = ClueState()

    st = state[channel]

    # Count the number of messages we have seen in this channel since
    # stony last repeated a clue.
    st.count = st.count + 1

    if re.search("^\s*&gt;", data['text'], re.MULTILINE):
        st.clue = data['text']
        st.count = 1
    else:
        if st.count % 10 == 0:
            outputs.append([channel, st.clue])
