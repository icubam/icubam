from absl import logging
import json
import tornado.web
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token


class DataJson(tornado.web.RequestHandler):
    ROUTE = '/beds'

    def initialize(self, db):
        self.db = db

    def get_icu_data(self):
        df = self.db.get_bedcount()
        return df

    def get(self):
        data = self.get_icu_data().to_dict(orient="records")
        self.write({"data": data})


class ShowHandler(base.BaseHandler):
    ROUTE = '/show'

    def initialize(self, db):
        self.db = db

    async def get(self):
        """Serves the page with a form to be filled by the user."""
        self.render("show.html")
