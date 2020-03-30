import dataclasses

class Message:

  TEMPLATE = (
    "Bonjour {},\nvoici le lien à suivre pour mettre à jour les données covid"
    " de {} sur ICUBAM: {}")

  def __init__(self, icu_id, icu_name, phone, user_id, user_name):
    self.text = ''
    self.phone = phone
    self.user_id = user_id
    self.user_name = user_name
    self.icu_id = icu_id
    self.icu_name = icu_name
    self.attempts = 0
    self.first_sent = None

  def reset(self):
    self.attempts = 0
    self.first_sent = None

  def build(self, url: str):
    self.text = self.TEMPLATE.format(self.user_name, self.icu_name, url)
