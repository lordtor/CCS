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
import git, shutil, datetime, time
import colors
from flask import g, request
from rfc3339 import rfc3339
from urllib.parse import urlparse, urljoin

def get_systems():
    systems = []
    for system in app.config['APP_CONFIG']['systems']:
        systems.append(app.config['APP_CONFIG']['systems'][system]['name'])
    return systems
def get_creds_id():
    creds_id = []
    for cred_id in app.config['APP_CONFIG']['app']['creds']:
        creds_id.append(app.config['APP_CONFIG']['app']['creds'][cred_id]['name'])
    return creds_id
def allowed_file(filename):
    # We only want files with a . in the filename
    if not "." in filename:
        return False
    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]
    # Check if the extension is in ALLOWED_IMAGE_EXTENSIONS
    if ext in app.config["ALLOWED_FILE_EXTENSIONS"]:
        return True
    else:
        return False
def allowed_file_size(filesize):

    if int(filesize) <= app.config["MAX_CONTENT_LENGTH"]:
        return True
    else:
        return False
def git_connect(system):
    git_config = {}
    git_config.update(app.config['APP_CONFIG']['systems'][system]['git'])
    DIR_NAME = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
    git_config["DIR_NAME"] = DIR_NAME
    git_config['log_conf'] =  app.config['LOG_CONF']
    git_config['cred_id'] = app.config['APP_CONFIG']['app']['creds'][app.config['APP_CONFIG']['systems'][system]['git']['cred_id']]
    git_config['sys_user'] =  app.config['GIT']
    app.logger.debug(colors.color("{}".format(dumps(git_config, indent=4)), fg="orange"))
    return gIt(git_config)
def systems_changes():
    systems_changes = {}
    for system in app.config['APP_CONFIG']['systems']:
        gc = git_connect(system)
        status = gc.check_changes()
        app.logger.info("system_changes:{}:{}".format(system, status))
        systems_changes.update({"{}".format(system): status})
    app.logger.info("systems_changes:{}".format(systems_changes))
    return systems_changes
def list_systems_dirs(system):
    dirs = []
    for r,d,f in walk(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])):
        if ".git" not in r:
            dirs.append(r)
    return dirs

def read_file(file_path):
    with open(file_path, 'r') as file:
        data = file.read()
        file.close()
    return data

def make_tree(system, pp=None):
    if pp == None:
        app.logger.debug("make_tree.system: {}".format(system))
        pp = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
        app.logger.debug("make_tree.pp: {}".format(pp))
    rp = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
    tree = dict(name=pp.replace(rp, path.join("/static/uploads/repository", app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])), children=[])
    app.logger.debug("make_tree.tree: {}".format(tree))
    try: 
        lst = listdir(pp)
        app.logger.debug("make_tree.lst: {}".format(lst))
    except OSError:
        pass #ignore errors
    else:
        for name in lst:
            app.logger.debug("make_tree.name: {}".format(name))
            if name != ".git":
                fn = path.join(pp, name)
                app.logger.debug("make_tree.fn: {}".format(fn))
                if path.isdir(fn):
                    app.logger.debug("make_tree.path.isdir.fn: {}".format(fn))
                    tree['children'].append(make_tree(pp=fn, system=system))
                else:
                    app.logger.debug("make_tree.path.isfile.fn: {}".format(fn))
                    tree['children'].append(dict(name=fn.replace(rp, path.join("/static/uploads/repository", app.config['APP_CONFIG']['systems'][system]['git']['work_dir']))))
    app.logger.debug("make_tree.tree: {}".format(tree))
    return tree
def is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    app.logger.debug("is_safe_url.ref_url: {}".format(ref_url))
    test_url = urlparse(urljoin(request.host_url, target))
    app.logger.debug("is_safe_url.test_url: {}".format(test_url))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def get_redirect_target():
    for target in request.form.get('next'), request.values.get('next'), request.referrer:
        app.logger.debug("get_redirect_target.target: {}".format(target))
        if is_safe_url(target):
            app.logger.debug("get_redirect_target.return.target: {}".format(target))
            return target
    return '/' 

@app.before_request
def start_timer():
    g.start = time.time()

@app.after_request
def log_request(response):
    # if request.path == '/favicon.ico':
    #     return response
    # elif request.path.startswith('/static'):
    #     return response
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
    app.logger.info(line)

    return response

@app.route("/")
def index():
    return render_template("public/index.html", envs=get_systems())


@app.route("/about")
def about():
    from markdown2 import markdown
    readme = read_file(path.join(app.config['ROOT_DIR'], "README.md"))
    content = markdown(readme, extras=["tables","fenced-code-blocks",'attr_list', 'footnotes']).replace('<table>', '<table class="table">')
    return render_template("public/about.html", envs=get_systems(), content=content)

@app.route("/show-config")
def config():
    return render_template("public/show-config.html", envs=get_systems(), val=app.config)

@app.route("/json", methods=["POST"])
def json_example():
    if request.is_json:
        req = request.get_json()
        response_body = {
            "message": "JSON received!",
            "sender": req.get("name")
        }
        res = make_response(jsonify(response_body), 200)
        return res
    else:
        return make_response(jsonify({"message": "Request body must be JSON"}), 400)


@app.route("/get-file/<path:path>")
def get_report(path):
    try:
        return send_from_directory(app.config["UPLOADS"], filename=path, as_attachment=True)
    except FileNotFoundError:
        abort(404)


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

@app.route("/env-settings/<system>", methods=["GET", "POST"])
def env_settings_name(system):
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
            app.config['APP_CONFIG']['systems'].pop(system, None)
            app.config['APP_CONFIG']['systems'].update({"{}".format(req.get("name")): sys})
            flash('New configuration succesed update on memory'.format(req.get("name")))
            with open(app.config['APP_CONFIG_FILE'], 'w') as f:
                dump(app.config['APP_CONFIG'], f)
                flash('New configuration succesed saved on disk'.format(req.get("name")))
            return render_template("public/env-settings.html", systems_changes=systems_changes(), systems=app.config['APP_CONFIG']['systems'], envs=get_systems())
        elif 'push' in req:
            gc = git_connect(system)
            if app.config['APP_CONFIG']['systems'][system]["git"]["work_branch_pref"] != "":
                br = gc.branch_new(pref=app.config['APP_CONFIG']['systems'][system]["git"]["work_branch_pref"])
                gc.push(branch=br)
                app.config['APP_CONFIG']['systems'][system]["git"]["branch"] = br
                with open(app.config['APP_CONFIG_FILE'], 'w') as f:
                    dump(app.config['APP_CONFIG'], f)
                    flash('New configuration succesed saved on disk'.format(req.get("name")))
            else:
                gc.push(branch=app.config['APP_CONFIG']['systems'][system]["git"]["work_branch_pref"])

    return render_template("public/env-settings.html", systems_changes=systems_changes(), system=system_d, envs=get_systems(), creds=get_creds_id())
    
@app.route("/env-settings/<system>/dell", methods=["GET", "POST"])
def env_settings_dell_name(system):
    #shutil.rmtree(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['work_dir']))
    for filename in listdir(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['work_dir'])):
        file_path = path.join(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['work_dir']), filename)
        try:
            if path.isfile(file_path) or path.islink(file_path):
                unlink(file_path)
            elif path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    app.config['APP_CONFIG']['systems'].pop(system, None)
    flash('System {} deleted from memory configuration'.format(system))
    with open(app.config['APP_CONFIG_FILE'], 'w') as f:
        dump(app.config['APP_CONFIG'], f)
        flash('New configuration succesed saved on disk'.format(system))
    return render_template("public/env-settings.html", systems_changes=systems_changes(), systems=app.config['APP_CONFIG']['systems'], envs=get_systems())



@app.route("/env-settings/<system>/upload", methods=["GET", "POST"])
def upload(system):
    dirs = list_systems_dirs(system)
    tree = make_tree(pp=None, system=system)
    if request.method == "POST":
        if request.files:
            r = request.form
            upload_file_name = request.files["file"]
            if upload_file_name.filename == "":
                app.logger.error('System {}: file not selected'.format(system))
                flash('System {}: file not selected'.format(system), 'danger')
                return redirect('/env-settings/{}/upload'.format(system))
            if allowed_file(upload_file_name.filename):
                if "filesize" in request.cookies:
                    if not r.get("path"):
                        app.logger.error('System {}: uploaded folder don`t selected'.format(system))
                        flash('System {}: uploaded folder don`t selected'.format(system), 'danger')
                    return redirect('/env-settings/{}/upload'.format(system))
                    upload_file_name.save(path.join(r.get("path"), upload_file_name.filename))
                    app.logger.info('System {}: file {} in {} success uloaded'.format(system, upload_file_name.filename ,r.get("path")))
                    flash('System {}: file {} in {} success uloaded'.format(system, upload_file_name.filename ,r.get("path")), "success")
                if not allowed_file_size(request.cookies["filesize"]):
                    app.logger.error('System {}: filesize exceeded maximum limit'.format(system))
                    flash('System {}: filesize exceeded maximum limit'.format(system), 'danger')
                    return redirect('/env-settings/{}/upload'.format(system))
                return redirect('/env-settings/{}/upload'.format(system))
            else:
                app.logger.info("That file extension is not allowed")
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
        if not req.get("name") in app.config['APP_CONFIG']['systems']:
            app.config['APP_CONFIG']['systems'].update({"{}".format(req.get("name")): sys})
            flash('System {} add to memory configuration success'.format(req.get("name")), "success")
            with open(app.config['APP_CONFIG_FILE'], 'w') as f:
                dump(app.config['APP_CONFIG'], f)
                flash('System {} succesed saved on disk'.format(req.get("name")), "success")
        else:
            flash('System {} exist!'.format(req.get("name")), "danger")
        return render_template("public/env-settings.html", systems_changes=systems_changes(), systems=app.config['APP_CONFIG']['systems'], envs=get_systems())
    return render_template("public/env-settings-add.html", creds=get_creds_id(), envs=get_systems())

@app.route("/env-settings/<system>/update", methods=["GET", "POST"])
def env_settings_update(system):
    app.logger.info("Update system: {}".format(system))
    gc = git_connect(system)
    DIR_NAME = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
    if not path.exists(DIR_NAME):
        gc.clone()
        flash('System {} cloned success '.format(system), "success")
        gc.checkout(app.config['APP_CONFIG']['systems'][system]['git']['branch'])
        flash('System {} checkout to branch {}'.format(system, app.config['APP_CONFIG']['systems'][system]['git']['branch']), "success")
    else:
        try:
            gc.checkout(app.config['APP_CONFIG']['systems'][system]['git']['branch'])
            flash('System {} checkout to branch {}'.format(system, app.config['APP_CONFIG']['systems'][system]['git']['branch']), "success")
            gc.pull(app.config['APP_CONFIG']['systems'][system]['git']['branch'])
            flash('System {} pulling success'.format(system), "success")
        except git.exc.GitCommandError as e:
            app.logger.info(e)
            flash('{}'.format(e), "danger")
            gc.head_reset()
            flash('System {} head reset success'.format(system), "danger")
            gc.pull(app.config['APP_CONFIG']['systems'][system]['git']['branch'])
            flash('System {} pulling success'.format(system), "danger")

    return render_template("public/env-settings.html", systems_changes=systems_changes(), systems=app.config['APP_CONFIG']['systems'], envs=get_systems())

@app.route("/env-settings/<system>/diff", methods=["GET", "POST"])
def env_settings_diff(system):
    gc = git_connect(system)
    root = path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])
    app.logger.info(request)
    diff = gc.list_diff_changes()
    if request.method == "POST":
        app.logger.info("Commit in system: {}".format(system))
        req = request.form
        app.logger.debug("env_settings_diff.post.req:{}".format(req))
        if 'commit_all' in req:
            app.logger.debug("env_settings_diff.post.commit_all:{}".format(diff["untracked_files"]+diff["changed_files"]))
            file_list = diff["untracked_files"]+diff["changed_files"]
        elif 'commit_selected' in req:
            app.logger.debug("env_settings_diff.post.commit_selected:{}".format(req.getlist("untracked_files")+req.getlist("changed_files")))
            file_list = req.getlist("untracked_files")+req.getlist("changed_files")
        elif 'commit_all_untracked' in req:
            file_list = diff["untracked_files"]
        elif 'commit_all_changed' in req:
            app.logger.debug("env_settings_diff.post.commit_all_changed:{}".format(diff["changed_files"]))
            file_list = diff["changed_files"]
        elif "back" in req:
            #url = get_redirect_target()
            app.logger.debug("env_settings_diff.post.back.url:{}".format('/env-settings/{}'.format(system)))
            return redirect('/env-settings/{}'.format(system))
        commit_message = req.get("commit_message")
        app.logger.debug("env_settings_diff.post.commit_message:{}".format(commit_message))
        gc.add(file_list)
        gc.commit(commit_message)
        app.logger.info("Get new diff for system: {}".format(system))
        diff = gc.list_diff_changes()
    else:
        app.logger.info("Get diff for system: {}".format(system))
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
        flash('{}'.format(app_conf), "success")
        app.config['APP_CONFIG'].update({"app": app_conf})
        flash('CCS config add to memory configuration success', "success")
        with open(app.config['APP_CONFIG_FILE'], 'w') as f:
            dump(app.config['APP_CONFIG'], f)
            flash('CCS config succesed saved on disk', "success")
    return render_template("public/app-settings.html", system=app.config['APP_CONFIG']['app'], envs=get_systems())


@app.route("/cred-settings", methods=["GET", "POST"])
def cred_settings():
    creds = app.config['APP_CONFIG']['app']['creds']
    return render_template("public/cred-settings.html", creds=creds, envs=get_systems())

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
        if not req.get("name") in app.config['APP_CONFIG']['app']['creds']:
            app.config['APP_CONFIG']['app']['creds'].update({"{}".format(req.get("name")): cred})
            flash('CCS {} add to memory configuration success'.format(req.get("name")), "success")
            with open(app.config['APP_CONFIG_FILE'], 'w') as f:
                dump(app.config['APP_CONFIG'], f)
                flash('CCS {} succesed saved on disk'.format(req.get("name")), "success")
                return redirect(url_for('cred-settings'))  
        else:
            flash('CCS {} cred exist!'.format(req.get("name")), "danger")
        return render_template("public/cred-settings-add.html", system=app.config['APP_CONFIG']['app'], files=files)
    return render_template("public/cred-settings-add.html", system=app.config['APP_CONFIG']['app'], files=files, envs=get_systems())


@app.route("/env-settings/<system>/files")
def list_files(system):
    """Endpoint to list files on the server."""
    files = []
    for filename in os.listdir(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir'])):
        path = os.path.join(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir']), filename)
        if os.path.isfile(path):
            files.append(filename)
    return jsonify(files)


@app.route("/env-settings/<system>/files/<path:path>")
def get_file(path, system):
    """Download a file."""
    return send_from_directory(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir']), path, as_attachment=True)


@app.route("/env-settings/<system>/files/<filename>", methods=["POST"])
def post_file(filename, system):
    """Upload a file."""

    if "/" in filename:
        # Return 400 BAD REQUEST
        abort(400, "no subdirectories directories allowed")

    with open(os.path.join(path.join(app.config['REPOSITORY'], app.config['APP_CONFIG']['systems'][system]['git']['work_dir']), filename), "wb") as fp:
        fp.write(request.data)

    # Return 201 CREATED
    return "", 201

@app.route('/editor')
def new_post():
    if request.method == 'POST':
        data = request.form.get('ckeditor')  # <--

    return render_template('editor.html')