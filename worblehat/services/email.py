import smtplib

from textwrap import indent

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import Config


def send_email(to: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg['From'] = Config['smtp.from']
    msg['To'] = to
    if Config['smtp.subject_prefix']:
        msg['Subject'] = f"{Config['smtp.subject_prefix']} {subject}"
    else:
        msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if Config['smtp.enabled'] and not Config['deadline_daemon.dryrun']:
        try:
            with smtplib.SMTP(Config['smtp.host'], Config['smtp.port']) as server:
                server.starttls()
                server.login(
                    Config['smtp.username'],
                    Config.read_password(Config['smtp.password']),
                )
                server.sendmail(Config['smtp.from'], to, msg.as_string())
        except Exception as err:
            print('Error: could not send email.')
            print(err)
    else:
        print('Debug: Email sending is disabled, so the following email was not sent:')
        print(indent(msg.as_string(), '  '))