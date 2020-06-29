# Config Control System (CCS)

## Blog Posts

An automatic configuration management system for subordinate programs or systems that uses a distributed version control system (Git).

## Quick Start

### First Steps

Installing dependencies

```sh
$ pyvenv-3.6 env
$ source env/bin/activate
$ pip install -r requirements.txt
```

### Configuration

The basic configuration is performed automatically, then it can be edited via the web-ui. You can also configure or add a system via the web-ui. Next, the configuration can be performed by editing the config.json file

### Run

Run each in a different terminal window...

```sh
# the app
$ python run.py
# or
$ flask run
```

## Advanced configuration

| Type | Section | Parametr | Dscription |
|---|---|---|---|
| systems | root | name |   |
| systems | git | cred_id |   |
| systems | git | url |   |
| systems | git | branch |   |
| systems | git | work_branch_pref |   |
| systems | git | work_dir |   |
| systems | git | auto_recreate |   |
| systems | git | auto_pull |   |
| app | root | SECRET_KEY |   |
| app | root | CSRF |   |
| app | root | DEBUG |   |
| app | root | SESSION_COOKIE_SECURE |   |
| app | root | ENV |   |
| app | root | MAX_CONTENT_LENGTH |   |
| app | root | ALLOWED_FILE_EXTENSIONS |   |
| app | root | uploads_dir |   |
| app | root | repository_dir |   |
| app | loginig | log_dir |   |
| app | loginig | log_file_name |   |
| app | loginig | log_level |   |
| app | loginig | log_max_size |   |
| app | loginig | log_backup_count |   |
| app | git_settings | git_log_level |   |
| app | git_settings | git_user |   |
| app | git_settings | git_mail |   |
| app | creds | name |   |
| app | creds | login |   |
| app | creds | cred_file |   |
