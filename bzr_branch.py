"""This module contains a class that manipulate bazaar repositories
"""
import os
import logging

from bzrlib.plugin import load_plugins
load_plugins()
from bzrlib.branch import Branch


class BzrBranch(object):
    """This class provides manipulation of bazaar repositories using
    lists of config dictionaries. Each dictionary contains the following
    information of a git branch:
        path: Path of branch location, usually relative to a common
              origin
        revno: Branch revno
        type: Always 'bzr'.
        parent: Url of remote origin of the repository
    """
    def __init__(self):
        self.__info = None
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('bzr_branches')

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
                if lFile == '.bzr':
                    self.logger.info("Found a bzr branch %s", p)
                    info = {}
                    repo = Branch.open(path)
                    info.update({'path': path,
                                 'parent': str(repo.get_parent()),
                                 'revno': str(repo.revno()),
                                 'type': "bzr"})
                    res.append(info)
                    self.logger.debug("Branch collected")
                else:
                    r = self.get_branches(p)
                    if r:
                        res = res + r
        self.__info = res
        return self.__info
