import os
import smtplib
import unittest
from unittest.mock import call, patch

from icubam.messaging import email_sender
from icubam import config

SMTP_HOST = 'localhost'
SMTP_USER = 'smtp_user'
SMTP_PASSWORD = 'password'
EMAIL_FROM = 'icubam@localhost'


class EmailSenderTest(unittest.TestCase):
  def setUp(self):
    super().setUp()
    os.environ['SMTP_HOST'] = SMTP_HOST
    os.environ['SMTP_USER'] = SMTP_USER
    os.environ['SMTP_PASSWORD'] = SMTP_PASSWORD
    os.environ['EMAIL_FROM'] = EMAIL_FROM
    self.config = config.Config('resources/test.toml', mode='dev')

  def test_fake_send(self):
    sender = email_sender.get(self.config, 'FAKE')
    sender.send('user@test.org', 'Test!', 'foo bar.')

  @patch('smtplib.SMTP')
  def test_smtp_send(self, mock_smtp):
    self.config.email.use_ssl = False
    sender = email_sender.get(self.config, 'SMTP')
    sender.send('user@test.org', 'Test!', 'foo bar.')

    mock_smtp.assert_called_once_with(SMTP_HOST)
    smtp = mock_smtp.return_value
    smtp.login.assert_called_once_with(SMTP_USER, SMTP_PASSWORD)
    msg = (
      'Content-Type: text/plain; charset="utf-8"\n'
      'Content-Transfer-Encoding: 7bit\n'
      'MIME-Version: 1.0\n'
      'Subject: Test!\n\nfoo bar.\n'
    )
    smtp.sendmail.assert_called_once_with(EMAIL_FROM, 'user@test.org', msg)

  @patch('smtplib.SMTP_SSL')
  def test_smtp_use_ssl(self, mock_smtp_ssl):
    self.config.email.use_ssl = True
    email_sender.SMTPEmailSender(self.config)
    mock_smtp_ssl.assert_called_once_with(SMTP_HOST)

  @patch('smtplib.SMTP')
  def test_smtp_reconnect(self, mock_smtp):
    self.config.email.use_ssl = False
    sender = email_sender.SMTPEmailSender(self.config)

    smtp = mock_smtp.return_value
    smtp.noop.side_effect = smtplib.SMTPServerDisconnected()
    sender.send('user@test.org', 'Test!', 'foo bar.')

    self.assertEqual(
      mock_smtp.call_args_list,
      [call(SMTP_HOST), call(SMTP_HOST)]
    )
    smtp.sendmail.assert_called_once()
