#!/usr/bin/python

import requests
import ConfigParser
import email_notification
import logging
import json
import sqlite3
import os


def failed(check, state, occurrences, notified):
    # So something failed, that is why you ended up here.
    occurrences += 1
    if state:
        # check the current known state in the DB
        state = False
        c.execute('''UPDATE monitor SET state=?, occurrences=? WHERE name=?''', (state, occurrences, check))
        conn.commit()
    elif not notified:
        if occurrences >= int(config.get('Plex_Info', 'f_occurrences')):
            email_notification.send_notification("Plex DOWN", "The Plex Server appears to be DOWN")
            c.execute('''UPDATE monitor SET occurrences=?, notified=? WHERE name=?''', (occurrences, True, check))
            conn.commit()
        else:
            c.execute('''UPDATE monitor SET occurrences=? WHERE name=?''', (occurrences, check))
            conn.commit()
    else:
        c.execute('''UPDATE monitor SET occurrences=? WHERE name=?''', (occurrences, check))
        conn.commit()

    clean_up()


def success(check, state, occurrences, notified):
    if data['MediaContainer']['Server'][0]['name'] == "Anthony's Plex":
    # will check the DB for the state, if it's bad, will update to good.
        if not state:
            email_notification.send_notification("Plex UP", "The Plex Server is back UP")
            state_data = (check, True, 0, False)
            c.execute('''UPDATE monitor SET state=?, occurrences=?, notified=? WHERE name=?''', (True, 0, False, check))
            conn.commit()

    else:
        failed(check, state, occurrences, notified)

def clean_up():
    conn.close()
    exit(0)


def create_db():
    print('Running first time setup')
    db_path = config.get('database', 'path')
    with open(db_path, 'ab'):
        pass

    # Connect to the database
    db_conn = sqlite3.connect(db_path)
    db_c = db_conn.cursor()

    # Create the table
    db_c.execute('''CREATE TABLE monitor (name, state, occurrences, notified)''')
    db_conn.commit()
    db_conn.close()


def start_up():
    if not os.path.exists(config.get('database', 'path')):
        create_db()


if __name__ == '__main__':
    logging.basicConfig(filename='./ping_plex.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

    config_file = 'config.ini'
    config = ConfigParser.RawConfigParser()
    config.read(config_file)

    start_up()

    # Read in config
    hostname = config.get('Plex_Info', 'ip')
    port = config.get('Plex_Info', 'port')
    uri = config.get('Plex_Info', 'uri')
    token = config.get('Plex_Info', 'token')
    check = config.get('Plex_Info', 'check_name')

    # Connect to DB
    db_path = config.get('database', 'path')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get current state of the check
    c.execute('''SELECT * FROM monitor WHERE name = ?''', (check,))
    db_check = c.fetchone()
    print db_check

    if not db_check:
        # if the check doesn't exist, make it.
        insert_data = (check, True, 0, False)
        c.execute('''INSERT INTO monitor (name, state, occurrences, notified) VALUES (?,?,?,?)''', insert_data)
        conn.commit()

        # Get it again for use now
        c.execute('''SELECT * FROM monitor WHERE name = ?''', (check,))
        db_check = c.fetchone()

    # put DB data into something easy to use
    occurrences = db_check[2]
    notified = bool(db_check[3])
    state = bool(db_check[1])

    url = 'http://{}:{}/{}'.format(hostname, port, uri)
    session = requests.Session()
    session.headers.update({'X-Plex-Token': token})
    session.headers.update({'Accept': 'application/json'})

    r = session.get(url)

    try:
        data = json.loads(r.content)
    except ValueError:
        failed(check, state, occurrences, notified)

    if r.status_code == 200:
        print('GOT 200')
        # If the responce is good, check the data.
        success(check, state, occurrences, notified)

    else:
        # if we don't get the expected data. Will start the fail process.
        failed(check, state, occurrences, notified)

