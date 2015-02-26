#!/usr/bin/python
# -*- coding: utf-8 -*-
""" This script loads branches information to a Json file
and reconstruct branches from such files
"""

import os
import subprocess
from git import Repo
import json
import logging
import argparse

from lib.utils import simplify_path
from lib.utils import name_from_url

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('info_branchs')

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--json_file", help="Json file to use", required=True)
parser.add_argument("-p", "--path",
                    help="Path of GIT Repo, actual dir by default",
                    default=False)
parser.add_argument("--repo", help="Comma separated list of repositories",
                    default=None)
action = parser.add_mutually_exclusive_group(required=True)
action.add_argument("-s", "--save", help="Create Json file from Repo",
                    action="store_true")
action.add_argument("-l", "--load", help="Reconstruct Repo from Json file",
                    action="store_true")
action.add_argument("-u", "--update", help="Update a list of repositories",
                    action="store_true")

args = parser.parse_args()
filename = args.json_file
path = args.path
if not path:
    path = os.getcwd()
if args.repo:
    branches = args.repo.split(',')
save = args.save
load = args.load
update = args.update


def get_all_branches_info(path):
    """This function get branches info and saves it in a list of dict

    :param path: Path of directory to be inspected
    :return: List of dictionaries
    """
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
                    'is_dirty': repo.is_dirty(),
                    'name': name_from_url(str(repo.remotes.origin.url)),
                    'depth': 1})
                res.append(info)
                logger.info("Branch collected")
            else:
                r = get_all_branches_info(p)
                if r:
                    res = res + r
    return res


def save_branches_info(info, json_file):
    """This function dumps branches' info into a Json file

    :param info: List of dictionaries with branches' info
    :param json_file: File where info will be

    :return: Absolute path of Json file
    """
    logger.debug("Opening file %s", json_file)
    with open(json_file, 'w') as fout:
        logger.info("Dumping branches into file: %s", json_file)
        json.dump(info, fout, sort_keys=True, indent=4, ensure_ascii=False,
                  separators=(',', ':'))
        if not os.path.isabs(json_file):
            json_file = os.path.abspath(json_file)
        logger.info("Branches dumped")
        return json_file


def load_branches(json_file):
    """This function loads branches' info from a Json file and dumps it
    into a list of dictionaries

    :param filename: File to be loaded
    :return: List of dictionaries
    """
    logger.debug("Opening file %s", json_file)
    with open(json_file, "r") as f:
        logger.info("Loading branches from file %s", json_file)
        repo_dict = json.load(f)
    logger.info("Branches loaded")
    return repo_dict


def set_branches(info):
    """This function builds branches using settings from a list of dictionaries

    :param info: List of dictionaries containing branches' info
    """
    logger.info("Cloning branches...")
    for branch in info:
        logger.debug("Cloning repo: %s - branch: %s - path: %s",
                     branch['repo_url'], branch['branch'],
                     os.path.join(path, branch['path']))
        depth = branch.get('depth', False)
        try:
            repo = Repo.clone_from(branch['repo_url'],
                                   os.path.join(path, branch['path']),
                                   branch=branch['branch'], depth=depth)
            logger.info("Branch %s cloned", branch['path'])
        except Exception as e:
            logger.error(e)


def update_branches(info, branches):
    """This function executes GIT PULL to listed repositories

    :param info: List of dictionaries containing branches' info
    :param branches: List of branches to be updated
    """
    logger.info("Updating branches...")
    for branch in info:
        if branch['name'] in branches:
            logger.debug("Repo %s FOUND", branch['name'])
            logger.debug("Pull from %s - branch %s", branch['repo_url'],
                         branch['branch'])
            repo = Repo(os.path.join(path, branch['path']))
            repo.remotes.origin.pull()
            logger.info("Repo %s updated", branch['name'])
            branches.remove(branch['name'])
    for name in branches:
        logger.warning("Repo %s NOT FOUND", name)


if __name__ == '__main__':
    if save:
        b_info = get_all_branches_info(path)
        b_info = simplify_path(b_info)
        save_branches_info(b_info, filename)
    if load:
        b_info = load_branches(filename)
        set_branches(b_info)
    if update:
        b_info = load_branches(filename)
        update_branches(b_info, branches)

    #_apply_recursive('/home/truiz/working/backupws')