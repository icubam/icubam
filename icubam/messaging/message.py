import dataclasses

@dataclasses.dataclass
class Message:
  text: str
  user_id: int
  phone: str
  icu_id: int
  icu_name: str
  attempts: int = 0
  first_sent: int = None

  def reset(self):
    self.attempts = 0
    self.first_sent = None
