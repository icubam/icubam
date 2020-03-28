import tornado
from tornado_sqlalchemy import SessionMixin

from backoffice.model.user import User
from backoffice.www.handlers.base import BaseBOHandler
from icubam.www.handlers import base


class CreateUserHandler(SessionMixin, BaseBOHandler):
  ROUTE = '/create_user'

  def get(self):
    count = self.session.query(User).count()
    self.write('{} users so far!'.format(count))


class UserJson(SessionMixin, BaseBOHandler):
  ROUTE = '/users_json'

  @tornado.web.authenticated
  def get(self):
    users = self.session.query(User).all()
    # self.write({"users": users},)
    self.write({"data": User.serialize_list(users)})


class ListUserHandler(SessionMixin, BaseBOHandler):
  ROUTE = '/list_users'

  @tornado.web.authenticated
  def get(self):
    self.render("list_users.html")
