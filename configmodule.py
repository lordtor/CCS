from os import path, makedirs, remove, listdir, walk, unlink
from sys import platform
from json import load, dump, dumps
from app.lib.flgit import git_operation as g
basedir = path.abspath(path.dirname(__file__))
import logging, shutil
from logging.config import dictConfig
import colors
from distutils.util import strtobool

def l(logger, t, m):
    if t == "i":
        logger.info(colors.color("{}".format(m), fg="blue"))
    elif t == "d":
        logger.debug(colors.color("{}".format(m), fg="green"))
    elif t == "e":
        logger.error(colors.color('{}'.format(m), fg="red"))
    elif t == "w":
        logger.warning(colors.color('{}'.format(m), fg="orange"))


def check_path(path_dir):
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
                "cred_file_dir": "C:\\ccs",
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
    #check_path(repository)
    systems_dirs = []
    for system in  conf['systems']:
        systems_dirs.append(conf['systems'][system]["git"]["work_dir"])
        logger.info(colors.color("Check system: {}".format(system), fg="green"))
        DIR_NAME = path.join(repository, conf['systems'][system]['git']['work_dir'])
        logger.info(colors.color("{} path: {}".format(system, DIR_NAME), fg="green"))
        gc = {}
        gc.update( conf['systems'][system]['git'])
        gc["DIR_NAME"] = DIR_NAME
        gc['log_conf'] = log_conf
        gc['cred_id'] = conf['app']['creds'][conf['systems'][system]['git']['cred_id']]
        gc['sys_user'] = git
        go = g(gc)
        if path.exists(gc['DIR_NAME']) and path.isdir(gc['DIR_NAME']):
            logger.debug(colors.color("{} {}".format(system, "Path exists"), fg="orange"))
            if not listdir(gc['DIR_NAME']):
                logger.debug(colors.color("{} {}".format(system, "Path is empty"), fg="orange"))
                if strtobool(gc['auto_recreate']):
                    logger.debug(colors.color("{} auto_recreate: {}".format(system, gc['auto_recreate']), fg="orange"))
                    try:
                        logger.debug(colors.color("{} try: {}".format(system, "clean"), fg="orange"))
                        shutil.rmtree(gc['DIR_NAME'])
                    except Exception as e:
                        logger.error(colors.color('{} Failed to delete {}. Reason:{}'.format(system, gc['DIR_NAME'], e), fg="red"))
                    finally:
                        logger.debug(colors.color("{} try: {}".format(system, "clone"), fg="orange"))
                        go.clone(gc['branch'])
            else:
                logger.debug(colors.color("{} {}".format(system, "Directory is not empty"), fg="orange"))
                logger.debug(colors.color("{} auto_recreate: {}".format(system, gc['auto_recreate']), fg="orange"))
                logger.debug(colors.color("{} .git: {}".format(system, path.exists(path.join(gc['DIR_NAME'],".git"))), fg="orange"))
                logger.debug(colors.color("{} platform: {}".format(system, platform), fg="orange"))
                if strtobool(gc['auto_recreate']):
                    if not platform.startswith('win') or not path.exists(path.join(gc['DIR_NAME'],".git")):
                        for filename in listdir(gc['DIR_NAME']):
                            file_path = path.join(gc['DIR_NAME'], filename)
                            try:
                                logger.debug(colors.color("{} try: {}".format(system, "clean"), fg="orange"))
                                if path.isfile(file_path) or path.islink(file_path):
                                    unlink(file_path)
                                elif path.isdir(file_path):
                                    shutil.rmtree(file_path)
                            except Exception as e:
                                logger.error(colors.color('{} Failed to delete {}. Reason:{}'.format(system, file_path, e), fg="red"))
                        try:
                            logger.debug(colors.color("{} try: {}".format(system, "clone"), fg="orange"))
                            go.clone(gc['branch'])
                        except Exception as e:
                            logger.error(colors.color('{} Failed clone {}. Reason:{}'.format(system, file_path, e), fg="red"))
                    else:
                        logger.debug(colors.color("{} try: {}".format(system, "head_reset"), fg="orange"))
                        go.head_reset()
                        logger.debug(colors.color("{} try: {}".format(system, "pull"), fg="orange"))
                        go.pull()
                else:
                    logger.debug(colors.color("{} try: {}".format(system, "fetch"), fg="orange"))
                    go.fetch()
                    logger.debug(colors.color("{} auto_pull: {}".format(system, gc['auto_pull']), fg="orange"))
                    if strtobool(gc['auto_pull']):
                        logger.debug(colors.color("{} try: {}".format(system, "pull"), fg="orange"))
                        go.pull()
        else:
            logger.debug(colors.color("{}".format("Given Directory don't exists"), fg="orange"))
            go.clone()
        logger.debug(colors.color("Check system: {} is: done".format(system), fg="orange"))
    return repository


class Config(object):
    APPLICATION_ROOT='/'
    ROOT_DIR = basedir
    APP = path.join(basedir, 'app')
    STATIC = path.join(APP,'static')
    UPLOADS =  path.join(STATIC, "uploads")
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
    LOG_DIR_PATH = path.join(basedir, path.join(path.join('app','static'), LOG_DIR_NAME))
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
    FLASKCODE_RESOURCE_BASEPATH = REPOSITORY
    FLASKCODE_EDITOR_THEME = 'vs'
    FLASKCODE_APP_TITLE = 'CCS'