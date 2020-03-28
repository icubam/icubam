from tornado_sqlalchemy import SessionMixin

from icubam.backoffice.handlers.base import BaseBOHandler
from icubam.model.user import User


class UserJson(SessionMixin, BaseBOHandler):
  ROUTE = '/users_json'

  def get(self):
    users = self.session.query(User).all()
    self.write({"data": User.serialize_list(users)})


class ListUserHandler(SessionMixin, BaseBOHandler):
  ROUTE = '/list_users'

  def get(self):
    self.render("list_users.html")
