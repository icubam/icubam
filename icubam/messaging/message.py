class Message:
  def __init__(self, icu, user, url: str = ''):
    self.icu_id = icu.icu_id
    self.phone = user.telephone
    if self.phone is not None:
      self.phone = self.phone.encode('ascii', 'ignore').decode()
    self.user_id = user.user_id
    self.user_name = user.name
    self.icu_name = icu.name
    self.url = url

    # TODO(olivier): have this in the region.
    self.locale_code = 'fr'

    # Those are filled at send time by the MessageFormatter
    self.text = ""
    self.html = ""

    # Members used by the scheduler.
    self.attempts = 0
    self.first_sent = None

  def reset(self):
    self.attempts = 0
    self.first_sent = None

  @property
  def key(self):
    """Returns an identifier of the message for keying in dicts."""
    return self.user_id, self.icu_id
