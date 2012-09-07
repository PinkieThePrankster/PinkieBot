#!/usr/bin/env python
'''
img.py - PinkiePyBot character image storage module
(C) 2012 Jordan T Kinsley (jordantkinsley@gmail.com)
GPLv2 or later

This module will store an image for a roleplay character. 
By image I of course mean link, because screw DCC. 6_9
'''

import os, sqlite3, re

# The regular expression that matches any of http: , https: , ftp: , and ftps: 
# as well as .jpg, .png, .gif, and .jpeg. 
url_re = re.compile('(ht|f)tp(s)?://.*.(jpg|png|gif|jpeg)')

def t_connect(db):
	return sqlite3.connect(db, check_same_thread = False)

def setup(self):
    self.img_db = os.path.join(os.path.expanduser('~/.phenny'), 'img.db')
    self.img_conn = t_connect(self.img_db)

    c = self.img_conn.cursor()
    c.execute('''create table if not exists character_images(
		channel		varchar(255),
		nick		varchar(255),
		character	varchar(255),
		url			text,
		unique(character) on conflict replace
    );''')
    c.close()
    self.img_conn.commit()
setup.thread = False

def verify_url(url):
    m = url_re.match(url)
    if m:
        return True
    return False

def store(phenny, channel, nick, url, character=None):
    # If no character is supplied, the nick is the character. 
    # e.g. from #RPMeetup : Aurora, Hush, Necropony, Thorinair
    if not character:
        character = nick
    
    if not verify_url(url):
        raise GrumbleError("THAT'S NOT A FUCKING CORRECT URL!")
    
    sqlitedata = {
        'channel': channel,
        'nick': nick,
        'character': character,
        'url': url,
    }
    
    if not store.conn:
        store.conn = t_connect(phenny.img_db)
    
    c = store.conn.cursor()
    c.execute('''insert or replace into character_images
                (channel, nick, character, url) 
                    values(
                    :channel,
                    :nick,
                    :character,
                    :url);''', sqlitedata)
    c.close()
    store.conn.commit()
    return True
store.conn = None # these variables MUST be named with the function, other they won't register. :S
store.thread = False

def add(phenny, input):
    '''.add [<character>] <image url> - Adds an image URL for a given character. 
    The URL must end in a .jpg, .png, or .gif'''
    if not input.sender.startswith('#'): 
        phenny.reply('This is a channel-only command. Please try again in a channel.')
    channel = input.sender
    nick = input.nick
    # get the url from the input
    try: 
        character, url = input.group(2).split()
    except ValueError: 
        url = input.group(2)
        character = nick
    if not url:
        if not verify_url(character):
            phenny.say(add.__doc__.strip() + ' You may have entered an invalid URL.') 
            return
        else:
            url = character
            character = nick
    else:
        if not verify_url(url):
            phenny.say(add.__doc__.strip() + ' You may have entered an invalid URL.')
            return
        if store(phenny, channel, nick, url, character):
            phenny.say('Image for ' + character + ' at ' + url + ' added successfully.')
add.commands = ['add']
add.thread = False
add.priority = 'low'

def remove(phenny, channel, nick, character):
    sqlitedata = {
        'channel': channel,
        'nick': nick,
        'character': character,
    }
    if not remove.conn:
        remove.conn = t_connect(phenny.img_db)
    
    c = remove.conn.cursor()
    c.execute('''
        delete from character_images where character = :character 
            and nick = :nick 
            and channel = :channel;
    ''', sqlitedata)
    c.close()
    remove.conn.commit()
    return True
remove.conn = None
remove.thread = False

def verify_nick(phenny, channel, nick, character):
    sqlitedata = {
        'channel': channel,
        'nick': nick,
        'character': character,
    }
    
    verify = False
    
    if not verify_nick.conn:
        verify_nick.conn = t_connect(phenny.img_db)
    
    c = verify_nick.conn.cursor()
    c.execute('''
        select from character_images where channel = :channel 
            and nick = :nick and character = :character;
    ''', sqlitedata)
    # we should only fetch one record since the characters are unique. 
    # if no record was retrieved, we'll default to no verification, and 
    # the delete can't proceed.
    if c.fetchone():
        verify = True
    c.close()
    verify_nick.conn.close()
    return verify
verify_nick.conn = None
verify_nick.thread = False

def delete(phenny, input):
    '''.del <character> - Removes the character's image from the database. 
    You must be an admin or own the character to delete the image.'''
    channel = input.sender
    nick = input.nick
    character = input.group(2)
    # admins can delete any image they want
    if input.admin:
        if remove(phenny, channel, nick, character):
            phenny.say('!!ADMIN!! deleted the image for ' + character + ' owned by ' + nick + ' from the database.')
            return
        else: 
            phenny.say('Oh SHIT! Something went wrong!')
    else: 
        if not verify_nick(phenny, channel, nick, character):
            phenny.reply('You can\'t delete a row that doesn\'t belong to you. Please contact a channel admin for assistance.')
            return
        else:
            if remove(phenny, channel, nick, character):
                phenny.say('Successfully deleted the image for ' + character + ' owned by ' + nick + ' from the database.')
            else:
                phenny.say('Oh SHIT! Something went wrong!')
delete.commands = ['del','delete','remove']
delete.thread = False

def get(phenny, input):
    '''.get <character> - Retrieves the image URL for the given character.'''
    channel = input.sender
    character = input.group(2)
    
    sqlitedata = {
        'channel': channel,
        'character': character,
    }
    if not get.conn:
        get.conn = t_connect(phenny.img_db)
    
    c = get.conn.cursor()
    c.execute('''
        select url from character_images where channel = :channel 
            and character = :character;
    ''', sqlitedata) # we don't want to check the nick; 
    # if someone else looks up a character, no match will be found.
    url = c.fetchone()[0] # we just fetched a tuple with only one value
    if url:
        phenny.say('The image for ' + character + ' is ' + url)
        return
    else:
        phenny.say('No image found for ' + character + '. Someone might\'ve done fucked up.')
        return
    c.close()
get.conn = None
get.commands = ['get']
get.thread = False

def getall(phenny, input):
    '''admin only get command'''
    
    if not input.admin:
        phenny.msg(input.nick, getall.__doc__.strip())
    else: 
        if not getall.conn:
            getall.conn = t_connect(phenny.img_db)
    
    c = getall.conn.cursor()
    c.execute('''select channel, nick, character, url from character_images;''')
    # we need to process all of these results. 
    for x in range(0, c.rowcount):
        row = c.fetchone()
        phenny.msg(input.nick, 'from ' + row[0] + ' nick ' + row[1] + ' posted ' + row[2] + '\'s image at ' + row[3])
    c.close()
getall.conn = None
getall.commands = ['getall']
getall.thread = False
