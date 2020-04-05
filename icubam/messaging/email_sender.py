"""Email sender."""
import abc
from email.message import EmailMessage
import smtplib

from absl import logging


class EmailSender(abc.ABC):
  """Base class for email senders."""

  def __init__(self, config):
    self.config = config

  @abc.abstractmethod
  def send(self, email, subject, contents):
    """Send the email with the specified contents and subject."""
    return


class SMTPEmailSender(EmailSender):
  """Sends emails using an SMTP server."""

  def __init__(self, config):
    super().__init__(config)
    self.smtp = self._connect()

  def _connect(self):
    """Connects to the SMTP server specified in the config."""
    config = self.config
    logging.info(f'Connecting to SMTP server {config.SMTP_HOST}')
    if config.email.use_ssl:
      smtp = smtplib.SMTP_SSL(config.SMTP_HOST)
    else:
      smtp = smtplib.SMTP(config.SMTP_HOST)
    smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
    return smtp

  def _maybe_reconnect(self):
    """Reconnects the SMTP server if disconnected."""
    try:
      self.smtp.noop()
    except smtplib.SMTPServerDisconnected:
      self.smtp = self._connect()

  def send(self, email, subject, contents):
    msg = EmailMessage()
    msg.set_content(contents)
    if subject:
      msg['Subject'] = subject
    self._maybe_reconnect()
    # It is easier to test sendmail instead of send_message.
    self.smtp.sendmail(self.config.EMAIL_FROM, email, msg.as_string())


class FakeEmailSender(EmailSender):

  def send(self, email, subject, contents):
    logging.info(f'Sending |{contents}| with subject |{subject}| to {email}.')


def get(config, protocol=None):
  protocol = protocol or config.email.protocol
  protocol = protocol.lower()
  if protocol == 'smtp':
    return SMTPEmailSender(config)
  elif protocol == 'fake':
    return FakeEmailSender(config)
  raise ValueError(f'Incorrect email protocol {procotol}.')
