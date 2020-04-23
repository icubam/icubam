from absl.testing import absltest
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
    token_str = self.authenticator.get_or_new_token(self.user, self.icu)
    self.assertGreater(len(token_str), 0)
    token_str2 = self.authenticator.get_or_new_token(self.user, self.icu)
    self.assertEqual(token_str, token_str2)


if __name__ == '__main__':
  absltest.main()