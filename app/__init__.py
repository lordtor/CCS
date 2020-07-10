from flask import Flask, session
import configmodule
import logging
from logging.handlers import RotatingFileHandler
from app.lib.flgit import git_operation
from os import environ, path
from werkzeug.utils import import_string
from logging.config import dictConfig
from flask_assets import Environment, Bundle

app = Flask(__name__)

_env_name = environ.get("APPLICATION_SETTINGS", default="DefaultConfig")
cfg = import_string(('configmodule.'+ _env_name))()
app.config.from_object(cfg)
app.logger = logging.getLogger('CCS')
assets = Environment(app)
js = Bundle('js/jquery.min.js',
'js/bootstrap.min.js',
'js/popper.min.js',
'vendor/monaco-editor/min/vs/loader.js')
#'vendor/monaco-editor/min/vs/editor/editor.main.css',
css = Bundle(
'css/style.css',
'css/bootstrap.min.css',
'css/open-iconic-bootstrap.min.css') 
assets.register('js_all', js)
assets.register('css_all', css)
from app import views
