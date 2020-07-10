from app import app

from datetime import datetime
from os import path, makedirs, remove, listdir, walk, unlink
from json import dump, dumps
from app.lib.flgit import git_operation as gIt
import git, shutil, datetime, time
import colors
from rfc3339 import rfc3339
from urllib.parse import urlparse, urljoin
from markdown2 import markdown



def l(t,m,j=False,s="CCS",a=None,v=None):

    if j:
        m = dumps({
            'system': s, 
            'action': a, 
            'message': m, 
            'value': v}, sort_keys=True, indent=4)
    if t == "i":
        app.logger.info(colors.color("{}".format(m), fg="blue"))
    elif t == "d":
        app.logger.debug(colors.color("{}".format(m), fg="green"))
    elif t == "e":
        app.logger.error(colors.color('{}'.format(m), fg="red"))
    elif t == "w":
        app.logger.warning(colors.color('{}'.format(m), fg="orange"))


def get_systems():
    systems = []
    for system in app.config['APP_CONFIG']['systems']:
        systems.append(app.config['APP_CONFIG']['systems'][system]['name'])
    systems.sort()
    l(t="d", j=True, s="CCS", a="get_systems", v=systems,
    m="get_systems.systems.value")
    return systems


def get_creds_id():
    creds_id = []
    for cred_id in app.config['APP_CONFIG']['app']['creds']:
        creds_id.append(app.config['APP_CONFIG']['app']['creds'][cred_id]['name'])
    l(t="d", j=True, s="CCS", a="get_creds_id", v=creds_id,
    m="get_creds_id.creds_id.value")
    return creds_id


def allowed_file(filename):
    if not "." in filename:
        l(t="d", j=True, s="CCS", a="allowed_file", v=False,
        m="return")
        return False
    ext = filename.rsplit(".", 1)[1]
    l(t="d", j=True, s="CCS", a="get_systems", v=ext,
    m="ext.value")
    if ext.upper() in map(lambda x:x.upper(), app.config["ALLOWED_FILE_EXTENSIONS"]):
        l(t="d", j=True, s="CCS", a="allowed_file", v=True,
        m="return")
        return True
    else:
        l(t="d", j=True, s="CCS", a="allowed_file", v=False,
        m="return")
        return False


def allowed_file_size(filesize):
    l(t="d", j=True, s="CCS", a="allowed_file_size", v=filesize,
    m="")
    if int(filesize) <= app.config["MAX_CONTENT_LENGTH"]:
        l(t="d", j=True, s="CCS", a="allowed_file_size", v=True, m="return")
        return True
    else:
        l(t="d", j=True, s="CCS", a="allowed_file_size", v=False, m="return")
        return False


def git_connect(system):
    git_config = {}
    git_config.update(app.config['APP_CONFIG']['systems'][system]['git'])
    DIR_NAME = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
    git_config["DIR_NAME"] = DIR_NAME
    git_config['log_conf'] =  app.config['LOG_CONF']
    git_config['cred_id'] = app.config['APP_CONFIG']['app']['creds'][app.config['APP_CONFIG']['systems'][system]['git']['cred_id']]
    git_config['sys_user'] =  app.config['GIT']
    l(t="d", j=True, s=system, a="git_connect", v=git_config, m="Create connect")
    return gIt(git_config)


def systems_changes():
    systems_changes = {}
    for system in app.config['APP_CONFIG']['systems']:
        gc = git_connect(system)
        status = gc.check_changes()
        l(t="d", j=True, s=system, a="system_changes", v=status, m="")
        systems_changes.update({"{}".format(system): status})
    l(t="d", j=True, s="CCS", a="system_changes", v=systems_changes, m="return")
    return systems_changes


def list_systems_dirs(system):
    dirs = []
    for r,d,f in walk(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])):
        if ".git" not in r:
            dirs.append(r)
    l(t="d", j=True, s=system, a="list_systems_dirs", v=dirs, m="return")
    return dirs


def read_file(file_path):
    with open(file_path, 'r') as file:
        data = file.read()
        file.close()
    l(t="d", j=True, s="CCS", a="read_file", v=data, m=file_path)
    return data


def make_tree(system, pp=None):
    l(t="d", j=True, s=system, a="make_tree", v=pp, m="")
    if pp == None:
        pp = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
        l(t="d", j=True, s=system, a="make_tree", v=pp, m="")
    rp = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
    l(t="d", j=True, s=system, a="make_tree", v=rp, m="rp")
    tree = dict(name=pp.replace(rp, path.join("/static/uploads/repository", app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])), children=[])
    l(t="d", j=True, s=system, a="make_tree", v=tree, m="tree")
    try: 
        lst = listdir(pp)
        l(t="d", j=True, s=system, a="make_tree", v=lst, m="lst")
    except OSError as e:
        l(t="e", j=True, s=system, a="make_tree", v=e, m="Error")
    else:
        for name in lst:
            l(t="d", j=True, s=system, a="make_tree", v=name, m="name")
            if name != ".git":
                fn = path.join(pp, name)
                l(t="d", j=True, s=system, a="make_tree", v=fn, m="fn")
                if path.isdir(fn):
                    tree['children'].append(make_tree(pp=fn, system=system))
                else:
                    tree['children'].append(dict(name=fn.replace(rp, path.join("/static/uploads/repository", app.config['APP_CONFIG']['systems'][system]['git']['work_dir']))))
            else:
                l(t="d", j=True, s=system, a="make_tree", v=True, m=".git")
    l(t="d", j=True, s=system, a="make_tree", v=tree, m="return")
    return tree

def get_file_extension(filename):
    ext = path.splitext(filename)[1]
    if ext.startswith('.'):
        ext = ext[1:]
    return ext.lower()

def dir_tree(abs_path, abs_root_path, exclude_names=None, excluded_extensions=None, allowed_extensions=None):
    tree = dict(
        name=path.basename(abs_path),
        path_name=path.relpath(abs_path, start=abs_root_path),
        children=[]
    )
    try:
        dir_entries = listdir(abs_path)
    except OSError:
        pass
    else:
        for name in dir_entries:
            if exclude_names and name in exclude_names:
                continue
            new_path = path.join(abs_path, name)
            if path.isdir(new_path):
                tree['children'].append(dir_tree(new_path, abs_root_path, exclude_names, excluded_extensions, allowed_extensions))
            else:
                ext = get_file_extension(name)
                if (excluded_extensions and ext in excluded_extensions) or (allowed_extensions and ext not in allowed_extensions):
                    continue
                tree['children'].append(dict(
                    name=path.basename(new_path),
                    path_name=path.relpath(new_path, start=abs_root_path).replace("\\", "/"),
                    is_file=True,
                ))
    return tree