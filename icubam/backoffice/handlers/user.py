from tornado_sqlalchemy import SessionMixin

from icubam.backoffice.handlers.base import BaseBOHandler
from icubam.model.forms.forms import UserForm
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


class AddUserHandler(SessionMixin, BaseBOHandler):
  ROUTE = '/add_user'

  def get(self):
    userForm = UserForm()
    self.render('add_user.html', form=userForm, **{"fields": userForm.__dict__.keys()})

  def post(self):
    form = UserForm(self.request.arguments)
    if form.validate():
      user = User(name=form.data["name"], mail=form.data["mail"])
      self.session.add(user)
      self.session.commit()
      self.session.close()
      self.redirect("/list_users")
    else:
      raise Exception("Form not valid")
