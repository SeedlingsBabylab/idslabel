import json
import os
import requests
import cgi

import tkSimpleDialog
from tkMessageBox import showwarning

import idsblocks

class IDSServer(object):
    def __init__(self, config_path=None, session=None):
        self.get_block_url = ""
        self.delete_block_url = ""
        self.delete_user_url = ""
        self.lab_info_url = ""
        self.all_lab_info_url = ""
        self.add_user_url = ""
        self.submit_labels_url = ""
        self.get_labels_url = ""
        self.get_lab_labels_url = ""
        self.get_all_labels_url = ""
        self.get_train_labels_url = ""
        self.get_relia_labels_url = ""
        self.send_back_blocks_url = ""

        self.github_tags_url = "https://api.github.com/repos/SeedlingsBabylab/idslabel/tags"

        self.lab_key = ""
        self.lab_name = ""

        self.session = session

        self.config_path = config_path
        if config_path:
            self.parse_config()


    def parse_config(self):
        with open(self.config_path, "rU") as input:
            config = json.load(input)

            self.lab_key = config["lab-key"]
            self.lab_name = config["lab-name"]

            self.get_block_url = config["server-urls"]["get_block_url"]
            self.delete_block_url = config["server-urls"]["delete_block_url"]
            self.delete_user_url = config["server-urls"]["delete_user_url"]
            self.lab_info_url = config["server-urls"]["lab_info_url"]
            self.all_lab_info_url = config["server-urls"]["all_lab_info_url"]
            self.add_user_url = config["server-urls"]["add_user_url"]
            self.submit_labels_url = config["server-urls"]["submit_labels_url"]
            self.get_labels_url = config["server-urls"]["get_labels_url"]
            self.get_lab_labels_url = config["server-urls"]["get_lab_labels_url"]
            self.get_all_labels_url = config["server-urls"]["get_all_labels_url"]
            self.get_train_labels_url = config["server-urls"]["get_train_labels_url"]
            self.get_relia_labels_url = config["server-urls"]["get_relia_labels_url"]
            self.send_back_blocks_url = config["server-urls"]["send_back_blocks_url"]

    def lab_info_ping(self):
        if not self.lab_info_url:
            self.parse_config()

        payload = {"lab-key": self.lab_key}

        resp = requests.post(self.lab_info_url, json=payload, allow_redirects=False)

        if resp.ok:
            self.session.lab_data = json.loads(resp.content)
            return self.session.lab_data
        else:
            showwarning("Bad Request", "User: \"{}\" does not exist on the server.\n\n".format(self.session.codername)+\
                                       "(File -> Add User to Server)")
            print resp.content
            return

    def add_user_to_server(self):
        name = tkSimpleDialog.askstring(title="Add User",
                                        prompt="Username:",
                                        initialvalue=self.session.codername)

        if not name:
            return

        payload = {"lab-key": self.lab_key,
                   "lab-name": self.lab_name,
                   "username": name}

        resp = requests.post(self.add_user_url, json=payload, allow_redirects=False)

        if not resp.ok:
            print resp.content

    def get_block(self):
        payload = {}
        payload["lab-key"] = self.lab_key
        payload["username"] = self.session.codername

        if not self.get_block_url:
            self.parse_config()

        resp = requests.post(self.get_block_url, json=payload, stream=True, allow_redirects=False)

        if resp.status_code != 200:
            return resp.content

        if resp.ok:
            params = cgi.parse_header(resp.headers.get('Content-Disposition', ''))
            filename = params[1]['filename']
            file_end = os.path.basename(filename)
            file_root = "{}_{}_block{}".format(self.session.codername, os.path.dirname(filename), file_end)
            block_path = os.path.join(self.session.clip_directory, file_root)

            if not os.path.exists(block_path):
                os.makedirs(block_path)

            output_path = os.path.join(block_path, file_end)

            with open(output_path, "wb") as output:
                output.write(resp.content)

            block = idsblocks.create_block_from_zip(output_path, self.session.codername, self.lab_key)

            self.session.clip_blocks.append(block)

    def get_training_block(self):
        payload = {}
        payload["lab-key"] = self.lab_key
        payload["username"] = self.session.codername
        payload["training"] = True
        payload["train-pack-num"] = 1

        if not self.get_block_url:
            self.parse_config()

        resp = requests.post(self.get_block_url, json=payload, stream=True, allow_redirects=False)

        if resp.status_code != 200:
            return resp.content

        if resp.ok:

            params = cgi.parse_header(resp.headers.get('Content-Disposition', ''))
            filename = params[1]['filename']
            file_end = os.path.basename(filename)
            file_root = "{}_{}_block{}".format(self.session.codername, os.path.dirname(filename), file_end)
            block_path = os.path.join(self.session.clip_directory, file_root)

            if not os.path.exists(block_path):
                os.makedirs(block_path)

            output_path = os.path.join(block_path, file_end)

            with open(output_path, "wb") as output:
                output.write(resp.content)

            block = idsblocks.create_block_from_zip(output_path, self.session.codername, self.lab_key)

            self.session.clip_blocks.append(block)

    def get_reliability_block(self):
        payload = {}
        payload["lab-key"] = self.lab_key
        payload["username"] = self.session.codername
        payload["reliability"] = True
        payload["train-pack-num"] = 1

        if not self.get_block_url:
            self.parse_config()

        resp = requests.post(self.get_block_url, json=payload, stream=True, allow_redirects=False)

        if resp.status_code != 200:
            return resp.content

        if resp.ok:

            params = cgi.parse_header(resp.headers.get('Content-Disposition', ''))
            filename = params[1]['filename']
            file_end = os.path.basename(filename)
            file_root = "{}_{}_block{}".format(self.session.codername, os.path.dirname(filename), file_end)
            block_path = os.path.join(self.session.clip_directory, file_root)

            if not os.path.exists(block_path):
                os.makedirs(block_path)

            output_path = os.path.join(block_path, file_end)

            with open(output_path, "wb") as output:
                output.write(resp.content)

            block = idsblocks.create_block_from_zip(output_path, self.session.codername, self.lab_key)

            self.session.clip_blocks.append(block)