"""This module contains a class that manipulate git repositories
"""
import os
from git import Repo
import logging

from lib.utils import name_from_url
from lib.utils import clean_files


class GitBranch(object):
    """This class provides manipulation of git repositories using
    lists of config dictionaries. Each dictionary contains the following
    information of a git branch:
        path: Path of branch location, usually relative to a common
              origin
        name: Name of repository
        branch: Branch to be used
        commit: Hash of the commit pointed by HEAD
        is_dirty: Status of the branch
        depth: Depth of the cloned branch. False by default.
        type: Always 'git'.
        repo_url: Urls of remote origins of the repository
    """
    def __init__(self):
        self.__info = None
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('git_branches')

    def __get_branch(self, path):
        """Gets required information of a repository

        :param path: Path of .git directory
        :return: Config dictionary
        """
        info = {}
        try:
            repo = Repo(path)
            info.update({'path': str(os.path.dirname(path)),
                         'branch': str(repo.head.ref),
                         'commit': str(repo.head.reference.commit),
                         'is_dirty': repo.is_dirty(),
                         'name': name_from_url(str(repo.remotes[0].url)),
                         'depth': 1,
                         'type': "git"})
            urls = {}
            remotes = repo.remotes
            for each in remotes:
                urls.update({each.name: each.url})
            info.update({'repo_url': urls})
        except Exception as e:
            self.logger.error(e)
            return {0: str(e)}
        return info

    def update_info(self, path):
        """Updates information of the repositories' list

        :param path: Common path that contains the repositories
        """
        res = []
        for each in self.__info:
            path_dir = os.path.join(path, each['path'])
            path_branch = os.path.join(path_dir, ".git")
            branch = self.__get_branch(path_branch)
            if not branch.get(0, False):
                res.append(branch)
        self.__info = res

    def get_branches(self, path):
        """Gets information of all existing repositories in a
        directory

        :param path: Common path that contains the repositories
        :return: List of config dictionaries
        """
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
        """Clones a repository in the specified path

        :param path: Path where will be cloned the repository
        :param branch: Config dict of the repository
        """
        depth = branch.get('depth', False)
        url = branch['repo_url'].get('origin', branch['repo_url'].values()[0])
        repo = Repo.clone_from(url, os.path.join(path, branch['path']),
                               branch=branch['branch'], depth=depth)
        return repo

    def set_branch(self, branch, path):
        """Clones a single repository in the specified path with the
        specified configuration

        :param branch: Config dict of the repository
        :param path: Path where will be cloned the repo
        :return: Branch name if success, False otherwise
        """
        url = branch['repo_url'].get('origin',
                                     branch['repo_url'].values()[0])
        self.logger.debug("Cloning repo: %s - branch: %s - path: %s",
                          url, branch['branch'],
                          os.path.join(path, branch['path']))
        try:
            repo = self.__clone(path, branch)
            current_commit = str(repo.active_branch.commit)
            if branch['commit'] != current_commit:
                clean_files([os.path.join(path, branch['path'])])
                branch.update({'depth': False})
                repo = self.__clone(path, branch)
                try:
                    self.__reset(os.path.join(path, branch['path']),
                                 branch['commit'])
                except Exception as e:
                    self.logger.error(e)
            self.logger.info("Branch %s cloned", branch['path'])
            return branch['name']
        except Exception as e:
            self.logger.error(e)
            return False

    def set_branches(self, path):
        """Clones a list of repositories in the specified path with
        the specified configuration

        :param path: Path where will be cloned the repositories
        :return: List of config dictionaries
        """
        res = []
        if not os.path.exists(path):
            os.makedirs(path)
        for branch in self.__info:
            success = False
            path_dir = os.path.join(path, branch['path'])
            try:
                os.makedirs(os.path.dirname(path_dir))
            except:
                pass
            if os.path.basename(path_dir) in os.listdir(os.path.dirname(path_dir)):
                self.logger.debug(("Path %s already exists."
                                   " Checking for a git branch"),
                                  path_dir)
                branch_info = self.__get_branch(os.path.join(path_dir, ".git"))
                if not branch_info.get(0, False):
                    self.logger.info("Path %s is a git branch", path_dir)
                    if branch_info['commit'] == branch['commit']:
                        self.logger.info("Branch %s already configured",
                                         branch['name'])
                        res.append(branch['name'])
                        success = True
                    else:
                        self.logger.info("Branch %s points to wrong commit",
                                         branch['name'])
                        self.logger.debug("Resetting branch %s",
                                          branch['name'])
                        try:
                            self.__reset(path_dir, branch['commit'])
                            res.append(branch['name'])
                            success = True
                            self.logger.info("Branch %s reset", branch['name'])
                        except Exception as e:
                            self.logger.warn(e)
            if not success:
                if os.path.exists(os.path.abspath(path_dir)):
                    clean_files([os.path.abspath(path_dir)])
                result = self.set_branch(branch, path)
                if result:
                    res.append(result)
        return res

    def __update(self, path, branch):
        """Pulls in the repo the new information from the origin url

        :param path: Path of the repository to be pulled
        :param branch: Config dict of the repository
        """
        repo = Repo(path)
        repo.remotes[0].pull(branch)

    def update_branches(self, path, branches):
        """Pulls in the new information of a list of repositories, from
        their origin urls

        :param path: Common path of the repositories
        :param branches: List of repositories to be pulled
        :return: List of repositories succesfully pulled
        """
        branches_updated = []
        for branch in self.__info:
            if branch['name'] in branches:
                self.logger.debug("Pull from %s - branch %s",
                                  branch['repo_url'].values()[0],
                                  branch['branch'])
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
        """Resets a branch to the specified commit

        :param path: Path of the repository
        :param commit: Commit to be pointed
        """
        repo = Repo(path)
        repo.git.reset(commit, "--hard")

    def reset_branches(self, path, branches):
        """Resets a list of branches to the specified commits

        :param path: Common path of the repositories
        :param branches: List of branches to be reset
        :return: List of branches succesfully reset
        """
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
        """Loads list of config dictionaries of 'git' repositories

        :param info: List of config dictionaries to be loaded
        :return: List of config dictionaries
        """
        self.__info = []
        for branch in info:
            if branch['type'] == "git":
                self.__info.append(branch)
        return self.__info

    def get_info(self):
        """Gives the information of the list of config dictionaries

        :return: List of config dictionaries
        """
        return self.__info
