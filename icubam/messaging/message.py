class Message:

  TEMPLATE = (
    "Bonjour {user},\nvoici le lien à suivre pour mettre à jour les"
    " données covid de {icu} sur ICUBAM: {link}"
  )
  HTML = (
    "Bonjour {user},<br/>voici le <a href=\"{link}\">lien à suivre pour mettre"
    " à jour les données covid de {icu} sur ICUBAM</a>"
  )

  def __init__(self, icu, user, url: str):
    self.icu_id = icu.icu_id
    self.phone = user.telephone.encode('ascii', 'ignore').decode()
    self.user_id = user.user_id
    self.user_name = user.name
    self.icu_name = icu.name
    self.url = url
    self.text = self.TEMPLATE.format(
      user=self.user_name, icu=self.icu_name, link=url
    )
    self.html = self.HTML.format(
      user=self.user_name, icu=self.icu_name, link=url
    )
    self.attempts = 0
    self.first_sent = None

  def reset(self):
    self.attempts = 0
    self.first_sent = None

  @property
  def key(self):
    """Returns an identifier of the message for keying in dicts."""
    return self.user_id, self.icu_id
