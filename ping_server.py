import os
import ConfigParser
import email_notification as email

config_file = 'stateful.ini'
config = ConfigParser.RawConfigParser()
config.read(config_file)

hostname = '192.168.1.50'
response = os.system("ping -c 1 {}".format(hostname))

failed = int(config.get('ping', 'failed'))
notified = int(config.get('ping', 'notified'))


def write_config():
    with open(config_file, 'wb') as configfile:
        config.write(configfile)


# and then check the response...
if response == 0:
    if failed != 0:
        failed = 0
        config.set('ping', 'failed', failed)
        write_config()
    if notified != 0:
        notified = 0
        config.set('ping', 'notified', notified)
        write_config()
        # Send success email
        subject = "Anthony-Server7 Responding - SUCCESS"
        body = "Anthony-Server7 has started responding to Ping requests."
        email.send_notification(subject, body)


else:
    failed += 1
    config.set('ping', 'failed', failed)

    if failed >= 5:
        if notified == 0:
            notified += 1
            config.set('ping', 'notified', notified)

            # Send email
            subject = "Anthony-Server7 NOT Responding - FAILURE"
            body = "Anthony-Server7 is not responding to ping requests.\n" \
                   "Please have a Look!"
            email.send_notification(subject, body)

    write_config()