#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import copy
from ansible.module_utils.basic import AnsibleModule
from doboto.DO import DO


"""

Ansible module to manage DigitalOcean tags
(c) 2017, Gaffer Fitch <gfitch@digitalocean.com>

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
module: doboto_tag

short_description: Manage DigitalOcean Tags
description:
    - Manages DigitalOcean tags
version_added: "0.1"
author: "Gaffer Fitch <gfitch@digitalocean.com>"
options:
    token:
        description:
            - token to use to connect to the API (uses DO_API_TOKEN from ENV if not found)
    action:
        ssh key action
        choices:
            - create
            - present
            - info
            - list
            - update
            - attach
            - detach
            - destroy
    name:
        description:
            - same as DO API variable
    new_name:
        description:
            - same as DO API variable, new name for updating
    resources:
        description:
            - same as DO API variable
    resource_type:
        description:
            - same as DO API variable, use if doing a single resource type
    resource_id:
        description:
            - same as DO API variable, use if doing a single resource id
    resource_ids:
        description:
            - paired with a single resource_type to build a resources list
    url:
        description:
            - URL to use if not official (for experimenting)
'''

EXAMPLES = '''
'''


class Tag(object):

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
                "create",
                "present",
                "info",
                "list",
                "update",
                "attach",
                "detach",
                "destroy"
            ]),
            token=dict(default=None),
            name=dict(default=None),
            new_name=dict(default=None),
            resources=dict(default=None, type='list'),
            resource_type=dict(default=None),
            resource_id=dict(default=None),
            resource_ids=dict(default=None, type='list'),
            url=dict(default=self.url),
        ))

    def act(self):

        getattr(self, self.module.params["action"])()

    def create(self):

        if self.module.params["name"] is None:
            self.module.fail_json(msg="the name parameter is required")

        result = self.do.tag.create(self.module.params["name"])

        if "tag" not in result:
            self.module.fail_json(msg="DO API error", result=result)

        self.module.exit_json(changed=True, tag=result['tag'])

    def present(self):

        if self.module.params["name"] is None:
            self.module.fail_json(msg="the name parameter is required")

        result = self.do.tag.list()

        if "tags" not in result:
            self.module.fail_json(msg="DO API error", result=result)

        tags = result["tags"]

        existing = None
        for tag in tags:
            if self.module.params["name"] == tag["name"]:
                existing = tag
                break

        if existing is not None:
            self.module.exit_json(changed=False, tag=existing)
        else:
            self.create()

    def info(self):

        result = None

        if self.module.params["name"] is None:
            self.module.fail_json(msg="the name parameter is required")

        result = self.do.tag.info(self.module.params["name"])

        if "tag" not in result:
            self.module.fail_json(msg="DO API error", result=result)

        self.module.exit_json(changed=False, tag=result['tag'])

    def list(self):

        result = self.do.tag.list()

        if "tags" not in result:
            self.module.fail_json(msg="DO API error", result=result)

        self.module.exit_json(changed=False, tags=result["tags"])

    def names(self):

        result = self.do.tag.names()

        if "tags" not in result:
            self.module.fail_json(msg="DO API error", result=result)

        self.module.exit_json(changed=False, tags=result["tags"])

    def update(self):

        result = None

        if self.module.params["name"] is None:
            self.module.fail_json(msg="the name parameter is required")

        if self.module.params["new_name"] is None:
            self.module.fail_json(msg="the new_name parameter is required")

        result = self.do.tag.update(self.module.params["name"], self.module.params["new_name"])

        if "tag" not in result:
            self.module.fail_json(msg="DO API error", result=result)

        self.module.exit_json(changed=True, tag=result['tag'])

    def build(self):

        resources = []

        if self.module.params["resource_type"] is not None and \
           self.module.params["resource_id"] is not None:
            resources.append({
                "resource_type": self.module.params["resource_type"],
                "resource_id": self.module.params["resource_id"]
            })

        if self.module.params["resource_type"] is not None and \
           self.module.params["resource_ids"] is not None:
            for resource_id in self.module.params["resource_ids"]:
                resources.append({
                    "resource_type": self.module.params["resource_type"],
                    "resource_id": resource_id
                })

        if self.module.params["resources"] is not None:
            resources.extend(copy.deepcopy(self.module.params["resources"]))

        return resources

    def attach(self):

        result = None

        if self.module.params["name"] is None:
            self.module.fail_json(msg="the name parameter is required")

        resources = self.build()

        if not resources:
            self.module.fail_json(
                msg="the resources or resource_type and resource_id(s) parameters are required"
            )

        result = self.do.tag.attach(self.module.params["name"], resources)

        if "status" not in result:
            self.module.fail_json(msg="DO API error", result=result)

        self.module.exit_json(changed=True, result=result)

    def detach(self):

        result = None

        if self.module.params["name"] is None:
            self.module.fail_json(msg="the name parameter is required")

        resources = self.build()

        if not resources:
            self.module.fail_json(
                msg="the resources or resource_type and resource_id(s) parameters are required"
            )

        result = self.do.tag.detach(self.module.params["name"], resources)

        if "status" not in result:
            self.module.fail_json(msg="DO API error", result=result)

        self.module.exit_json(changed=True, result=result)

    def destroy(self):

        result = None

        if self.module.params["name"] is None:
            self.module.fail_json(msg="the name parameter is required")

        result = self.do.tag.destroy(self.module.params["name"])

        if "status" not in result:
            self.module.fail_json(msg="DO API error", result=result)

        self.module.exit_json(changed=True, result=result)

Tag()