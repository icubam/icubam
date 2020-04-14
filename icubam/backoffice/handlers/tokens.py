from absl import logging
import datetime
import os.path
import tornado.escape
import tornado.web
from typing import Optional, Tuple, List

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import home
from icubam.www.handlers import home as www_home
from icubam.www.handlers import db as www_db
from icubam.db import store


class ListTokensHandler(base.AdminHandler):

  ROUTE = "list_tokens"

  def prepare_for_table(self, client):
    result = [{
      'key': 'name',
      'value': client.name,
      'link': f'{TokenHandler.ROUTE}?id={client.external_client_id}'
    }]
    client_dict = dict()
    for key in ['access_key', 'is_active', 'expiration_date']:
      client_dict[key] = getattr(client, key, None)
    client_dict['access_type'] = (
      client.access_type.name if client.access_type else ''
    )
    client_dict['regions'] = ', '.join([r.name for r in client.regions])
    result.extend(self.format_list_item(client_dict))
    for handler in [www_home.MapByAPIHandler, www_db.DBHandler]:
      route = handler.ROUTE.strip('/').split('/')[0]
      if handler == www_db.DBHandler:
        route += '/bedcounts'
      args = f'?API_KEY={client.access_key}'
      url = os.path.join(self.config.server.base_url, route + args)
      result.append({'key': route, 'value': 'link', 'link': url})
    return result

  @tornado.web.authenticated
  def get(self):
    clients = self.db.get_external_clients()
    data = [self.prepare_for_table(client) for client in clients]
    self.render_list(
      data=data, objtype='Acces Tokens', create_handler=TokenHandler
    )


class TokenHandler(base.AdminHandler):

  ROUTE = 'token'
  ID_KEY = 'external_client_id'
  TIME_FORMAT = "%m/%d/%Y %I:%M %p"

  @tornado.web.authenticated
  def get(self):
    userid = self.get_query_argument('id', None)
    user = None
    regions = []
    if userid is not None:
      user = self.db.get_external_client(userid)
      regions = [r.region_id for r in user.regions]
    return self.do_render(user=user, regions=regions, error=False)

  def do_render(
    self,
    user: Optional[store.User],
    regions: Optional[List[int]],
    error=False
  ):
    user = user if user is not None else store.ExternalClient()
    if user.is_active is None:
      user.is_active = True
    if user.access_type is None:
      user.access_type = store.AccessTypes.ALL
    elif isinstance(user.access_type, str):
      user.access_type = store.AccessTypes.__members__[user.access_type]
    date = ""
    if user.expiration_date is not None:
      date = user.expiration_date.strftime(self.TIME_FORMAT)
    options = self.db.get_regions()
    access_types = list(store.AccessTypes.__members__.keys())
    return self.render(
      "token.html",
      user=user,
      options=options,
      regions=regions,
      error=error,
      access_types=access_types,
      date=date,
      list_route=ListTokensHandler.ROUTE
    )

  def create_token(self, token_id, values, regions):
    client_id, _ = self.db.add_external_client(
      self.current_user.user_id, store.ExternalClient(**values)
    )
    for rid in regions:
      self.db.assign_external_client_to_region(
        self.current_user.user_id, client_id, rid
      )

  def update_token(self, token_id, values, regions):
    self.db.update_external_client(self.current_user.user_id, token_id, values)
    token = self.db.get_external_client(token_id)
    existing_regions = set([region.region_id for region in token.regions])
    for rid in regions.difference(existing_regions):
      self.db.assign_external_client_to_region(
        self.current_user.user_id, token_id, rid
      )
    for rid in existing_regions.difference(regions):
      self.db.remove_external_client_from_region(
        self.current_user.user_id, token_id, rid
      )

  def prepare_for_save(self, token_dict) -> Tuple[int, List[int]]:
    token_dict["is_active"] = token_dict.get("is_active", "off") == 'on'
    date = token_dict.get('expiration_date', '')
    if date == '':
      token_dict['expiration_date'] = None
    else:
      token_dict['expiration_date'] = datetime.datetime.strptime(
        date, self.TIME_FORMAT
      )
    token_id = token_dict.pop(self.ID_KEY, '')
    regions = set(map(int, token_dict.pop('regions', [])))
    return token_id, regions

  @tornado.web.authenticated
  def post(self):
    values = self.parse_from_body(store.ExternalClient)
    token_id, regions = self.prepare_for_save(values)
    try:
      save_fn = self.create_token if not token_id else self.update_token
      save_fn(token_id, values, regions)
    except Exception as e:
      logging.error(f'cannot save token {e}')
      values[self.ID_KEY] = token_id
      return self.do_render(
        store.ExternalClient(**values), regions, error=True
      )

    return self.redirect(ListTokensHandler.ROUTE)
