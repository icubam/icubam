from absl.testing import absltest
import datetime
from icubam import authenticator
from icubam import config
from icubam.db import store


class AuthenticatorTest(absltest.TestCase):
  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml')
    factory = store.create_store_factory_for_sqlite_db(self.config)
    self.db = factory.create()
    self.admin_id = self.db.add_default_admin()
    self.icu_id = self.db.add_icu(self.admin_id, store.ICU(name='hospital'))
    self.icu = self.db.get_icu(self.icu_id)
    self.user_id = self.db.add_user_to_icu(
      self.admin_id, self.icu_id, store.User(name='michel')
    )
    self.user = self.db.get_user(self.user_id)
    self.authenticator = authenticator.Authenticator(self.config, self.db)

  def test_unknown(self):
    user_icu = self.authenticator.authenticate('something!')
    self.assertIsNone(user_icu)

  def test_with_jwt(self):
    token = self.authenticator.token_encoder.encode_data(self.user, self.icu)
    user_icu = self.authenticator.authenticate(token)
    self.assertIsNotNone(user_icu)
    user, icu = user_icu
    self.assertEqual(user.user_id, self.user.user_id)
    self.assertEqual(icu.icu_id, self.icu.icu_id)

  def test_from_db(self):
    token = self.db.add_token(
      self.admin_id,
      store.UserICUToken(user_id=self.user_id, icu_id=self.icu_id)
    )
    user_icu = self.authenticator.authenticate(token)
    self.assertIsNotNone(user_icu)
    user, icu = user_icu
    self.assertEqual(user.user_id, self.user.user_id)
    self.assertEqual(icu.icu_id, self.icu.icu_id)

  def test_user_not_in_icu(self):
    other_icu_id = self.db.add_icu(self.admin_id, store.ICU(name='other'))
    token = self.db.add_token(
      self.admin_id,
      store.UserICUToken(user_id=self.user_id, icu_id=other_icu_id)
    )
    self.assertIsNotNone(self.authenticator.decode(token))
    self.assertIsNone(self.authenticator.authenticate(token))

  def test_icu_is_off(self):
    self.db.update_icu(self.admin_id, self.icu_id, dict(is_active=False))
    token = self.db.add_token(
      self.admin_id,
      store.UserICUToken(user_id=self.user_id, icu_id=self.icu_id)
    )
    self.assertIsNotNone(self.authenticator.decode(token))
    self.assertIsNone(self.authenticator.authenticate(token))

  def test_get_or_new_token(self):
    self.assertFalse(self.db.has_token(self.user_id, self.icu_id))
    token_str = self.authenticator.get_or_new_token(
      self.user.user_id, self.icu.icu_id
    )
    self.assertGreater(len(token_str), 0)
    token_str2 = self.authenticator.get_or_new_token(
      self.user.user_id, self.icu.icu_id
    )
    self.assertEqual(token_str, token_str2)

  def test_get_or_new_old_but_valid(self):
    user_icu = self.user.user_id, self.icu.icu_id
    validity = self.config.messaging.token_validity_days
    token_str = self.authenticator.get_or_new_token(*user_icu)
    # Now let's change the date of the token in the db to make it old but valid
    old_date = datetime.datetime.utcnow() - datetime.timedelta(
      days=validity * 0.8
    )
    token_obj = self.db.get_token(token_str)
    self.db.update_token(
      None, token_obj.token_id, dict(last_modified=old_date)
    )
    # Checks that we did change the date.
    token_obj = self.db.get_token(token_str)
    self.assertEqual(token_obj.last_modified, old_date)
    # Checks that by calling this function the token has been renewed.
    token_str2 = self.authenticator.get_or_new_token(*user_icu, update=True)
    self.assertIsNotNone(self.authenticator.validity)
    self.assertEqual(token_str, token_str2)

  def test_get_or_new_needs_renew(self):
    user_icu = self.user.user_id, self.icu.icu_id
    validity = self.config.messaging.token_validity_days
    token_str = self.authenticator.get_or_new_token(*user_icu)
    # Now let's change the date of the token in the db to make it old but valid
    old_date = datetime.datetime.utcnow() - datetime.timedelta(
      days=validity + 1
    )
    token_obj = self.db.get_token(token_str)
    self.db.update_token(
      None, token_obj.token_id, dict(last_modified=old_date)
    )
    # Checks that we did change the date.
    token_obj = self.db.get_token(token_str)
    self.assertEqual(token_obj.last_modified, old_date)

    # Checks that by calling this function the token has not been renewed.
    token_str2 = self.authenticator.get_or_new_token(*user_icu, update=False)
    self.assertIsNotNone(self.authenticator.validity)
    self.assertEqual(token_str, token_str2)

    # Checks that by calling this function the token has been renewed.
    token_str3 = self.authenticator.get_or_new_token(*user_icu, update=True)
    self.assertIsNotNone(self.authenticator.validity)
    self.assertNotEqual(token_str, token_str3)


if __name__ == '__main__':
  absltest.main()