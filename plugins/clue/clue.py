from __future__ import unicode_literals
# don't convert to ascii in py2.7 when creating string to return

crontable = []
outputs = []


def process_message(data):
    outputs.append([data['channel'], data['text']])
