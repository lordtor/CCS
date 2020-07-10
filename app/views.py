from app import app
from flask import render_template
from datetime import datetime
from flask import request, redirect
from flask import jsonify, make_response
from os import path, makedirs, remove, listdir, walk, unlink
from werkzeug.utils import secure_filename
from flask import send_file, send_from_directory, safe_join, abort
from flask import session, url_for
from flask import flash
from json import dump, dumps
from app.lib.flgit import git_operation as gIt
from app.lib.utils import *
import git, shutil, datetime, time
import colors
from flask import g, request
from rfc3339 import rfc3339
from urllib.parse import urlparse, urljoin
from markdown2 import markdown
import re, jinja2

@app.before_request
def start_timer():
    br = {"Headers": "{}".format(request.headers), "Body": "{}".format(request.get_data())}
    app.logger.debug(colors.color("{}".format(dumps({
            "system": "CCS", 
            "action": "before_request", 
            "message": "m", 
            "value": br}, sort_keys=True, indent=4)), fg="blue"))
    g.start = time.time()


@app.after_request
def log_request(response):
    if request.path == '/favicon.ico':
         return response
    elif request.path.startswith('/static'):
         return response
    now = time.time()
    duration = round(now - g.start, 2)
    dt = datetime.datetime.fromtimestamp(now)
    timestamp = rfc3339(dt, utc=True)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    host = request.host.split(':', 1)[0]
    args = dict(request.args)
    log_params = [
        ('method', request.method, 'blue'),
        ('path', request.path, 'blue'),
        ('status', response.status_code, 'yellow'),
        ('duration', duration, 'green'),
        ('time', timestamp, 'magenta'),
        ('ip', ip, 'red'),
        ('host', host, 'red'),
        ('params', args, 'blue')
    ]
    request_id = request.headers.get('X-Request-ID')
    if request_id:
        log_params.append(('request_id', request_id, 'yellow'))
    parts = []
    for name, value, color in log_params:
        part = colors.color("{}={}".format(name, value), fg=color)
        parts.append(part)
    line = " ".join(parts)
    app.logger.debug(colors.color("{}".format(line), fg="green"))
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("public/index.html", envs=get_systems())


@app.route("/about")
def about():
    readme = read_file(path.join(app.config['ROOT_DIR'], "README.md"))
    content = markdown(readme, extras=["tables","fenced-code-blocks",'attr_list', 'footnotes']).replace('<table>', '<table class="table">')
    return render_template("public/about.html", envs=get_systems(), content=content)


@app.route("/show-config")
def config():
    return render_template("public/show-config.html", envs=get_systems(), val=app.config)


@app.errorhandler(403)
def forbidden(e):
    return render_template("error_handlers/forbidden.html", envs=get_systems()), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error_handlers/404.html", envs=get_systems()), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error_handlers/500.html", envs=get_systems()), 500


@app.route("/env-settings")
def env_settings():
    return render_template("public/env-settings.html", systems=app.config['APP_CONFIG']['systems'], systems_changes=systems_changes(), envs=get_systems())


@app.route("/env-settings/<system>/edit", methods=["GET", "POST"])
def env_settings_edit(system):
    system_d=app.config['APP_CONFIG']['systems'][system]
    if request.method == "POST":
        req = request.form
        if 'save' in req:
            sys = {
                "name": req.get("name"),
                "git": {
                    "cred_id": req.get("cred"),
                    "url": req.get("url"),
                    "branch": req.get("branch"),
                    "work_branch_pref": req.get("work_branch_pref"),
                    "work_dir": req.get("work_dir"),
                    "auto_recreate":req.get("auto_recreate"),
                    "auto_pull": req.get("auto_pull")}
                    }
            l(t="d", j=True, s=req.get("name"), a="env-settings_edit.save", v=sys, m='new_config')
            try:
                app.config['APP_CONFIG']['systems'].pop(system, None)
                l(t="d", j=True, s=req.get("name"), a="env-settings_edit.save", v=True, m='Delete old configuration from memory')
                app.config['APP_CONFIG']['systems'].update({"{}".format(req.get("name")): sys})
                l(t="d", j=True, s=req.get("name"), a="env-settings_edit.save", v=True, m='Add new configuration in memory')
                flash('New configuration for {} succesed update on memory'.format(req.get("name")), "success")
                with open(app.config['APP_CONFIG_FILE'], 'w') as f:
                    dump(app.config['APP_CONFIG'], f, sort_keys=True, indent=4)
                    l(t="d", j=True, s=req.get("name"), a="env-settings_edit.save", v=True, m='Write new configuration on file')
                    flash('New configuration for {} succesed saved on disk'.format(req.get("name")), "success")
            except Exception as e:
                flash('Faild update/save configuration for {}: \n{}'.format(req.get("name"), e), "danger")
                l(t="e", j=True, s=req.get("name"), a="env-settings_edit.save", v=e, m='Faild update/save configuration')
        elif 'push' in req:
            gc = git_connect(system)
            if app.config['APP_CONFIG']['systems'][system]["git"]["work_branch_pref"] != "":
                br = gc.branch_new(pref=app.config['APP_CONFIG']['systems'][system]["git"]["work_branch_pref"])
                gc.push(branch=br)
                l(t="d", j=True, s=req.get("name"), a="env-settings_edit.push", v=br, m='New branch created and pushed')
                flash('New branch: {} created and pushed'.format(br), "success")
                app.config['APP_CONFIG']['systems'][system]["git"]["branch"] = br
                flash('New configuration for {} succesed update on memory'.format(req.get("name")), "success")
                l(t="d", j=True, s=req.get("name"), a="env-settings_edit.push.update_conf", v=True, m='New configuration succesed update on memory')
                with open(app.config['APP_CONFIG_FILE'], 'w') as f:
                    dump(app.config['APP_CONFIG'], f, sort_keys=True, indent=4)
                    flash('New configuration succesed saved on disk'.format(req.get("name")), "success")
                    l(t="d", j=True, s=req.get("name"), a="env-settings_edit.push.save_conf", v=True, m='New configuration succesed saved on disk')
            else:
                gc.push(branch=app.config['APP_CONFIG']['systems'][system]["git"]["branch"])
                flash('Branch: {} pushed'.format(app.config['APP_CONFIG']['systems'][system]["git"]["branch"]), "success")
                l(t="d", j=True, s=req.get("name"), a="env-settings_edit.push", v=app.config['APP_CONFIG']['systems'][system]["git"]["branch"], m='Branch pushed')
        elif "back" in req:
            return redirect('/env-settings')
        elif "revert" in req:
            return redirect(url_for('env_settings_edit', system=system))
        elif "delete" in req:
            return redirect(url_for('env_settings_delete', system=system))
        elif "diff" in req:
            return redirect(url_for('env_settings_diff', system=system))
        elif "files" in req:
            return redirect(url_for('env_settings_files', system=system))
        elif "editor" in req:
            return redirect(url_for('env_settings_browse', system=system))
        
    return render_template("public/env-settings-edit.html", system=system_d, envs=get_systems(), creds=get_creds_id())

@app.route('/env-settings/<system>/browse', methods=['GET'], defaults={'file_url': None})
@app.route("/env-settings/<system>/browse", methods=["GET"])
def env_settings_browse(system, file_url=None):
    if file_url == None:
        file_url = url_for('static', filename='clean.txt')
    l(t="e", j=True, s=system, a=file_url, v="e", m='Monaco')
    system_p = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
    dirname = path.basename(system_p)
    dtree = dir_tree(abs_path=system_p, abs_root_path=app.config['STATIC'], exclude_names=[".git"])
    print(dtree)
    return render_template("public/browse.html", envs=get_systems(), dirname=dirname, dtree=dtree, system=system, file_url=file_url)


@app.route("/env-settings/<system>/browse/save", methods=["POST"])
def env_settings_browse_save(system, file_url=None):
    if request.method == "POST":
        file_url = request.form.get('Path').replace("/static","static")
        data = request.form.get('monaco')
        system = request.form.get('system')
        l(t="i", j=True, s=system, a="save", v=data, m='Monaco')
        try:
            pp = path.abspath(path.join(app.config['APP'], file_url))
            if not path.exists(path.split(path.abspath(pp))[0]):
                makedirs(path.split(path.abspath(pp))[0])
            f = open(pp, "w", encoding = 'utf8')
            f.write(data)
            f.close()
            flash('File {} saved'.format(file_url))
            system_p = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
            dirname = path.basename(system_p)
            dtree = dir_tree(abs_path=system_p, abs_root_path=app.config['STATIC'], exclude_names=[".git"])
            tree = render_template("public/tree.html", dir_tree=dtree)
            return jsonify(tree=tree, system = system , file_url=file_url)

        except Exception as e:
            l(t="e", j=True, s=system, a=file_url, v=e, m='Monaco')
            flash('Error for saving file {}: \n {}'.format(file_url, e))
            abort(500)

@app.route("/env-settings/<system>/dell", methods = ['GET', 'POST'])
def env_settings_delete(system):
    l(t="i", j=True, s=system, a="env-settings_dell", v=None, m='Run deleting system')
    for filename in listdir(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])):
        file_path = path.join(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir']), filename)
        try:
            if path.isfile(file_path) or path.islink(file_path):
                unlink(file_path)
            elif path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            l(t="e", j=True, s=system, a="env-settings_dell", v=e, m='Failed to delete')
    app.config['APP_CONFIG']['systems'].pop(system, None)
    l(t="d", j=True, s=system, a="env-settings_dell", v=None, m='Delete system from memory configuration')
    flash('System {} deleted from memory configuration'.format(system))
    with open(app.config['APP_CONFIG_FILE'], 'w') as f:
        dump(app.config['APP_CONFIG'], f, sort_keys=True, indent=4)
        flash('New configuration succesed saved on disk'.format(system))
        l(t="d", j=True, s=system, a="env-settings_dell", v=None, m='Save new configuration on disk')
    return render_template("public/env-settings.html", systems_changes=systems_changes(), systems=app.config['APP_CONFIG']['systems'], envs=get_systems())

@app.route("/env-settings/<system>/files", methods=["GET", "POST"])
def env_settings_files(system):
    dirs = list_systems_dirs(system)
    tree = make_tree(pp=None, system=system)
    if request.method == "POST":
        if request.files:
            r = request.form
            upload_file_name = request.files["file"]
            if upload_file_name.filename == "":
                l(t="e", j=True, s=system, a="env-settings_files.upload", v=None, m='File not selected')
                flash('System {}: file not selected'.format(system), 'danger')
                return redirect('/env-settings/{}/upload'.format(system))
            if allowed_file(upload_file_name.filename):
                if "filesize" in request.cookies:
                    if not r.get("path"):
                        l(t="e", j=True, s=system, a="env-settings_files.upload", v=None, m='Uploaded folder don`t selected')
                        flash('System {}: uploaded folder don`t selected'.format(system), 'danger')
                    return redirect('/env-settings/{}/upload'.format(system))
                    upload_file_name.save(path.join(r.get("path"), upload_file_name.filename))
                    l(t="i", j=True, s=system, a="env-settings_files.upload", v=upload_file_name.filename, m=' file in {} success uloaded'.format(r.get("path")))
                    flash('System {}: file {} in {} success uloaded'.format(system, upload_file_name.filename ,r.get("path")), "success")
                if not allowed_file_size(request.cookies["filesize"]):
                    l(t="e", j=True, s=system, a="env-settings_files.upload", v=None, m='filesize exceeded maximum limit')
                    flash('System {}: filesize exceeded maximum limit'.format(system), 'danger')
                    return redirect('/env-settings/{}/upload'.format(system))
                return redirect('/env-settings/{}/upload'.format(system))
            else:
                l(t="e", j=True, s=system, a="env-settings_files.upload", v=None, m='that file extension is not allowed')
                flash('System {}: that file extension is not allowed'.format(system), 'danger')
                return redirect('/env-settings/{}/upload'.format(system))
    return render_template("public/upload.html", envs=get_systems(), dirs=dirs, tree=tree)


@app.route("/env-settings/add", methods=["GET", "POST"])
def env_settings_add():
    if request.method == "POST":
        req = request.form
        sys = {
            "name": req.get("name"),
            "git": {
                "cred_id": req.get("cred"),
                "url": req.get("url"),
                "branch": req.get("branch"),
                "work_branch_pref": req.get("work_branch_pref"),
                "work_dir": req.get("work_dir"),
                "auto_recreate":req.get("auto_recreate"),
                "auto_pull": req.get("auto_pull")}
            }
        l(t="d", j=True, s=req.get("name"), a="env-settings_add", v=sys, m='new_config')
        if not req.get("name") in app.config['APP_CONFIG']['systems']:
            app.config['APP_CONFIG']['systems'].update({"{}".format(req.get("name")): sys})
            flash('System {} add to memory configuration success'.format(req.get("name")), "success")
            l(t="i", j=True, s=req.get("name"), a="env-settings_add", v=True, m='Add new configuration in memory')
            with open(app.config['APP_CONFIG_FILE'], 'w') as f:
                dump(app.config['APP_CONFIG'], f, sort_keys=True, indent=4)
                l(t="i", j=True, s=req.get("name"), a="env-settings_add", v=True, m='Write new configuration on file')
                flash('System {} succesed saved on disk'.format(req.get("name")), "success")
        else:
            l(t="e", j=True, s=req.get("name"), a="env-settings_add", v=None, m='System exist!')
            flash('System {} exist!'.format(req.get("name")), "danger")
        return render_template("public/env-settings.html", systems_changes=systems_changes(), systems=app.config['APP_CONFIG']['systems'], envs=get_systems())
    return render_template("public/env-settings-add.html", creds=get_creds_id(), envs=get_systems())


@app.route("/env-settings/<system>/update", methods=["GET", "POST"])
def env_settings_update(system):
    l(t="d", j=True, s=system, a="env-settings_update", v=None, m='Run update system')
    gc = git_connect(system)
    DIR_NAME = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
    if not path.exists(DIR_NAME):
        gc.clone()
        l(t="d", j=True, s=system, a="env-settings_update", v=DIR_NAME, m='Not exist! System cloned.')
        flash('System {} cloned success '.format(system), "success")
        gc.checkout(app.config['APP_CONFIG']['systems'][system]['git']['branch'])
        l(t="d", j=True, s=system, a="env-settings_update", v=app.config['APP_CONFIG']['systems'][system]['git']['branch'], m='Checkouted')
        flash('System {} checkout to branch {}'.format(system, app.config['APP_CONFIG']['systems'][system]['git']['branch']), "success")
    else:
        try:
            gc.checkout(app.config['APP_CONFIG']['systems'][system]['git']['branch'])
            l(t="d", j=True, s=system, a="env-settings_update", v=app.config['APP_CONFIG']['systems'][system]['git']['branch'], m='Checkouted')
            flash('System {} checkout to branch {}'.format(system, app.config['APP_CONFIG']['systems'][system]['git']['branch']), "success")
            gc.pull(app.config['APP_CONFIG']['systems'][system]['git']['branch'])
            l(t="i", j=True, s=system, a="env-settings_update", v=app.config['APP_CONFIG']['systems'][system]['git']['branch'], m='Pulled')
            flash('System {} pulling success'.format(system), "success")
        except git.exc.GitCommandError as e:
            l(t="e", j=True, s=system, a="env-settings_update", v=e, m='Error')
            flash('{}'.format(e), "danger")
            gc.head_reset()
            l(t="i", j=True, s=system, a="env-settings_update", v=None, m='Head reset')
            flash('System {} head reset success'.format(system), "danger")
            gc.pull(app.config['APP_CONFIG']['systems'][system]['git']['branch'])
            l(t="i", j=True, s=system, a="env-settings_update", v=app.config['APP_CONFIG']['systems'][system]['git']['branch'], m='Pulled')
            flash('System {} pulling success'.format(system), "danger")
    return render_template("public/env-settings.html", systems_changes=systems_changes(), systems=app.config['APP_CONFIG']['systems'], envs=get_systems())

@app.route("/env-settings/<system>/diff", methods=["GET", "POST"])
def env_settings_diff(system):
    gc = git_connect(system)
    root = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
    diff = gc.list_diff_changes()
    l(t="d", j=True, s=system, a="env-settings_diff", v=diff, m='')
    if request.method == "POST":
        req = request.form
        if 'commit_all' in req:
            l(t="i", j=True, s=system, a="env-settings_diff.commit_all", v={"untracked_files": diff["untracked_files"], "changed_files": diff["changed_files"]}, m='Commit all')
            file_list = diff["untracked_files"]+diff["changed_files"]
        elif 'commit_selected' in req:
            l(t="i", j=True, s=system, a="env-settings_diff.commit_selected", v={"untracked_files": req.getlist("untracked_files"), "changed_files": req.getlist("changed_files")}, m='Commit selected')
            file_list = req.getlist("untracked_files")+req.getlist("changed_files")
        elif 'commit_all_untracked' in req:
            l(t="i", j=True, s=system, a="env-settings_diff.commit_all_untracked", v={"commit_all_untracked": diff["untracked_files"]}, m='Commit all untracked files')
            file_list = diff["untracked_files"]
        elif 'commit_all_changed' in req:
            l(t="i", j=True, s=system, a="env-settings_diff.changed_files", v={"changed_files": diff["changed_files"]}, m='Commit all changed')
            file_list = diff["changed_files"]
        elif "back" in req:
            return redirect(url_for('env_settings_edit', system=system))
        commit_message = req.get("commit_message")
        gc.add(file_list)
        gc.commit(commit_message)
        l(t="i", j=True, s=system, a="env-settings_diff.commit", v=commit_message, m='Commited')
        return redirect(url_for('env_settings_diff', system=system))
    return render_template("public/env-diff.html", system=system, envs=get_systems(), diff=diff)


@app.route("/app-settings", methods=["GET", "POST"])
def app_settings():
    if request.method == "POST":
        req = request.form
        app_conf = {
            "SECRET_KEY": app.config['APP_CONFIG']['app']['SECRET_KEY'],
            "CSRF": req.get("CSRF"),
            "DEBUG": req.get("DEBUG"),
            "SESSION_COOKIE_SECURE": req.get("SESSION_COOKIE_SECURE"),
            "ENV": req.get("ENV"),
            "MAX_CONTENT_LENGTH": int(req.get("MAX_CONTENT_LENGTH")),
            "ALLOWED_FILE_EXTENSIONS": req.get("ALLOWED_FILE_EXTENSIONS").split(','),
            "repository_dir": req.get("repository_dir"),
            "cred_file_dir": req.get("cred_file_dir"),
            "loginig": {
                "log_dir": req.get("log_dir"),
                "log_file_name": req.get("log_file_name"),
                "log_level": req.get("log_level"),
                "log_max_size": int(req.get("log_max_size")),
                "log_backup_count": int(req.get("log_backup_count"))
            },
            "git_settings": {
                "git_log_level": req.get("git_log_level"),
                "git_user": req.get("git_user"),
                "git_mail": req.get("git_mail")
            },
            "creds": app.config['APP_CONFIG']['app']['creds']
        }
        app.config['APP_CONFIG'].update({"app": app_conf})
        l(t="i", j=True, s="CCS", a="app-settings.memory_update", v=app.config['APP_CONFIG']["app"], m='config add to memory')
        flash('CCS config add to memory configuration success', "success")
        with open(app.config['APP_CONFIG_FILE'], 'w') as f:
            dump(app.config['APP_CONFIG'], f, sort_keys=True, indent=4)
            l(t="i", j=True, s="CCS", a="app-settings.write_disk", v=app.config['APP_CONFIG'], m='config write on disk')
            flash('CCS config succesed saved on disk', "success")
    return render_template("public/app-settings.html", system=app.config['APP_CONFIG']['app'], envs=get_systems())


@app.route("/cred-settings", methods=["GET", "POST"])
def cred_settings():
    creds = app.config['APP_CONFIG']['app']['creds']
    return render_template("public/cred-settings.html", creds=creds, envs=get_systems())

@app.route("/cred-settings/<cred>/edit", methods=["GET", "POST"])
def cred_settings_edit(cred):
    files = []
    for f in listdir(app.config['APP_CONFIG']['app']["cred_file_dir"]):
        if path.isfile(path.join(app.config['APP_CONFIG']['app']["cred_file_dir"], f)):
            files.append(f)
    old_name = cred
    cred = app.config['APP_CONFIG']['app']['creds'][cred]
    if request.method == "POST":
        req = request.form
        cred = {
            "name": req.get("name"),
            "login": req.get("login"),
            "cred_file": path.join(app.config['APP_CONFIG']['app']["cred_file_dir"], req.get("file"))
            }
        l(t="d", j=True, s="CCS", a="cred_settings-edit", v=cred, m='Update cred')
        app.config['APP_CONFIG']['app']['creds'].update({"{}".format(req.get("name")): cred})
        l(t="d", j=True, s="CCS", a="cred-settings-edit.memory_update", v=req.get("name"), m='Update to memory configuration')
        if old_name != req.get("name"):
            for system in app.config['APP_CONFIG']['systems']:
                if app.config['APP_CONFIG']['systems'][system]['git']['cred_id'] == old_name:
                    l(t="w", j=True, s="CCS", a="cred-settings-edit.update_cred_id.systems", v=system, m='Update cred id for system')
                    app.config['APP_CONFIG']['systems'][system]['git'].update({'cred_id': req.get("name")})

        flash('CCS {} add to memory configuration success'.format(req.get("name")), "success")
        with open(app.config['APP_CONFIG_FILE'], 'w') as f:
            dump(app.config['APP_CONFIG'], f, sort_keys=True, indent=4)
            l(t="i", j=True, s="CCS", a="cred-settings-edit.write_disk", v=app.config['APP_CONFIG'], m='configuration save on disk')
            flash('CCS {} succesed saved on disk'.format(req.get("name")), "success")
            return redirect(url_for('cred_settings'))  
    return render_template("public/cred-settings-edit.html", cred=cred, system=app.config['APP_CONFIG']['app'], files=files, envs=get_systems())

@app.route("/cred-settings-add", methods=["GET", "POST"])
def cred_settings_add():
    files = []
    for f in listdir(app.config['APP_CONFIG']['app']["cred_file_dir"]):
        if path.isfile(path.join(app.config['APP_CONFIG']['app']["cred_file_dir"], f)):
            files.append(f)
    if request.method == "POST":
        req = request.form
        cred = {
            "name": req.get("name"),
            "login": req.get("login"),
            "cred_file": path.join(app.config['APP_CONFIG']['app']["cred_file_dir"], req.get("file"))
            }
        l(t="d", j=True, s="CCS", a="cred-settings-add", v=cred, m='new cred')
        if not req.get("name") in app.config['APP_CONFIG']['app']['creds']:
            app.config['APP_CONFIG']['app']['creds'].update({"{}".format(req.get("name")): cred})
            l(t="d", j=True, s="CCS", a="cred-settings-add.memory_update", v=req.get("name"), m='add to memory configuration')
            flash('CCS {} add to memory configuration success'.format(req.get("name")), "success")
            with open(app.config['APP_CONFIG_FILE'], 'w') as f:
                dump(app.config['APP_CONFIG'], f, sort_keys=True, indent=4)
                l(t="i", j=True, s="CCS", a="cred-settings-add.write_disk", v=req.get("name"), m='configuration save on disk')
                flash('CCS {} succesed saved on disk'.format(req.get("name")), "success")
                return redirect(url_for('cred-settings'))  
        else:
            l(t="e", j=True, s="CCS", a="cred-settings-add.write_disk", v=req.get("name"), m='cred exist')
            flash('CCS {} cred exist!'.format(req.get("name")), "danger")
        return redirect(url_for('cred_settings'))
    return render_template("public/cred-settings-add.html", system=app.config['APP_CONFIG']['app'], files=files, envs=get_systems())