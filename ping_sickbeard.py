import logging
from urllib2 import urlopen, URLError, HTTPError
import json
import socket
import ConfigParser
import email_notification


def call_sb(sb_api_key, sb_ip, sb_port, sb_api):
    try:
        socket.setdefaulttimeout(5)
        response = urlopen('http://{}:{}/api/{}/{}'.format(sb_ip, sb_port, sb_api_key, sb_api))
        return response, True

    except HTTPError, e:
        return e.code, False

    except URLError, e:
        return e.reason, False


def write_file(cfile, stuff):
    with open(cfile, 'wb') as configfile:
        stuff.write(configfile)


def failure(failed, notified):
    failed += 1
    state.set('sb', 'failed', failed)
    logging.warning('FAILED Count: {}'.format(failed))
    if failed >= 5:
        print 'Sickbeard is DOWN'
        if notified == 0:
            subject = 'SickBeard is DOWN -- FAILURE'
            body = 'SickBeard is not responding to API ping requests.\n' \
                   'Please have a look.'
            email_notification.send_notification(subject, body)
            notified += 1
            state.set('sb', 'notified', notified)
    write_file(state_file, state)
    return failed, notified


if __name__ == '__main__':
    logging.basicConfig(filename='/var/log/ping_sickbeard.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
    state_file = 'stateful.ini'
    config_file = 'config.ini'
    # Read in the config.
    config = ConfigParser.RawConfigParser()
    config.read(config_file)

    # Read in state.
    state = ConfigParser.RawConfigParser()
    state.read(state_file)

    sb_api_key = config.get('SBInfo', 'sb_api_key')
    sb_ip = config.get('SBInfo', 'sb_ip')
    sb_port = config.get('SBInfo', 'sb_port')
    sb_api = config.get('SBInfo', 'sb_api')

    up = bool
    failed = int(state.get('sb', 'failed'))
    notified = int(state.get('sb', 'notified'))

    response, up = call_sb(sb_api_key, sb_ip, sb_port, sb_api)

    if up is True:
        response2 = json.load(response)
        test = response2['result']

        if test == 'success':
            print 'Sickbeard is up'
            if failed != 0:
                failed = 0
                state.set('sb', 'failed', failed)
                write_file(state_file, state)
                logging.warning('FAILED Count Reset to: {}'.format(failed))
            if notified != 0:
                notified = 0
                state.set('sb', 'notified', notified)
                write_file(state_file, state)
                subject = 'SickBeard is up -- SUCCESS'
                body = 'SickBeard has started responding to ping requests.\n' \
                       'All is good!'
                email_notification.send_notification(subject, body)
                logging.warning('NOTIFIED Count Reset to: {}'.format(notified))

        else:
            failed, notified = failure(failed, notified)

    else:
        failed, notified = failure(failed, notified)
