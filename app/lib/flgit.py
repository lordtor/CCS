import os.path
from git import *
import git, os, shutil
from datetime import datetime
import logging
from logging.config import dictConfig
from json import dumps
import colors

def read_file(file_path):
    with open(file_path, 'r') as file:
        data = file.read().replace('\n', '')
        file.close()
    return data

class git_operation():

    def __init__(self, git_config):
        self.gc = git_config
        self.gc['REMOTE_URL'] = "{}//{}:{}@{}".format(
            git_config["url"].split("//")[0],
            git_config["cred_id"]["login"], 
            read_file(git_config["cred_id"]["cred_file"]),
            git_config["url"].split("//")[1])
        logging.config.dictConfig(self.gc["log_conf"])
        self.logger = logging.getLogger("GIT")
        
    def clone(self, branch=None):
        try:
            if branch == None:
                branch = self.gc['branch']
            cloned = False
            if os.path.exists( self.gc['DIR_NAME']) and  self.gc['auto_recreate']:
                if os.path.isdir( self.gc['DIR_NAME']):
                    self.logger.debug(colors.color("{}".format("EXISTING CLEAN"), fg="red"))
                    shutil.rmtree( self.gc['DIR_NAME'])
                    status = "Recreate"
                os.makedirs( self.gc['DIR_NAME'])
                repo = Repo.clone_from( self.gc['REMOTE_URL'], self.gc['DIR_NAME'],branch=branch)
                cloned = True
            elif not os.path.exists( self.gc['DIR_NAME']):
                self.logger.debug(colors.color("{}".format("NOT EXISTING"), fg="red"))
                status = "New"
                os.makedirs( self.gc['DIR_NAME'])
                repo = Repo.clone_from( self.gc['REMOTE_URL'], self.gc['DIR_NAME'],branch=branch)
                cloned = True
            elif os.path.exists( self.gc['DIR_NAME']) and not self.gc['auto_recreate']:
                repo = git.Repo.init( self.gc['DIR_NAME'])
                origin = repo.remotes['origin']
                self.fetch()
                if self.gc['auto_pull']:
                    origin.pull(origin.refs[0].remote_head)
                    status = "Updated"
                status = "Not updated"
                cloned = False
            else:
                self.logger.error("Repo not cloned")
            log = {
                    "type": "Clone repository",
                    "recreate":  self.gc['auto_recreate'],
                    "repository":  self.gc['DIR_NAME'],
                    "url":  self.gc['REMOTE_URL'],
                    "status": status,
                    "cloned": cloned
                }
            self.logger.info(dumps(log, indent=4))
        except Exception as e:
            self.logger.error(str(e))
    def fetch(self):
        try:
            repo = git.Repo.init( self.gc['DIR_NAME'])
            origin = repo.remotes['origin']
            origin.fetch()
            log = {
                "type": "Fetch repository",
                "repository":  self.gc['DIR_NAME']
            }
            self.logger.info(dumps(log, indent=4))
            return True
        except Exception as e:
            self.logger.error(str(e))
    def push(self, commit=None, branch=None):
        try:
            if branch is None:
                branch = self.gc['branch']
            repo = Repo( self.gc['DIR_NAME'])
            origin = repo.remote('origin')
            origin.push(branch)
            #repo.git.add(update=True)
            log = {
                "type": "Push repository",
                "branch": branch,
                "repository":  self.gc['DIR_NAME']
            }
            self.logger.info(dumps(log, indent=4))
            return True
        except Exception as e:
            self.logger.error(str(e))
    def pull(self, branch=None):
        try:
            if branch == None:
                branch = self.gc['branch']
            repo = Repo( self.gc['DIR_NAME'])
            repo.remotes.origin.pull(branch)
            log = {
                "type": "Pull repository",
                "branch": branch,
                "repository":  self.gc['DIR_NAME']
            }
            self.logger.info(dumps(log, indent=4))
            return True
        except Exception as e:
            self.logger.error(str(e))
    def add(self, files):
        try:
            repo = Repo( self.gc['DIR_NAME'])
            repo.index.add(files)
            log = {
                "type": "Add files",
                "repository":  self.gc['DIR_NAME'],
                "files": files,
            }
            self.logger.info(dumps(log, indent=4))
            return True
        except Exception as e:
            self.logger.error(str(e))
    def commit(self, message=None):
        try:
            if message == None:
                message = "Auto commit at {}".format(str(datetime.now()).split('.')[0].replace(' ','_').replace(':','_'))
            repo = Repo( self.gc['DIR_NAME'])
            repo.index.commit(message)
            log = {
                "type": "Commit",
                "repository":  self.gc['DIR_NAME'],
                "commit_message": message
            }
            self.logger.info(dumps(log, indent=4))
            return True
        except Exception as e:
            self.logger.error(str(e))
    def list_remotes(self):
        try:
            repo = Repo( self.gc['DIR_NAME'])
            remotes = []
            for remote in repo.remotes:
                print(f'- {remote.name} {remote.url}')
                remotes.append(f'- {remote.name} {remote.url}')
            return remotes
        except Exception as e:
            self.logger.error(str(e))
    def check_changes(self):
        try:
            #self.logger.info('Check changes for folder:{}'.format( self.gc['DIR_NAME']))
            repo = Repo( self.gc['DIR_NAME'])
            self.fetch()

            changed = [ item.a_path for item in repo.index.diff(None) ]
            if self.gc['DIR_NAME'] in repo.untracked_files:
                return 'Untracked'
            elif self.gc['DIR_NAME'] in changed:
                return 'Modified'
            else:
                return "Don't care"



            # if repo.is_dirty(untracked_files=True):
            #     self.logger.info('Changes detected.')
            #     return True
            # else:
            #     self.logger.info('Changes not detected.')
            #     return False
        except Exception as e:
            self.logger.error(str(e))
    def head_reset(self):
        try:
            repo = Repo( self.gc['DIR_NAME'])
            repo.head.reset(index=True, working_tree=True)
            return True
        except Exception as e:
            self.logger.error(str(e))
    def list_diff_changes(self):
        try:
            repo = Repo( self.gc['DIR_NAME'])
            diff = repo.git.diff(repo.head.commit.tree)
            changedFiles = [ item.a_path for item in repo.index.diff(None) ]
            self.logger.debug(colors.color("{}".format(changedFiles), fg="red"))
            
            logging.info(diff)
            un =  repo.untracked_files
            log = {
                "type": "Diff",
                "changed_files": changedFiles,
                "diff": diff,
                "repository":  self.gc['DIR_NAME'],
                "untracked_files": un
            }
            self.logger.info(repo.untracked_files)
            return {"diff": diff,  "changed_files": changedFiles, "untracked_files": un}
        except Exception as e:
                self.logger.error(str(e))
    def config_user(self):
        try:
            repo = Repo( self.gc['DIR_NAME'])
            with repo.config_writer() as git_config:
                git_config.set_value('user', 'email', self.gc['sys_user']['mail'])
                git_config.set_value('user', 'name', self.gc['sys_user']['user'])
                self.logger.info("Set git user: {} and git mail: {}".format(self.gc['sys_user']['user'], self.gc['sys_user']['mail']))
        except Exception as e:
            self.logger.error(str(e))
    def list_branch(self):
        try:
            repo = Repo( self.gc['DIR_NAME'])
            self.logger.info('Branch list:')
            branches = []
            for branch in repo.branches:
                branches.append(branch)
                self.logger.info(branch)
            return branches
        except Exception as e:
            self.logger.error(str(e))
    def branch_new (self, name=None, pref=None):
        try:
            repo = Repo( self.gc['DIR_NAME'])
            if name is None:
                if pref is None:
                    name = 'branch-'+str(datetime.now()).split('.')[0].replace(' ','_').replace(':','_')
                else:
                    name = pref+'-'+str(datetime.now()).split('.')[0].replace(' ','_').replace(':','_')
            # Create a new branch
            repo.git.branch(name)
            # You need to check out the branch after creating it if you want to use it
            self.checkout(branch=name)
            self.logger.info('New branch name is: {}'.format(name))
            return name
        except Exception as e:
            self.logger.error(str(e))
    def checkout (self, branch):
        try:
            repo = git.Repo.init( self.gc['DIR_NAME'])
            repo.git.checkout(branch)
            self.logger.info('Current branch name is: {}'.format(branch))
        except Exception as e:
            self.logger.error(str(e))
