class QueueWriter:
  """Processes an input queue and write the incoming data to DB."""

  def __init__(self, queue, db):
    self.queue = queue
    self.db = db

  async def process(self):
    async for item in self.queue:
      try:
        self.db.update_bedcount(**item)
      finally:
        self.queue.task_done()
