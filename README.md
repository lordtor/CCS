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

| Type   | Section   | Parametr   | Dscription |
|---|---|---|---|
| systems   | root   | name   |   |
| systems   | git   | cred\_id   |   |
| systems   | git   | url   |   |
| systems   | git   | branch   |   |
| systems   | git   | work\_branch\_pref   |   |
| systems   | git   | work\_dir   |   |
| systems   | git   | auto\_recreate   |   |
| systems   | git   | auto\_pull   |   |
| app   | root   | SECRET\_KEY   |   |
| app   | root   | CSRF   |   |
| app   | root   | DEBUG   |   |
| app   | root   | SESSION\_COOKIE\_SECURE   |   |
| app   | root   | ENV   |   |
| app   | root   | MAX\_CONTENT\_LENGTH   |   |
| app   | root   | ALLOWED\_FILE\_EXTENSIONS   |   |
| app   | root   | uploads\_dir   |   |
| app   | root   | repository\_dir   |   |
| app   | loginig   | log\_dir   |   |
| app   | loginig   | log\_file\_name   |   |
| app   | loginig   | log\_level   |   |
| app   | loginig   | log\_max\_size   |   |
| app   | loginig   | log\_backup\_count   |   |
| app   | git\_settings   | git\_log\_level   |   |
| app   | git\_settings   | git\_user   |   |
| app   | git\_settings   | git\_mail   |   |
| app   | creds   | name   |   |
| app   | creds   | login   |   |
| app   | creds   | cred\_file   |   |
