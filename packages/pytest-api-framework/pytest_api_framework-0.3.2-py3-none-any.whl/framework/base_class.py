import traceback

import pytest
from box import Box

from framework.utils.log_util import logger
from framework.db.mysql_db import MysqlDB
from framework.db.redis_db import RedisDB
from framework.exit_code import ExitCode
from framework.http_client import ResponseUtil
from framework.global_attribute import CONTEXT, CONFIG, GlobalAttribute


class BaseTestCase(object):
    context: GlobalAttribute = None
    config: GlobalAttribute = None
    http = None
    data: Box = None
    belong_app = None
    response: ResponseUtil = None

    def request(self, app=None, *, account, data, **kwargs):
        try:
            app = self.default_app(app)
            app_http = getattr(self.http, app)
            self.response = getattr(app_http, account).request(data=data, keyword=kwargs)
            return self.response
        except AttributeError as e:
            logger.error(f"app {app} or account {account} no exist: {e}")
            traceback.print_exc()
            pytest.exit(ExitCode.APP_OR_ACCOUNT_NOT_EXIST)
            return None

    def post(self, app, account, url, data=None, json=None, **kwargs):
        return getattr(getattr(self.http, app), account).post(app, url, data=data, json=json, **kwargs)

    def get(self, app, account, url, params=None, **kwargs):
        return getattr(getattr(self.http, app), account).get(app, url, params=params, **kwargs)

    def put(self, app, account, url, data=None, **kwargs):
        return getattr(getattr(self.http, app), account).put(app, url, data=data, **kwargs)

    def delete(self, app, account, url, **kwargs):
        return getattr(getattr(self.http, app), account).delete(app, url, **kwargs)

    def mysql_conn(self, db, app=None):
        config = CONFIG.get(app=self.default_app(app), key="mysql")
        config["db"] = db
        return MysqlDB(**config)

    def redis_conn(self, db, app=None):
        config = CONFIG.get(app=self.default_app(app), key="redis")
        config["db"] = db
        return RedisDB(**config)

    def contest_set(self, app=None, *, key, value):
        app = self.default_app(app)
        self.context.set(app=app, key=key, value=value)

    def contest_get(self, app=None, *, key):
        app = self.default_app(app)
        return self.context.get(app=app, key=key)

    def config_get(self, app=None, *, key):
        app = self.default_app(app)
        return self.config.get(app=app, key=key)

    def default_app(self, app):
        return app or self.belong_app
