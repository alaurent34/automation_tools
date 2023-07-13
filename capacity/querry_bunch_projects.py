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
APP_URL = 'http://173.176.178.92:65060/api/fetchProjectData'


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


def get_restrictions(project_name: str,
                     url: str) -> dict:
    """
    doc
    """

    data = {'projectName': project_name}

    restriction = requests.post(url, json=data)

    try:
        restriction = json.loads(restriction.text)
    except:
        print('1')
        print(restriction.text)
        restriction = {}

    return restriction


def save_capacity(project_name: str, capacity_array: dict):
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

    capacities = map(get_restrictions, projects_list,
                     itertools.repeat(APP_URL))

    list(map(save_capacity, projects_list, capacities))


if __name__ == "__main__":
    main()
