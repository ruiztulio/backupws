#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
from git import Repo
import json
import logging

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('info_branchs')

def get_all_branches_info(path):
    res = []
    for lFile in os.listdir(path):
        p = os.path.join(path, lFile)
        if os.path.isdir(p) \
                and lFile not in ['.', '..'] \
                and not os.path.islink(p):
            if lFile == '.git':
                logger.debug("Found a git folder %s", p)
                info = {}
                repo = Repo(p)
                info.update({'path': path,
                    'repo_url': str(repo.remotes.origin.url),
                    'branch': str(repo.head.ref),
                    'commit': str(repo.head.reference.commit),
                    'is_dirty': repo.is_dirty()})
                res.append(info)
            else:
                r = get_all_branches_info(p)
                if r:
                    res = res + r
    return res

if __name__ == '__main__':
    b_info = get_all_branches_info('/home/truiz/working/lodigroup/instance_as_prod')
    with open('branches_info.txt', 'w') as fout:
        json.dump(b_info, fout, sort_keys=True, indent=4, ensure_ascii=False)

    #_apply_recursive('/home/truiz/working/backupws')