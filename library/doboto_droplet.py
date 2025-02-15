#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import copy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.doboto_module import require, DOBOTOModule

"""
Ansible module to manage DigitalOcean droplets
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
module: doboto_droplet

short_description: Manage DigitalOcean droplets
description: Manages DigitalOcean droplets
version_added: "0.1"
author: "SWE Data <swe-data@do.co>"
options:
    token:
        description: token to use to connect to the API (uses DO_API_TOKEN from ENV if not found)
    action:
        description: droplet action
        choices:
            - list
            - neighbor_list
            - droplet_neighbor_list
            - create
            - present
            - info
            - destroy
            - backup_list
            - backup_enable
            - backup_disable
            - reboot
            - shutdown
            - power_on
            - power_off
            - power_cycle
            - restore
            - password_reset
            - resize
            - rebuild
            - rename
            - kernel_list
            - kernel_update
            - ipv6_enable
            - private_networking_enable
            - snapshot_list
            - snapshot_create
            - action_list
            - action_info

    id:
        description: same as DO API variable (droplet id)
    name:
        description: same as DO API variable (for single create)
    names:
        description: same as DO API variable (for mass create)
    region:
        description: same as DO API variable
    size:
        description: same as DO API variable
    disk:
        description: same as DO API variable
    image:
        description: same as DO API variable
    kernel:
        description: same as DO API variable
    ssh_keys:
        description: same as DO API variable (if single value, converted to array)
    backups:
        description: same as DO API variable
    ipv6:
        description: same as DO API variable
    private_networking:
        description: same as DO API variable
    user_data:
        description: same as DO API variable
    monitoring:
        description: same as DO API variable
    volume:
        description: same as DO API variable (if single value, converted to array)
    tags:
        description: same as DO API variable (if single value, converted to array)
    tag_name:
        description: same as DO API variable (for tag ID)
    snapshot_name:
        description: name of the snapshot
    wait:
        description: wait until tasks has completed before continuing
    poll:
        description: poll value to check while waiting (default 5 seconds)
    timeout:
        description: timeout value to give up after waiting (default 300 seconds)
    action_id:
        description: same as DO API variable (action id)
    url:
        description: URL to use if not official (for experimenting)
    extra:
        description: key / value of extra values to send (for experimenting)

'''

EXAMPLES = '''
- name: droplet | create | simple
  doboto_droplet:
    action: create
    name: droplet-create
    region: nyc3
    size: 1gb
    image: debian-7-0-x64
  register: droplet_create

- name: droplet | create | multiple
  doboto_droplet:
    action: create
    names:
      - droplet-create-01
      - droplet-create-02
      - droplet-create-03
    region: nyc3
    size: 1gb
    image: ubuntu-14-04-x64
  register: droplets_create

- name: droplet | ssh_key | file
  command: ssh-keygen -t rsa -P "" -C "doboto@digitalocean.com" -f /tmp/id_doboto

- name: droplet | ssh_key | create
  doboto_ssh_key:
    action: create
    name: droplet-ssh-key
    public_key: "{{ lookup('file', '/tmp/id_doboto.pub') }}"
  register: droplet_ssh_key

- name: droplet | present | complex | new
  doboto_droplet:
    action: present
    name: droplet-present
    region: nyc3
    size: 2gb
    image: ubuntu-14-04-x64
    ssh_keys: "{{ droplet_ssh_key.ssh_key.id }}"
    backups: true
    ipv6: true
    private_networking: true
    user_data: "stuff"
    tags: one
    wait: true
  register: droplet_present_new

- name: droplet | present | complex | public ipv4 address
  debug:
    msg: "{{droplet_present_new|json_query(public_ipv4_query)}}"
  vars:
    public_ipv4_query: "droplet.networks.v4[?type=='public'].ip_address | [0]"

- name: droplet | present | complex | private ipv4 address
  debug:
    msg: "{{droplet_present_new|json_query(private_ipv4_query)}}"
  vars:
    private_ipv4_query: "droplet.networks.v4[?type=='private'].ip_address | [0]"

- name: droplet | present | complex | public ipv6 address
  debug:
    msg: "{{droplet_present_new|json_query(public_ipv6_query)}}"
  vars:
    public_ipv6_query: "droplet.networks.v6[?type=='public'].ip_address | [0]"

- name: droplet | info
  doboto_droplet:
    action: info
    id: "{{ droplet_create.droplet.id }}"
  register: droplet_info

- name: droplet | list
  doboto_droplet:
    action: list
  register: droplets_list

- name: droplet | list | tag
  doboto_droplet:
    action: list
    tag_name: some
  register: droplets_list_tag

- name: droplet | action | list
  doboto_droplet:
    action: action_list
    id: "{{ droplet_create.droplet.id }}"
  register: droplet_action_list

- name: droplet | destroy | by id
  doboto_droplet:
    action: destroy
    id: "{{ droplet_create.droplet.id }}"
  register: droplet_id_destroy

- name: droplet | destroy | by tag
  doboto_droplet:
    action: destroy
    tag_name: some
  register: droplet_tag_destroy

- name: droplet_action | single | password_reset
  doboto_droplet:
    action: password_reset
    id: "{{ droplet_create.droplet.id }}"
    wait: true
  register: single_password_reset

- name: droplet_action | single | resize
  doboto_droplet:
    action: resize
    id: "{{ droplet_create.droplet.id }}"
    size: 2gb
    disk: true
    wait: true
  register: single_resize

- name: droplet_action | multiple | power_off
  doboto_droplet:
    action: power_off
    tag_name: some
    wait: true
  register: multiple_power_off
'''


class Droplet(DOBOTOModule):

    def input(self):

        return AnsibleModule(argument_spec=dict(
            action=dict(default=None, required=True, choices=[
                "list",
                "neighbor_list",
                "droplet_neighbor_list",
                "create",
                "present",
                "info",
                "destroy",
                "backup_list",
                "backup_enable",
                "backup_disable",
                "reboot",
                "shutdown",
                "power_on",
                "power_off",
                "power_cycle",
                "restore",
                "password_reset",
                "resize",
                "rebuild",
                "rename",
                "kernel_list",
                "kernel_update",
                "ipv6_enable",
                "private_networking_enable",
                "snapshot_list",
                "snapshot_create",
                "action_list",
                "action_info",
            ]),
            token=dict(default=None, no_log=True),
            id=dict(default=None),
            name=dict(default=None),
            names=dict(default=None, type='list'),
            region=dict(default=None),
            size=dict(default=None),
            disk=dict(default=None, type='bool'),
            image=dict(default=None),
            kernel=dict(default=None),
            ssh_keys=dict(default=None, type='list'),
            backups=dict(default=False, type='bool'),
            ipv6=dict(default=False, type='bool'),
            private_networking=dict(type='bool'),
            user_data=dict(default=None),
            monitoring=dict(type='bool'),
            volume=dict(default=None, type='list'),
            tags=dict(type='list'),
            tag_name=dict(default=None),
            snapshot_name=dict(default=None),
            wait=dict(default=False, type='bool'),
            poll=dict(default=5, type='int'),
            timeout=dict(default=300, type='int'),
            action_id=dict(default=None),
            url=dict(default=self.url),
            extra=dict(default=None, type='dict'),
        ))

    def act(self):

        if self.module.params["action"] in [
            "kernel_list",
            "snapshot_list",
            "backup_list",
            "action_list"
        ]:
            self.list_action(self.module.params["action"].replace('_list', 's'))
        elif self.module.params["action"] in [
            "backup_enable",
            "backup_disable",
            "shutdown",
            "power_cycle",
            "power_on",
            "power_off",
            "private_networking_enable",
            "ipv6_enable"
        ]:
            self.action()
        elif self.module.params["action"] in [
            "reboot",
            "password_reset"
        ]:
            self.action(tagless=True)
        elif self.module.params["action"] == "neighbor_list":
            self.list_action("droplets")
        else:
            getattr(self, self.module.params["action"])()

    def list(self):
        self.module.exit_json(changed=False, droplets=self.do.droplet.list(
            tag_name=self.module.params["tag_name"])
        )

    def droplet_neighbor_list(self):
        self.module.exit_json(changed=False, neighbors=self.do.droplet.droplet_neighbor_list())

    @require("id")
    def list_action(self, key=None):

        if key is None:
            key = self.module.params["action"]

        self.module.exit_json(changed=False,
            **{key: getattr(self.do.droplet, self.module.params["action"])(
               self.module.params["id"]
            )}
        )

    def attribs(self):

        attribs = {
            "region": self.module.params["region"],
            "size": self.module.params["size"],
            "image": self.module.params["image"],
        }

        for optional in [
            'ssh_keys', 'volume', 'tags', 'backups', 'ipv6',
            'private_networking', 'user_data', 'monitoring'
        ]:
            attribs[optional] = self.module.params[optional]

        if self.module.params['extra'] is not None:
            attribs.update(self.module.params['extra'])

        return attribs

    @require("name", "names")
    @require("region")
    @require("size")
    @require("image")
    def create(self):

        attribs = self.attribs()

        if self.module.params["name"] is not None:

            attribs["name"] = self.module.params["name"]
            droplet = self.do.droplet.create(
                attribs,
                self.module.params["wait"],
                self.module.params["poll"],
                self.module.params["timeout"]
            )
            self.module.exit_json(changed=True, droplet=droplet)

        elif self.module.params["names"] is not None:

            attribs["names"] = self.module.params["names"]
            droplets = self.do.droplet.create(
                attribs,
                self.module.params["wait"],
                self.module.params["poll"],
                self.module.params["timeout"]
            )
            self.module.exit_json(changed=True, droplets=droplets)

    @require("name", "names")
    @require("region")
    @require("size")
    @require("image")
    def present(self):

        attribs = self.attribs()

        if self.module.params["name"] is not None:

            attribs["name"] = self.module.params["name"]
            (droplet, created) = self.do.droplet.present(
                attribs,
                wait=self.module.params["wait"],
                poll=self.module.params["poll"],
                timeout=self.module.params["timeout"]
            )
            self.module.exit_json(changed=(created is not None), droplet=droplet, created=created)

        elif self.module.params["names"] is not None:

            attribs["names"] = self.module.params["names"]
            (droplets, created) = self.do.droplet.present(
                attribs,
                wait=self.module.params["wait"],
                poll=self.module.params["poll"],
                timeout=self.module.params["timeout"]
            )
            self.module.exit_json(changed=(len(created) > 0), droplets=droplets, created=created)

    @require("id")
    def info(self):
        self.module.exit_json(changed=False, droplet=self.do.droplet.info(
            self.module.params["id"]
        ))

    @require("id", "tag_name")
    def destroy(self):
        self.module.exit_json(changed=True, result=self.do.droplet.destroy(
            id=self.module.params["id"], tag_name=self.module.params["tag_name"]
        ))

    def action(self, tagless=False):

        if self.module.params["id"] is not None:

            self.module.exit_json(changed=True, action=getattr(
                self.do.droplet,
                self.module.params["action"]
            )(
                id=self.module.params["id"],
                wait=self.module.params["wait"],
                poll=self.module.params["poll"],
                timeout=self.module.params["timeout"]
            ))

        elif not tagless and self.module.params["tag_name"] is not None:

            self.module.exit_json(changed=True, actions=getattr(
                self.do.droplet,
                self.module.params["action"]
            )(
                tag_name=self.module.params["tag_name"],
                wait=self.module.params["wait"],
                poll=self.module.params["poll"],
                timeout=self.module.params["timeout"]
            ))

        else:

            self.module.fail_json(msg="the id or tag_name parameter is required")

    @require("id")
    @require("image")
    def restore(self):
        self.module.exit_json(changed=True, action=self.do.droplet.restore(
            self.module.params["id"], self.module.params["image"],
            wait=self.module.params["wait"],
            poll=self.module.params["poll"],
            timeout=self.module.params["timeout"]
        ))

    @require("id")
    @require("size")
    def resize(self):
        self.module.exit_json(changed=True, action=self.do.droplet.resize(
            self.module.params["id"], self.module.params["size"], self.module.params["disk"],
            wait=self.module.params["wait"],
            poll=self.module.params["poll"],
            timeout=self.module.params["timeout"]
        ))

    @require("id")
    @require("image")
    def rebuild(self):
        self.module.exit_json(changed=True, action=self.do.droplet.rebuild(
            self.module.params["id"], self.module.params["image"],
            wait=self.module.params["wait"],
            poll=self.module.params["poll"],
            timeout=self.module.params["timeout"]
        ))

    @require("id")
    @require("name")
    def rename(self):
        self.module.exit_json(changed=True, action=self.do.droplet.rename(
            self.module.params["id"], self.module.params["name"],
            wait=self.module.params["wait"],
            poll=self.module.params["poll"],
            timeout=self.module.params["timeout"]
        ))

    @require("id")
    @require("kernel")
    def kernel_update(self):
        self.module.exit_json(changed=True, action=self.do.droplet.kernel_update(
            self.module.params["id"], self.module.params["kernel"],
            wait=self.module.params["wait"],
            poll=self.module.params["poll"],
            timeout=self.module.params["timeout"]
        ))

    @require("id", "tag_name")
    @require("snapshot_name")
    def snapshot_create(self):
        self.module.exit_json(changed=True, action=self.do.droplet.snapshot_create(
            id=self.module.params["id"],
            tag_name=self.module.params["tag_name"],
            snapshot_name=self.module.params["snapshot_name"],
            wait=self.module.params["wait"],
            poll=self.module.params["poll"],
            timeout=self.module.params["timeout"]
        ))

    @require("id")
    @require("action_id")
    def action_info(self):
        self.module.exit_json(changed=False, action=self.do.droplet.action_info(
            self.module.params["id"], self.module.params["action_id"]
        ))


if __name__ == '__main__':
    Droplet()
