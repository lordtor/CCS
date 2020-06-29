from flask import Flask, session
import configmodule
import logging
from logging.handlers import RotatingFileHandler
from app.lib.flgit import git_operation
from os import environ, path
from werkzeug.utils import import_string
from logging.config import dictConfig

app = Flask(__name__)


_env_name = environ.get("APPLICATION_SETTINGS", default="DefaultConfig")
cfg = import_string(('configmodule.'+ _env_name))()
app.config.from_object(cfg)
dictConfig(app.config["LOG_CONF"])
app.logger = logging.getLogger('CCS')


from app import views
from app import admin_views