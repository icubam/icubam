from absl import logging
import json
import tornado.web
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token


class UpdateHandler(base.BaseHandler):
    ROUTE = '/update'
    QUERY_ARG = 'id'

    def initialize(self, db, queue):
        self.db = db
        self.queue = queue

    def get_icu_data_by_id(self, icu_id, def_val=0):
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
        data.update(token.decode(self.get_secure_cookie(self.COOKIE)))
        await self.queue.put(data)
        self.redirect(home.HomeHandler.ROUTE)
