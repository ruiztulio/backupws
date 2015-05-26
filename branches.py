#!/usr/bin/python
# -*- coding: utf-8 -*-
""" This script loads branches information to a Json file
and reconstruct branches from such files
"""

import os
import subprocess
from git_branch import GitBranch
import logging
import argparse

from lib.utils import simplify_path
from lib.utils import name_from_url
from lib.utils import save_json
from lib.utils import load_json

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('info_branches')

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
action.add_argument("-r", "--reset",
                    help="Resets HARD all branches to commits from Json file",
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
reset = args.reset


def get_all_branches_info(branch, path):
    """This function get branches info and saves it in a list of dict

    :param path: Path of directory to be inspected
    :return: List of dictionaries
    """
    logger.info("Colleting branches in %s", path)
    res = branch.get_branches(path)
    logger.info("Branches collected")
    return res


def save_branches_info(info, json_file):
    """This function dumps branches' info into a Json file

    :param info: List of dictionaries with branches' info
    :param json_file: File where info will be

    :return: Absolute path of Json file
    """
    logger.info("Dumping branches into file: %s", json_file)
    json_file = save_json(info, json_file)
    logger.info("Branches dumped")
    return json_file


def load_branches(json_file):
    """This function loads branches' info from a Json file and dumps it
    into a list of dictionaries

    :param filename: File to be loaded
    :return: List of dictionaries
    """
    logger.info("Loading branches from file %s", json_file)
    repo_dict = load_json(json_file)
    logger.info("Branches loaded")
    return repo_dict


def set_branches(branch):
    """This function builds branches using settings from a list of dictionaries

    :param info: List of dictionaries containing branches' info
    """
    logger.info("Cloning branches")
    branch.set_branches(path)
    logger.info("Branches cloned")


def update_branches(branch, info, branches):
    """This function executes GIT PULL to listed repositories

    :param info: List of dictionaries containing branches' info
    :param branches: List of branches to be updated
    """
    logger.info("Updating branches...")
    success = branch.update_branches(path, info, branches)
    for name in branches:
        if name not in success:
            logger.warning("Repo %s NOT UPDATED", name)


def reset_branches(branch, info, branches):
    """This function resets hardly all branches to the commits specified in
    dicts info

    :param info: List of dictionaries containing branches' info
    :param branches: List of branches to be reset
    """
    logger.info("Resetting branches...")
    success = branch.reset_branches(path, info, branches)
    for name in branches:
        if name not in success:
            logger.warning("Repo %s NOT RESET", name)


if __name__ == '__main__':
    gitbranch = GitBranch()
    if save:
        b_info = get_all_branches_info(gitbranch, path)
        b_info = simplify_path(b_info)
        save_branches_info(b_info, filename)
    if load:
        gitbranch.set_info(load_branches(filename))
        set_branches(gitbranch)
    if update:
        b_info = load_branches(filename)
        update_branches(gitbranch, b_info, branches)
    if reset:
        b_info = load_branches(filename)
        reset_branches(gitbranch, b_info, branches)

    #_apply_recursive('/home/truiz/working/backupws')