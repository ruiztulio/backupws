import os
from git import Repo
import logging

from lib.utils import name_from_url


class GitBranch(object):

    def __init__(self):
        self.__info = None
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('git_branches')

    def __get_branch(self, path):
        info = {}
        try:
            repo = Repo(path)
            info.update({'path': str(os.path.dirname(path)),
                         'repo_url': str(repo.remotes.origin.url),
                         'branch': str(repo.head.ref),
                         'commit': str(repo.head.reference.commit),
                         'is_dirty': repo.is_dirty(),
                         'name': name_from_url(str(repo.remotes.origin.url)),
                         'depth': 1,
                         'type': "git"})
        except Exception as e:
            return {0: str(e)}
        return info

    def update_info(self, path):
        res = []
        for each in self.__info:
            path_dir = os.path.join(path, each['path'])
            path_branch = os.path.join(path_dir, ".git")
            branch = self.__get_branch(path_branch)
            if not branch.get(0, False):
                res.append(branch)
        self.__info = res

    def get_branches(self, path):
        res = []
        for lFile in os.listdir(path):
            p = os.path.join(path, lFile)
            if os.path.isdir(p) \
                    and lFile not in ['.', '..'] \
                    and not os.path.islink(p):
                if lFile == '.git':
                    self.logger.info("Found a git branch %s", path)
                    res.append(self.__get_branch(p))
                    self.logger.debug("Branch collected")
                else:
                    r = self.get_branches(p)
                    if r:
                        res = res + r
        self.__info = res
        return self.__info

    def __clone(self, path, branch):
        depth = branch.get('depth', False)
        repo = Repo.clone_from(branch['repo_url'],
                               os.path.join(path, branch['path']),
                               branch=branch['branch'], depth=depth)
        return repo

    def set_branches(self, path):
        res = []
        for branch in self.__info:
            self.logger.debug("Cloning repo: %s - branch: %s - path: %s",
                              branch['repo_url'], branch['branch'],
                              os.path.join(path, branch['path']))
            try:
                repo = self.__clone(path, branch)
                self.logger.info("Branch %s cloned", branch['path'])
                res.append(branch['name'])
            except Exception as e:
                self.logger.error(e)
        return res

    def __update(self, path, branch):
        repo = Repo(path)
        repo.remotes.origin.pull(branch)

    def update_branches(self, path, branches):
        branches_updated = []
        for branch in self.__info:
            if branch['name'] in branches:
                self.logger.debug("Pull from %s - branch %s",
                                  branch['repo_url'], branch['branch'])
                try:
                    self.__update(os.path.join(path, branch['path']),
                                  branch['branch'])
                    self.logger.info("Repo %s updated", branch['name'])
                    branches_updated.append(branch['name'])
                except Exception as e:
                    self.logger.error(e)
        self.update_info(path)
        return branches_updated

    def __reset(self, path, commit):
        repo = Repo(path)
        repo.git.reset(commit, "--hard")

    def reset_branches(self, path, branches):
        branches_reset = []
        for branch in self.__info:
            if branch['name'] in branches:
                try:
                    self.logger.debug("Resetting branch %s to commit %s",
                                      branch['name'], branch['commit'])
                    self.__reset(os.path.join(path, branch['path']),
                                 branch['commit'])
                    self.logger.info("Branch %s reset", branch['name'])
                    branches_reset.append(branch['name'])
                except Exception as e:
                    self.logger.error(e)
        self.update_info(path)
        return branches_reset

    def set_info(self, info):
        self.__info = []
        for branch in info:
            if branch['type'] == "git":
                self.__info.append(branch)
        return self.__info

    def get_info(self):
        return self.__info
