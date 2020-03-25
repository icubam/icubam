from absl import logging
import json
import time
import tornado.web
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token


def time_ago(ts) -> str:
    if ts is None:
        return 'jamais'

    delta = int(time.time() - int(ts))
    units = [(86400, 'jour'), (3600, 'heure'), (60, 'minute'), (1, 'seconde')]
    for unit, name in sorted(units, reverse=True):
        curr = delta // unit
        if curr > 0:
            plural = '' if curr == 1 else 's'  # hack
            return 'il y a {} {}{}'.format(curr, name, plural)
    return 'à l\'instant'


class UpdateHandler(base.BaseHandler):
    ROUTE = '/update'
    QUERY_ARG = 'id'

    def initialize(self, db, queue, token_encoder):
        self.db = db
        self.queue = queue
        self.token_encoder = token_encoder

    def get_icu_data_by_id(self, icu_id):
        df = None
        try:
            df = self.db.get_bedcount_by_icu_id(icu_id)
        except Exception as e:
            logging.error(e)
        result = df.to_dict(orient="records")[0] if df is not None and not df.empty else None
        return result

    @tornado.web.authenticated
    async def get(self):
        """Serves the page with a form to be filled by the user."""
        icu_id = self.get_query_argument("icu_id", None, True)
        if icu_id is None or self.get_icu_data_by_id(icu_id) == None:
            return self.redirect('/error')

        data = self.get_icu_data_by_id(icu_id)

        # self.set_secure_cookie(self.COOKIE, user_token)
        self.render('update_form.html', **data)

    @tornado.web.authenticated
    async def post(self):
        def parse(param):
            parts = param.split('=')
            value = int(parts[1]) if parts[1].isnumeric() else 0
            return parts[0], value

        data = dict([parse(p) for p in self.request.body.decode().split('&')])
        data.update(self.token_encoder.decode(self.get_secure_cookie(self.COOKIE)))
        await self.queue.put(data)
        self.redirect(home.HomeHandler.ROUTE)
