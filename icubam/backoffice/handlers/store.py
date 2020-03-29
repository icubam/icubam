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
class StoreHandler(BaseHandler, metaclass=ABCMeta):

  def get_logged_user(self):
    userid = self.get_current_user()
    if not userid:
      return None

    return self.db.get_user(userid)

  """Invokes the get operation on the context of the user."""
 @abc.abstractmethod
  def get(self, user):
      pass

  """Invokes the post operation on the context of the user."""
  @abc.abstractmethod
   def post(self, user):
      pass

  @tornado.web.authenticated
  def get(self):
    user = self.get_logged_user()
    if not user:
      set.set_status(401)
      return self.write("Unauthorized")
    return self.get(user)

  @tornado.web.authenticated
  def post(self):
    user = self.get_logged_user()
    if not user:
      set.set_status(401)
      return self.write("Unauthorized")
    return self.post(user)
