#!/usr/bin/env python
'''
access to urbandictionary.com lookups
'''

# Example JSON query.
# http://api.urbandictionary.com/v0/define?term=<query>[&page=2]


import urbandict

def ud(bot, input):
    '''.ud <term>'''
    term = input.group()[len(".ud"):].strip()

    if not term:
        bot.reply('Look up a term on urbandictionary.com: ' + ud.__doc__)
        return

    chunks = term.split()
    index = 1
    try:
        index = int(chunks[0])
        term = ' '.join(chunks[1:])
    except ValueError:
        pass


    defs = urbandict.define(term)
    ndefs = len(defs)

    if not ndefs:
        bot.reply('No hip definition for "%s"' % term)
        return

    index = 1
    for the_def in defs:
        example = the_def['example']
        if example: example = '"%s"' % example
        bot.say('[%d/%d] "%s": %s %s' % ( index, len(defs), term, the_def['def'], example))
        index += 1

ud.commands = ['ud']
ud.rate = 2


