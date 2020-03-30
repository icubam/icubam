import abc
import tornado.escape

from icubam.backoffice.handlers.base import BaseHandler

"""A base handler for store-related operations (CRUD-like).
Users must be authenticated to be able to call these operations. Instead of
only checking the cookie, this class also checks if the cookie is valid, and
corresponds to a real user in the database. If so, it forwards the user to
the child classes, so derived classes know that they are dealing with a valid
user of the system.
"""
class StoreHandler(BaseHandler, metaclass=abc.ABCMeta):

  def get_logged_user(self):
    userid = self.get_current_user()
    if not userid:
      return None

    return self.store.get_user(int(tornado.escape.json_decode(userid)))

  """Invokes the GET operation on the context of the user."""
  def getForUser(self, user):
    pass

  """Invokes the POST operation on the context of the user."""
  def postForUser(self, user):
    pass

  def validate_and_call(self, callback):
    user = self.get_logged_user()
    if not user:
      self.set_status(401)
      return self.write("Unauthorized")
    return callback(user)

  @tornado.web.authenticated
  def get(self):
    return self.validate_and_call(self.getForUser)

  @tornado.web.authenticated
  def post(self):
    return self.validate_and_call(self.postForUser)
