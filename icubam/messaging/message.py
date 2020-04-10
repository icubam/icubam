class Message:

  TEMPLATE = (
    "Bonjour {},\nvoici le lien à suivre pour mettre à jour les données covid"
    " de {} sur ICUBAM: {}"
  )

  def __init__(self, icu, user, url: str):
    self.icu_id = icu.icu_id
    self.phone = user.telephone.encode('ascii', 'ignore').decode()
    self.user_id = user.user_id
    self.user_name = user.name
    self.icu_name = icu.name
    self.url = url
    self.text = self.TEMPLATE.format(self.user_name, self.icu_name, url)
    self.attempts = 0
    self.first_sent = None

  def reset(self):
    self.attempts = 0
    self.first_sent = None

  @property
  def key(self):
    """Returns an identifier of the message for keying in dicts."""
    return self.user_id, self.icu_id
