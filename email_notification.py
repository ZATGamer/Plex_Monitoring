import smtplib
import ConfigParser


def send_notification(subject, body):
    config = ConfigParser.RawConfigParser()
    config.read('config.ini')
    message = \
        "From: {sender}\n" \
        "To: {receivers}\n" \
        "Subject: {subject}\n \n" \
        "{body}".format(sender=config.get('EmailInfo', 'sender'),
                        receivers=config.get('EmailInfo', 'recipient'),
                        subject=subject,
                        body=body)

    session = smtplib.SMTP(config.get('EmailInfo', 'server'), int(config.get('EmailInfo', 'port')))
    session.ehlo()
    session.starttls()
    session.ehlo()
    session.login(config.get('EmailInfo', 'sender'), config.get('EmailInfo', 'password'))
    session.sendmail(config.get('EmailInfo', 'sender'), config.get('EmailInfo', 'recipient'), message)
    session.quit()