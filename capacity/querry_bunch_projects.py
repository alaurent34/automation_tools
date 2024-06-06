 # -*- coding: utf-8 -*-
"""
File: querry_bunch_projects.py
Author: Antoine Laurent
Email: alaurent@agencemobilitedurable.ca
Github: https://github.com/alaurent34
Description:
"""

import argparse
import itertools
import json
import os
import re
import requests
import sys
import unicodedata

from unidecode import unidecode

# APP CONFIG
APP_URL = 'https://curbsn.app/'
API_FETCH = 'api/fetchProjectData'
API_CONNECT = 'api/login'


def parse_args() -> argparse.Namespace:
    """
    Argument parser for the script

    Return
    ------
    argparse.Namespace
        Parsed command line arguments
    """
    # Initialize parser
    parser = argparse.ArgumentParser(
            description="This script provide an automation to batch querry" +
                        " projects from the capacity app."
            )

    # Adding optional argument
    parser.add_argument("projects_list", metavar='Project list', type=str,
                        nargs='*', default=[],
                        help="List of project names to querry.")
    parser.add_argument('-u', '--user', type=str, default=None,
                        help='User name')
    parser.add_argument('-p', '--pwd', type=str, default=None,
                        help='Password')
    parser.add_argument('-k', '--api-key', type=str, default=None, help='API key')
    parser.add_argument('-o', '--output', type=str, nargs='*', default=[],
                        help='Output name')
    # Read arguments from command line
    args = parser.parse_args()

    if not sys.stdin.isatty():
        args.projects_list.extend(sys.stdin.read().splitlines())

    return args

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = (unicodedata.normalize('NFKD', value)
                            .encode('ascii', 'ignore')
                            .decode('ascii'))
        value = re.sub(r'[^\w\s-]', '', value.lower())

    return re.sub(r'[-\s]+', '-', value).strip('-_')


def connect(url, user, password) -> requests.Session:

    login_data = {'username': user, 'password': password}

    session = requests.Session()
    session.post(url, data=login_data, timeout=600)

    return session

def get_restrictions(project_name: str,
                     url: str, active_session: str = None,
                     key: str = None) -> dict:
    """
    doc
    """

    data = {'projectId': project_name}

    if key:
        data['apiKey'] = key

    if active_session:
        restriction = active_session.post(url, json=data, timeout=600)
    else:
        restriction = requests.post(url, json=data, timeout=600)

    try:
        restriction = json.loads(restriction.text)
    except:
        print('1')
        print(restriction.text)
        restriction = {}

    return restriction


def save_restrictions(project_name: str, capacity_array: dict):
    """TODO: Docstring for save_capacity.

    Parameters
    ----------
    project_name: str
        Name of the project

    """

    os.makedirs("./output/", exist_ok=True)

    with open("output/" + slugify(unidecode(project_name)) + "_capacity_array.json", 'w+') as f:
        json.dump(capacity_array, f)


def main():
    """TODO: Docstring for main.

    """
    config = parse_args()

    projects_list = config.projects_list

    user = config.user
    password = config.pwd
    key = config.api_key

    if user and password:
        session = connect(url=APP_URL+API_CONNECT, user=user, password=password) if user else None

        capacities = map(get_restrictions, projects_list,
                         itertools.repeat(APP_URL+API_FETCH),
                         itertools.repeat(session))
    elif key:
        capacities = map(get_restrictions, projects_list,
                         itertools.repeat(APP_URL+API_FETCH),
                         itertools.repeat(None),
                         itertools.repeat(key))

    else:
        print('No identification given. Quitting.')
        sys.exit(2)

    # save
    if config.output:
        projects_list=config.output

    list(map(save_restrictions, projects_list, capacities))


if __name__ == "__main__":
    main()
