import os
import ConfigParser
import email_notification
import logging


def write_file(cfile, stuff):
    with open(cfile, 'wb') as configfile:
        stuff.write(configfile)


if __name__ == '__main__':
    logging.basicConfig(filename='/var/log/ping_server.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
    state_file = 'stateful.ini'
    state = ConfigParser.RawConfigParser()
    state.read(state_file)

    config_file = 'config.ini'
    config = ConfigParser.RawConfigParser()
    config.read(config_file)

    hostname = config.get('General', 'ip')
    response = os.system("ping -c 1 {}".format(hostname))

    failed = int(state.get('ping', 'failed'))
    notified = int(state.get('ping', 'notified'))

    # and then check the response...
    if response == 0:
        if failed != 0:
            failed = 0
            state.set('ping', 'failed', failed)
            write_file(state_file, state)
        if notified != 0:
            notified = 0
            state.set('ping', 'notified', notified)
            write_file(state_file, state)
            # Send success email
            subject = "Anthony-Server7 Responding - SUCCESS"
            body = "Anthony-Server7 has started responding to Ping requests."
            email_notification.send_notification(subject, body)

    else:
        failed += 1
        state.set('ping', 'failed', failed)
        logging.warning('FAILED Count: {}'.format(failed))

        if failed >= 5:
            if notified == 0:
                notified += 1
                state.set('ping', 'notified', notified)

                # Send email
                subject = "Anthony-Server7 NOT Responding - FAILURE"
                body = "Anthony-Server7 is not responding to ping requests.\n" \
                       "Please have a Look!"
                email_notification.send_notification(subject, body)

        write_file(state_file, state)
