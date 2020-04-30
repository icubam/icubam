import os.path
import tornado.locale
import tornado.template
import pathlib


class MessageFormatter:
  """This class aims at formatting the messages sent to the user.

  Formatting means turning the data in the message into a localized text or
  html.
  """
  ROOT_PATH = pathlib.Path(__file__).resolve().parents[2].as_posix()
  ROOT_PATH = os.path.join(ROOT_PATH, 'resources', 'messages')
  TRANSLATION_FOLDER = os.path.join(ROOT_PATH, 'translations')
  HTML_TEMPLATE = 'message.html'
  TEXT_TEMPLATE = 'message.txt'

  def __init__(self):
    tornado.locale.load_translations(self.TRANSLATION_FOLDER)
    loader = tornado.template.Loader(self.ROOT_PATH)
    self.html_template = loader.load(self.HTML_TEMPLATE)
    self.text_template = loader.load(self.TEXT_TEMPLATE)

  def format(self, msg, may_renew_token=False):
    """Sets both the msg.text and msg.html members of the message."""
    locale = tornado.locale.get(msg.locale_code)
    html = self.html_template.generate(msg=msg, _=locale.translate)
    msg.html = html.decode()
    text = self.text_template.generate(msg=msg, _=locale.translate)
    msg.text = text.decode()
