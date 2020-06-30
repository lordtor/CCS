from os import path, makedirs, remove, listdir, walk
from json import load, dump, dumps
from app.lib.flgit import git_operation as g
basedir = path.abspath(path.dirname(__file__))
import logging, shutil
from logging.config import dictConfig
import colors

def check_path(path_dir):
    print(path_dir)
    if not path.exists(path_dir):
        makedirs(path_dir)

def read_file(file_path):
    with open(file_path, 'r') as file:
        data = file.read().replace('\n', '')
        file.close()
    return data

def load_conf(file_name):
    if not path.isfile(file_name):
        print('Config not found! Create new.')
        data = {
            "systems": {},
            "app":{
                "SECRET_KEY": 'OCML3BRawWEUeaxcuKHLpw',
                "CSRF": True,
                "DEBUG": False,
                "SESSION_COOKIE_SECURE": False,
                "ENV": "production",
                "MAX_CONTENT_LENGTH": 50 * 1024 * 1024,
                "ALLOWED_FILE_EXTENSIONS": ["json", "txt", "html", "conf", "sub"],
                "repository_dir": "repository",
                "cred_file_dir": "/run/secrets",
                "loginig": {
                    "log_dir": "logs",
                    "log_file_name": "CCS.log",
                    "log_level": "INFO",
                    "log_max_size": 1024,
                    "log_backup_count": 3
                },
                "git_settings": {
                    "git_log_level": "INFO",
                    "git_user": "Yuriy Rumyantsev",
                    "git_mail": "rumyantsevyn@yandex.ru",
                },
                "creds": {}
            }
        }
        with open(file_name, 'w') as f:
            dump(data, f)
    else:
        print("Config found.")
    with open(file_name) as f:
        conf = load(f)
    return conf



def check_repository(pathx, conf, log_conf, logger, git):
    repository = path.join(pathx, conf['app']['repository_dir'])
    check_path(repository)
    systems_dirs = []
    for system in  conf['systems']:
        print(conf['systems'][system]["git"]["work_dir"])
        systems_dirs.append(conf['systems'][system]["git"]["work_dir"])
        logger.info("Check system: {}".format(system))
        DIR_NAME = path.join(repository, conf['systems'][system]['git']['work_dir'])
        git_config = {}
        git_config.update( conf['systems'][system]['git'])
        git_config["DIR_NAME"] = DIR_NAME
        git_config['log_conf'] = log_conf
        git_config['cred_id'] = conf['app']['creds'][conf['systems'][system]['git']['cred_id']]
        git_config['sys_user'] = git
        go = g(git_config)
        if not path.exists(DIR_NAME) or ".git" not in listdir(DIR_NAME) or conf['systems'][system]['git']['auto_recreate']:
            logger.debug(colors.color("{}".format("NOT EXIST"), fg="red"))
            go.clone(conf['systems'][system]['git']['branch'])
        else:
            if conf['systems'][system]['git']['auto_pull']:
                logger.debug(colors.color("{}".format("AUTO PULL"), fg="green"))
                go.config_user()
                go.fetch()
                go.pull()
            else:
                logger.debug(colors.color("{}".format("FETCH"), fg="green"))
                go.config_user()
                go.fetch()

    for dir in listdir(repository):
        if dir not in systems_dirs:
            print("{} not exist in project setting {}".format(dir, systems_dirs))
            shutil.rmtree(path.join(repository, dir))
            print("Deleted")

    return repository


class Config(object):
    DEBUG = False
    TESTING = False
    ROOT_DIR = basedir
    UPLOADS =  path.join(path.join(basedir, 'app/static'), "uploads")
    check_path(UPLOADS)
    CONFIG_PATH = path.join(UPLOADS, 'ccs')
    check_path(CONFIG_PATH)
    APP_CONFIG_FILE = path.join(CONFIG_PATH, 'config.json')
    APP_CONFIG = load_conf(APP_CONFIG_FILE)
    CREDS = {}
    for cred in APP_CONFIG["app"]["creds"]:
        CREDS["{}".format(APP_CONFIG["app"]["creds"][cred]["name"])] = {
            "name": APP_CONFIG["app"]["creds"][cred]["name"],
            "login": APP_CONFIG["app"]["creds"][cred]["login"],
            "passwd": read_file(APP_CONFIG["app"]["creds"][cred]["cred_file"])
        }
    SESSION_TYPE = 'filesystem'

class DefaultConfig(Config):
    DEBUG = Config.APP_CONFIG["app"]["DEBUG"]
    CSRF_ENABLED = Config.APP_CONFIG["app"]["CSRF"]
    SECRET_KEY = Config.APP_CONFIG["app"]["SECRET_KEY"]
    SESSION_COOKIE_SECURE = Config.APP_CONFIG["app"]["SESSION_COOKIE_SECURE"]
    ALLOWED_FILE_EXTENSIONS = Config.APP_CONFIG["app"]["ALLOWED_FILE_EXTENSIONS"]
    MAX_CONTENT_LENGTH = Config.APP_CONFIG["app"]["MAX_CONTENT_LENGTH"] * 1024 * 1024 #50MB
    GIT = { "user": Config.APP_CONFIG["app"]["git_settings"]["git_user"],
            "mail": Config.APP_CONFIG["app"]["git_settings"]["git_mail"]
        }
    GIT_LOG =  Config.APP_CONFIG["app"]["git_settings"]["git_log_level"]
    LOG_DIR_NAME = Config.APP_CONFIG["app"]["loginig"]["log_dir"]
    LOG_DIR_PATH = path.join(basedir, path.join('app/static', LOG_DIR_NAME))
    LOG_FILE_NAME = Config.APP_CONFIG["app"]["loginig"]["log_file_name"]
    LOG_LEVEL =  Config.APP_CONFIG["app"]["loginig"]["log_level"]
    LOG_MAX = Config.APP_CONFIG["app"]["loginig"]["log_max_size"]
    LOG_BACKUP_COUNT = Config.APP_CONFIG["app"]["loginig"]["log_backup_count"]
    check_path(LOG_DIR_PATH)
    LOG_CONF = {
        "version":1,
        "handlers":{
            "fileHandler":{
                "class":"logging.handlers.RotatingFileHandler",
                "formatter": "{}{}".format("CCSFormatter",LOG_LEVEL),
                "filename": "{}".format(path.join(LOG_DIR_PATH, LOG_FILE_NAME)),
                "maxBytes": LOG_MAX,
                "backupCount": LOG_BACKUP_COUNT
            },
            "fileHandlerGit":{
                "class":"logging.handlers.RotatingFileHandler",
                "formatter": "{}{}".format("CCSFormatter",LOG_LEVEL),
                "filename": "{}".format(path.join(LOG_DIR_PATH, "git.log")),
                "maxBytes": LOG_MAX,
                "backupCount": LOG_BACKUP_COUNT
            },
            "console": {
                "class" : "logging.StreamHandler",
                "formatter": "{}{}".format("CCSFormatter",LOG_LEVEL),
                "level"   : LOG_LEVEL,
            }
        },
        "loggers":{
            "CCS":{
                "handlers":["fileHandler", "console"],
                "level"   : LOG_LEVEL
            },
            "GIT":{
                "handlers":["fileHandlerGit", "console"],
                "level"   : GIT_LOG
            }
        },
        "formatters":{
            "CCSFormatterDEBUG":{
                "format":"%(asctime)s - %(name)s - %(levelname)s - %(message)s  [in %(pathname)s:%(lineno)d]"
            },
            "CCSFormatterINFO":{
                "format":"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    }
    logging.config.dictConfig(LOG_CONF)
    logger = logging.getLogger("CCS")
    REPOSITORY = check_repository(Config.UPLOADS, Config.APP_CONFIG, LOG_CONF, logger, GIT)
    
class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"
    SECRET_KEY = 'OCML3BRawWEUeaxcuKHLpw'
    DATABASE =  DATABASE = path.join(basedir, 'production_database.db')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE
    ALLOWED_FILE_EXTENSIONS = ["json", "txt", "html", "conf", "sub"]

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    ENV = "staging"
    DATABASE =  DATABASE = path.join(basedir, 'staging_database.db')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    ENV = "development"
    DATABASE = path.join(basedir,'development_database.db')
    #SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    TESTING = True
    ENV = "testing"
    DATABASE = path.join(basedir,'testing_database.db')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE