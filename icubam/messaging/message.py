class Message:

  TEMPLATE = (
    "Bonjour {},\nvoici le lien à suivre pour mettre à jour les données covid"
    " de {} sur ICUBAM: {}")

  def __init__(self, icu_id, user, url: str):
    self.icu_id = icu_id
    self.phone = user.telephone
    self.user_id = user.user_id
    self.user_name = user.name
    icu = {icu.icu_id: icu for icu in user.icus}.get(icu_id, None)
    self.icu_name = '' if icu is None else icu.name
    self.url = url
    self.text = self.TEMPLATE.format(self.user_name, self.icu_name, url)
    self.attempts = 0
    self.first_sent = None

  def reset(self):
    self.attempts = 0
    self.first_sent = None
