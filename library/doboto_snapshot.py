#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import copy
from ansible.module_utils.basic import AnsibleModule
from doboto.DO import DO
from doboto.DOBOTOException import DOBOTOException

"""

Ansible module to manage DigitalOcean snapshots
(c) 2017, SWE Data <swe-data@do.co>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: doboto_snapshot

short_description: Manage DigitalOcean snapshots
description:
    - Manages DigitalOcean Snapshots
version_added: "0.1"
author: "SWE Data <swe-data@do.co>"
options:
    token:
        description:
            - token to use to connect to the API (uses DO_API_TOKEN from ENV if not found)
    action:
        snapshot action
        choices:
            - list
            - info
            - destroy
    id:
        description:
            - same as DO API variable (snapshot id)
    resource_type:
        description:
            - same as DO API variable
    url:
        description:
            - URL to use if not official (for experimenting)

'''

EXAMPLES = '''
'''


def require(*required):
    def requirer(function):
        def wrapper(*args, **kwargs):
            params = required
            if not isinstance(params, tuple):
                params = (params,)
            met = False
            for param in params:
                if args[0].module.params[param] is not None:
                    met = True
            if not met:
                args[0].module.fail_json(msg="the %s parameter is required" % " or ".join(params))
            function(*args, **kwargs)
        return wrapper
    return requirer


class Snapshot(object):

    url = "https://api.digitalocean.com/v2"

    def __init__(self):

        self.module = self.input()

        token = self.module.params["token"]

        if token is None:
            token = os.environ.get('DO_API_TOKEN', None)

        if token is None:
            self.module.fail_json(msg="the token parameter is required")

        self.do = DO(url=self.module.params["url"], token=token)

        self.act()

    def input(self):

        return AnsibleModule(argument_spec=dict(
            action=dict(default=None, required=True, choices=[
                "info",
                "list",
                "destroy"
            ]),
            token=dict(default=None),
            id=dict(default=None),
            resource_type=dict(default=None),
            url=dict(default=self.url)
        ))

    def act(self):
        try:
            getattr(self, self.module.params["action"])()
        except DOBOTOException as exception:
            self.module.fail_json(msg=exception.message, result=exception.result)

    def list(self):
        self.module.exit_json(changed=False, snapshots=self.do.snapshot.list(
            resource_type=self.module.params["resource_type"]
        ))

    @require("id")
    def info(self):
        self.module.exit_json(changed=False, snapshot=self.do.snapshot.info(
            id=self.module.params["id"]
        ))

    @require("id")
    def destroy(self):
        self.module.exit_json(changed=True, result=self.do.snapshot.destroy(
            id=self.module.params["id"]
        ))


Snapshot()
