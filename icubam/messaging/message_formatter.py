import os.path
import tornado.locale
import tornado.template


class MessageFormatter:
  """This class aims at formatting the messages sent to the user.

  Formatting means turning the data in the message into a localized text or
  html.
  """
  ROOT_PATH = os.path.abspath(__file__)
  for _ in range(3):
    ROOT_PATH = os.path.dirname(ROOT_PATH)

  ROOT_PATH = os.path.join(ROOT_PATH, 'resources/messages/')
  TRANSLATION_FOLDER = os.path.join(ROOT_PATH, 'translations')
  HTML_TEMPLATE = 'message.html'
  TEXT_TEMPLATE = 'message.txt'

  def __init__(self, updater):
    self.updater = updater
    tornado.locale.load_translations(self.TRANSLATION_FOLDER)
    loader = tornado.template.Loader(self.ROOT_PATH)
    self.html_template = loader.load(self.HTML_TEMPLATE)
    self.text_template = loader.load(self.TEXT_TEMPLATE)

  def format(self, msg):
    """Sets both the msg.text and msg.html members of the message."""
    locale = tornado.locale.get(msg.locale_code)
    msg.html = self.html_template.generate(msg, locale=locale)
    msg.text = self.text_template.generate(msg, locale=locale)
    print(msg.html)