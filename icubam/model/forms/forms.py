from wtforms import StringField
from wtforms_tornado import Form


class UserForm(Form):
  name = StringField()
  mail = StringField()
