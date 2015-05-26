import os
import logging

from bzrlib.plugin import load_plugins
load_plugins()
from bzrlib.branch import Branch

from lib.utils import name_from_url


class BzrBranch(object):

    def __init__(self):
        self.__info = None
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('bzr_branches')

    def get_branches(self, path):
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
                        #'master': path,
                        'revno': str(repo.revno()),
                        #'name': name_from_url(str(repo.remotes.origin.url)),
                        'type': "bzr"})
                    res.append(info)
                    self.logger.debug("Branch collected")
                else:
                    r = self.get_branches(p)
                    if r:
                        res = res + r
        self.__info = res
        return self.__info
