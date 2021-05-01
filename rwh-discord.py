#!/usr/bin/python3

import discord
import re
import os
import time
from datetime import datetime, timedelta
from random import randint
import json
import logging as log

EMOTED = re.compile(r"^_(?:([^ ]+ly) )?(?:feed|send|da[mr]n|punt|tosse|smite|condemn|hurl|throw|kick|cast|banishe|drag|pull|consign|pushe|shove|drop|give)s (.*) (?:(?:in)?to|at) (?:heck|hell)([,\.]? +.*?)?[\.\?!]*_$", flags=re.I)
SAID = re.compile(r"^(?:feed|send|da[mr]n|punt|toss|smite|condemn|hurl|throw|kick|cast|banish|drag|pull|consign|push|shove|drop|give) (.*) (?:(?:in)?to|at) (?:heck|(?:rw)?hell)([,\.]? +.*?)?[\.\?!]*$", flags=re.I)
SIMPLE = re.compile(r"^to (?:heck|hell) with (.*?)[\.\?!]*$", flags=re.I)

BASEPATH = os.path.dirname(__file__)
# basic log config.
log.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s', 
    datefmt='%m/%d/%Y %I:%M:%S %p',
    filename='bot.log',
    level=log.INFO
    )

items = {}

async def feed_on(match, channel):
    """
        This method takes an item and the channel it was fed to hell in.
        It adds the item to the list for that channel along with the time it was
        fed into hell, and then emotes eating it to the channel.
    """
    global items
    chan_hash = str(hash(channel))

    item = {"name" : match, "time" : datetime.utcnow().isoformat() }
    if chan_hash in items:
        items[chan_hash].append(item)
    else:
        items[chan_hash] = [item]

    with open(os.path.join(BASEPATH, 'hell.json'), 'w') as cucumber:
        json.dump( items, cucumber )

    action = f"_sneaks out a scaly hand and grabs {match}!_"
    await channel.send(action)


def emoted(text):
    emote = EMOTED.match(text)
    if emote:
        item = ' '.join(filter(None, [emote.group(2), emote.group(3),  emote.group(1)]))
        return item
    return None  

def said(text):
    say = SAID.match(text)
    if say:
        item = ' '.join(filter(None, [say.group(1), say.group(2)]))
        return item
    return None  

def simple_said(text):
    say = SAID.match(text)
    if say:
        item = say.group(1)
        return item
    return None  

def remove_random(channel):
    global items
    chan_hash = str(hash(channel))
    if chan_hash in items and len(items[chan_hash]):
        channel_items = items[chan_hash]
        index = randint(0, len(channel_items) - 1)
        item = channel_items.pop(index)
        with open(os.path.join(BASEPATH,'hell.json'), 'w') as cucumber:
            json.dump( items, cucumber )
        return item['name'], item['time']
    else:
        return None, None

async def expel(channel,rerun=False):
    global items
    if channel in items:
        numitems = len(items[channel])
    else:
        numitems = 0
    if rerun:
        percent = 100
        rerunpercent = 0  # was 20, set to 0 to stop more than two expulsions at once
    else:
        # CHANGETHIS: This section controls how often the bot will spit something
        #             out, and how often it'll trigger more than once. The default
        #             numbers will make the bot eventually reach a stable
        #             equilibrium at roughly 60 items. percent = the percentage
        #             chance of spitting something out, rerunpercent = the
        #             percentage chance that it'll spit two things out.
        if numitems <= 5:
            percent = 12
            rerunpercent = 0
        elif numitems <= 10:
            percent = 25
            rerunpercent = 0
        elif numitems <= 15:
            percent = 40
            rerunpercent = 0
        elif numitems <= 20:
            percent = 65
            rerunpercent = 2
        elif numitems <= 30:
            percent = 80
            rerunpercent = 4
        elif numitems <= 45:
            percent = 82
            rerunpercent = 5
        elif numitems <= 60:
            percent = 85
            rerunpercent = 6
        else:
            percent = 95
            rerunpercent = 10

    chance = randint(1, 100)
    rerunchance = randint(1, 100)
    duration = "an unknown amount of time"
    if chance <= percent:
        random, time = remove_random(channel)
        if random:
            if time:
                now = datetime.utcnow()
                duration = time_pp(now - time.fromisoformat())
        if rerun:
            emit = "continue to"
        else:
            emit = "emit a sudden"

        action = f"_Hell's depths {emit} roar as it expels {random}. (stayed in Hell for {duration})_"
        await channel.send(action)
        if rerunchance <= rerunpercent:
            await expel(channel, rerun=True)


def time_pp(delta):
    days = delta.days
    hours = delta.seconds / 3600
    minutes = (delta.seconds % 3600 ) / 60
    seconds = (delta.seconds % 3600) % 60
    days_str = "{0:d} days".format(days) if days > 0 else None
    hours_str = "{0:d} hours".format(hours) if hours > 0 else None
    min_str = "{0:d} minutes".format(minutes) if minutes > 0 else None
    sec_str = "{0:d} seconds".format(seconds) if seconds > 0 else "less than a second."
    duration = ', '.join(filter(None, [days_str, hours_str, min_str, sec_str]))
    return duration


client = discord.Client()

@client.event
async def on_ready():
    global items
    try:
        with open(os.path.join(BASEPATH,'hell.json'), 'r') as cucumber:
            items = json.load(cucumber, parse_int=int)
        log.info("Successfully unpickled items.")
        log.warn(items)
    except Exception as e:
        log.warning("Something went wrong unpickling.")
        log.warning(e)
    log.info('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global items
    if message.author == client.user:
        return

    channel = message.channel
    chan_hash = str(hash(channel))
    content = message.content

    say = said(content)
    emote = emoted(content)
    simple = simple_said(content)
    action = [i for i in [say, emote, simple] if i]
    if len(action) > 0:
        item = action[0]
        nick = message.author.display_name
        my = nick + "'" if re.match(r"s$", nick, flags=re.I) else nick + "'s"
        item = re.sub(r"^(?:his|her|hir|their|my)", my, item, flags=re.I)
        item = re.sub(r"^(?:(?:him|her|hir|them)self|themselves)", nick, item, flags=re.I)
        await feed_on(item, channel)
        await expel(channel)
    if re.match(r"^hell.*tally[\?\.]?$", content, flags=re.I):
        if chan_hash in items:
            numitems = len(items[chan_hash])
        else:
            numitems = 0
        tally = f"I am lord over {numitems!s} damned souls."
        await channel.send(tally)


client.run('')
