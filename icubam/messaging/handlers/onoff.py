
import tornado.web
from icubam.www.handlers import base
from icubam.www.handlers import home


class OnOffHandler(tornado.web.RequestHandler):

  ROUTE = '/onoff'

  def post(self):
    try:
    get_fn = self.get_fns.get(collection, None)
    do_csv = self.get_query_argument('csv', default=None)
    max_ts = self.get_query_argument('max_ts', default=None)
    if get_fn is not None:
      if do_csv:
        if collection == 'get_bedcount':
          self.write(get_fn(max_ts=max_ts).to_csv())
        else:
          self.write(get_fn().to_csv())
      else:
        self.write(get_fn().to_html())
    else:
      self.redirect(home.HomeHandler.ROUTE)
