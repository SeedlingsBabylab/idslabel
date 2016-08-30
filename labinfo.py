import requests
import json
import csv

from Tkinter import *
from tkMessageBox import showwarning, askyesno
import tkFileDialog

import idsserver
import idsblocks
import idssession

class LabInfoPage:
    def __init__(self, server, session):

        self.server = server
        self.session = session

        self.lab_info_page_root = Toplevel()
        self.lab_info_page_root.title("Lab Info")
        self.lab_info_page_root.geometry("1157x400")

        users_label = Label(self.lab_info_page_root, text="Users")
        users_label.grid(row=0, column=0)

        act_work_item_label = Label(self.lab_info_page_root, text="Active Blocks")
        act_work_item_label.grid(row=0, column=1)

        fin_work_item_label = Label(self.lab_info_page_root, text="Finished Blocks")
        fin_work_item_label.grid(row=0, column=2)

        block_attempt_label = Label(self.lab_info_page_root, text="Attempt #")
        block_attempt_label.grid(row=0, column=3)

        self.lab_info_user_box = Listbox(self.lab_info_page_root, width=15, height=20)
        self.lab_info_user_box.grid(row=1, column=0, rowspan=9)
        self.lab_info_user_box.bind('<<ListboxSelect>>', self.update_curr_user)

        self.lab_info_user_work_box = Listbox(self.lab_info_page_root, width=22, height=20)
        self.lab_info_user_work_box.grid(row=1, column=1, rowspan=9)

        self.lab_info_user_past_work_box = Listbox(self.lab_info_page_root, width=22, height=20)
        self.lab_info_user_past_work_box.grid(row=1, column=2, rowspan=9)
        self.lab_info_user_past_work_box.bind('<<ListboxSelect>>', self.get_labels)

        self.lab_info_user_past_work_attempt_box = Listbox(self.lab_info_page_root, width=5, height=20)
        self.lab_info_user_past_work_attempt_box.grid(row=1, column=3, rowspan=9)
        self.lab_info_user_past_work_attempt_box.bind('<<ListboxSelect>>', self.load_block_attempt)

        self.lab_info_past_work_box = Listbox(self.lab_info_page_root, width=10, height=20)
        self.lab_info_past_work_box.grid(row=1, column=4, rowspan=9)
        self.lab_info_past_work_box.bind('<<ListboxSelect>>', self.update_lab_info_curr_clip)

        self.lab_info_past_work_info = Text(self.lab_info_page_root, width=36, height=20)
        self.lab_info_past_work_info.grid(row=1, column=5, rowspan=9)

        self.save_this_block_button = Button(self.lab_info_page_root, text="Save This Block",
                                             command=self.lab_info_save_this_block)
        self.save_this_block_button.grid(row=0, column=6)

        self.delete_this_block_button = Button(self.lab_info_page_root, text="Delete This Block",
                                               command=self.lab_info_delete_this_block)
        self.delete_this_block_button.grid(row=1, column=6)

        self.save_all_lab_blocks_button = Button(self.lab_info_page_root, text="Save Lab Blocks",
                                                 command=self.lab_info_save_lab_blocks)
        self.save_all_lab_blocks_button.grid(row=2, column=6, )

        self.save_all_blocks_button = Button(self.lab_info_page_root, text="Save All Blocks",
                                             command=self.lab_info_save_all_blocks)
        self.save_all_blocks_button.grid(row=3, column=6)

        self.save_training_blocks_button = Button(self.lab_info_page_root, text="Save Training Blocks",
                                                  command=self.lab_info_save_training_blocks)
        self.save_training_blocks_button.grid(row=4, column=6)

        self.save_reliability_blocks_button = Button(self.lab_info_page_root, text="Save Reliability Blocks",
                                                     command=self.lab_info_save_reliability_blocks)
        self.save_reliability_blocks_button.grid(row=5, column=6)

        self.delete_users_blocks_button = Button(self.lab_info_page_root, text="Delete User's Blocks",
                                                 command=self.lab_info_delete_users_blocks)
        self.delete_users_blocks_button.grid(row=6, column=6)

        self.delete_labs_blocks_button = Button(self.lab_info_page_root, text="Delete Lab's Blocks",
                                                command=self.lab_info_delete_labs_blocks)
        self.delete_labs_blocks_button.grid(row=7, column=6)

        self.delete_this_user_button = Button(self.lab_info_page_root, text="Delete This User",
                                              command=self.lab_info_delete_this_user)
        self.delete_this_user_button.grid(row=8, column=6)

        self.curr_past_block = None

        self.curr_past_block_group = None

        payload = {"lab-key": self.server.lab_key}

        resp = requests.post(self.server.lab_info_url, json=payload, allow_redirects=False)

        if resp.ok:
            self.lab_data = json.loads(resp.content)

            i = 0
            for key, value in self.lab_data['users'].iteritems():
                self.lab_info_user_box.insert(i, value['name'])
                self.session.lab_users.append(value["name"])
                i += 1

    def update_curr_user(self, evt):
        box = evt.widget
        index = int(box.curselection()[0])

        self.session.lab_info_curr_user = box.get(index)
        user_data = self.lab_data["users"][str(self.session.lab_info_curr_user)]

        self.lab_info_user_work_box.delete(0, END)
        if user_data["active-work-items"]:
            for index, item_id in enumerate(user_data["active-work-items"]):
                self.lab_info_user_work_box.insert(index, item_id)

        self.lab_info_user_past_work_box.delete(0, END)
        if user_data["finished-work-items"]:
            for index, item_id in enumerate(user_data["finished-work-items"]):
                self.lab_info_user_past_work_box.insert(index, item_id)

    def get_labels(self, evt):
        box = evt.widget
        index = int(box.curselection()[0])

        work_item = box.get(index)

        if not self.server.lab_info_url:
            self.server.parse_config()

        training = True if "train_" in work_item else False
        reliability = True if "reliability" in work_item else False

        payload = {"lab-key": self.server.lab_key,
                   "item-id": work_item,
                   "training": training,
                   "reliability": reliability,
                   "username": self.session.lab_info_curr_user}

        resp = requests.post(self.server.get_labels_url, json=payload, allow_redirects=False)

        block_data = None
        if resp.ok:
            block_data = json.loads(resp.content)
            self.curr_past_block_group = [idsblocks.json_to_block(block) for block in block_data]
            self.curr_past_block = self.curr_past_block_group[0]
            self.fill_attempt_list_lab_info()
            self.load_block_lab_info()
        else:
            showwarning("Bad Request", "Server: {}".format(resp.content))
            return

    def load_block_attempt(self, evt):
        box = evt.widget
        index = int(box.curselection()[0])

        attempt_num = int(box.get(index)) - 1

        if not self.server.lab_info_url:
            self.server.parse_config()

        self.curr_past_block = self.curr_past_block_group[attempt_num]

        self.load_block_lab_info()

    def update_lab_info_curr_clip(self, evt):
        box = evt.widget
        index = int(box.curselection()[0])

        self.curr_lab_info_clip = self.curr_past_block.clips[index]
        work_item = box.get(index)

        self.lab_info_past_work_info.configure(state="normal")
        self.lab_info_past_work_info.delete("1.0", END)

        info_string = "{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n\n\n{}       {}\n{}   {}\n" \
            .format("block:",
                    str(self.curr_lab_info_clip.block_index),
                    "clip:",
                    str(self.curr_lab_info_clip.clip_index),
                    "tier:",
                    str(self.curr_lab_info_clip.clip_tier),
                    "timestamp:",
                    str(self.curr_lab_info_clip.timestamp),
                    "clip length:",
                    str(self.curr_lab_info_clip.offset_time),
                    "clan file:",
                    str(self.curr_lab_info_clip.clan_file),
                    "coder:",
                    str(self.curr_lab_info_clip.coder),
                    "label:",
                    str(self.curr_lab_info_clip.classification),
                    "gender:",
                    str(self.curr_lab_info_clip.gender_label))

        self.lab_info_past_work_info.insert('1.0', info_string)

        self.lab_info_past_work_info.tag_add("label", 10.6, 11.0)
        self.lab_info_past_work_info.tag_add("gender", 11.7, 12.0)
        self.lab_info_past_work_info.tag_configure("label", foreground="red")
        self.lab_info_past_work_info.tag_configure("gender", foreground="#333ccc333")

        self.lab_info_past_work_info.tag_add("block_key", 1.0, 1.5)
        self.lab_info_past_work_info.tag_add("clip_key", 2.0, 2.4)
        self.lab_info_past_work_info.tag_add("tier_key", 3.0, 3.4)
        self.lab_info_past_work_info.tag_add("timestamp_key", 4.0, 4.9)
        self.lab_info_past_work_info.tag_add("clip_length_key", 5.0, 5.11)
        self.lab_info_past_work_info.tag_add("clan_file_key", 6.0, 6.9)
        self.lab_info_past_work_info.tag_add("coder_key", 7.0, 7.6)
        self.lab_info_past_work_info.tag_add("label_key", 10.0, 10.5)
        self.lab_info_past_work_info.tag_add("gender_key", 11.0, 11.6)

        self.lab_info_past_work_info.tag_add("block_value", 1.5, 2.0)
        self.lab_info_past_work_info.tag_add("clip_value", 2.4, 3.0)
        self.lab_info_past_work_info.tag_add("tier_value", 3.4, 4.0)
        self.lab_info_past_work_info.tag_add("timestamp_value", 4.9, 5.0)
        self.lab_info_past_work_info.tag_add("clip_length_value", 5.11, 6.0)
        self.lab_info_past_work_info.tag_add("coder_value", 7.5, 8.0)
        self.lab_info_past_work_info.tag_add("clan_file_value", 6.9, 7.0)
        self.lab_info_past_work_info.tag_add("label_value", 10.5, 11.0)
        self.lab_info_past_work_info.tag_add("gender_value", 11.6, 12.0)

        self.lab_info_past_work_info.tag_configure("block_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("clip_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("tier_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("timestamp_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("clip_length_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("coder_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("clan_file_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("label_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("gender_key", font=("System", "12", "bold"))

        self.lab_info_past_work_info.tag_configure("block_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("clip_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("tier_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("timestamp_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("clip_length_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("coder_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("clan_file_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("label_value", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("gender_value", font=("System", "12", "bold"))

        self.lab_info_past_work_info.configure(state="disabled")

    def lab_info_save_this_block(self):
        output_path = tkFileDialog.asksaveasfilename()

        idsblocks.save_blocks_to_csv([self.curr_past_block], output_path)

    def lab_info_delete_this_block(self):

        if not self.server.lab_key:
            showwarning("Load Config", "You need to load the config.json first")
            return

        payload = {"lab-key": self.server.lab_key,
                   "coder": self.curr_past_block.coder,
                   "block-id": self.curr_past_block.block_id(),
                   "delete-type": "single",
                   "instance": self.curr_past_block.instance}

        resp = requests.post(self.server.delete_block_url, json=payload, allow_redirects=False)

        if not resp.ok:
            print resp.content
        else:
            self.update_curr_user_refresh()

    def lab_info_delete_users_blocks(self):
        theyre_sure = askyesno("Delete User's Blocks",
                               "Are you sure you want to delete all of this user's submissions?")

        if theyre_sure:
            if not self.server.lab_key:
                showwarning("Load Config", "You need to load the config.json first")
                return

            payload = {"lab-key": self.server.lab_key,
                       "coder": self.session.lab_info_curr_user,
                       "delete-type": "user"}

            resp = requests.post(self.server.delete_block_url, json=payload, allow_redirects=False)

            if not resp.ok:
                print resp.content
            else:
                self.update_curr_user_refresh()

    def lab_info_delete_labs_blocks(self):
        theyre_sure = askyesno("Delete Lab's Blocks",
                               "Are you sure you want to delete all of this lab's submissions?")
        if theyre_sure:
            if not self.server.lab_key:
                showwarning("Load Config", "You need to load the config.json first")
                return

            payload = {"lab-key": self.server.lab_key,
                       "delete-type": "lab"}

            resp = requests.post(self.server.delete_block_url, json=payload, allow_redirects=False)

            if not resp.ok:
                print resp.content
            else:
                self.update_curr_user_refresh()

    def lab_info_delete_this_user(self):
        theyre_sure = askyesno("Delete Lab's Blocks",
                               "Are you sure you want to delete this user?\n\n"
                               "All of their data (including submissions) will be lost.")
        if theyre_sure:
            if not self.server.lab_key:
                showwarning("Load Config", "You need to load the config.json first")
                return

        payload = {"lab-key": self.server.lab_key,
                   "username": self.session.lab_info_curr_user}

        resp = requests.post(self.server.delete_user_url, json=payload, allow_redirects=False)

        if not resp.ok:
            print resp.content
        else:
            self.update_user_list()
            #self.update_curr_user_refresh()

    def lab_info_save_lab_blocks(self):
        output_path = tkFileDialog.asksaveasfilename()

        if not self.server.lab_key:
            showwarning("Load Config", "You need to load the config.json first")
            return

        payload = {"lab-key": self.server.lab_key}

        resp = requests.post(self.server.get_lab_labels_url, json=payload, allow_redirects=False)

        block_data = None
        if resp.ok:
            block_data = json.loads(resp.content)

        blocks = []
        for block in block_data:
            blocks.append(idsblocks.json_to_block(block))

        idsblocks.save_blocks_to_csv(blocks, output_path)

    def lab_info_save_all_blocks(self):
        output_path = tkFileDialog.asksaveasfilename()

        if not self.server.lab_key:
            showwarning("Load Config", "You need to load the config.json first")
            return

        payload = {"lab-key": self.server.lab_key}

        resp = requests.post(self.server.get_all_labels_url, json=payload, allow_redirects=False)

        block_data = None
        if resp.ok:
            block_data = json.loads(resp.content)

        blocks = []
        if block_data:
            for block_group in block_data:
                for block in block_group["blocks"]:
                    blocks.append(idsblocks.json_to_block(block))

        idsblocks.save_blocks_to_csv(blocks, output_path)

    def lab_info_save_training_blocks(self):
        output_path = tkFileDialog.asksaveasfilename()

        if not self.server.lab_key:
            showwarning("Load Config", "You need to load the config.json first")
            return

        payload = {"lab-key": self.server.lab_key}

        resp = requests.post(self.server.get_train_labels_url, json=payload, allow_redirects=False)

        block_data = None
        if resp.ok:
            block_data = json.loads(resp.content)

        blocks = []
        for block in block_data:
            blocks.append(idsblocks.json_to_block(block))

        idsblocks.save_blocks_to_csv(blocks, output_path)

    def lab_info_save_reliability_blocks(self):
        output_path = tkFileDialog.asksaveasfilename()

        if not self.server.lab_key:
            showwarning("Load Config", "You need to load the config.json first")
            return

        payload = {"lab-key": self.server.lab_key}

        resp = requests.post(self.server.get_relia_labels_url, json=payload, allow_redirects=False)

        block_data = None
        if resp.ok:
            block_data = json.loads(resp.content)

        blocks = []
        for block in block_data:
            blocks.append(idsblocks.json_to_block(block))

        idsblocks.save_blocks_to_csv(blocks, output_path)

    def fill_attempt_list_lab_info(self):
        self.lab_info_user_past_work_attempt_box.delete(0, END)

        for index, block in enumerate(self.curr_past_block_group):
            self.lab_info_user_past_work_attempt_box.insert(index, str(index+1))

    def load_block_lab_info(self):
        self.lab_info_past_work_box.delete(0, END)

        for index, element in enumerate(self.curr_past_block.clips):
            self.lab_info_past_work_box.insert(index, element.clip_tier)
            if element.clip_tier not in ["FAN", "MAN"]:
                self.lab_info_past_work_box.itemconfig(index, fg="grey")

        self.lab_info_past_work_box.selection_clear(0, END)
        self.lab_info_past_work_box.selection_set(0)

        self.update_lab_info_curr_clip_initial()

    def update_lab_info_curr_clip_initial(self):
        self.lab_info_past_work_box.selection_set(0)
        self.curr_lab_info_clip = self.curr_past_block.clips[0]

        self.lab_info_past_work_info.configure(state="normal")
        self.lab_info_past_work_info.delete("1.0", END)

        info_string = "{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n\n\n{}       {}\n{}   {}\n" \
            .format("block:",
                    str(self.curr_lab_info_clip.block_index),
                    "clip:",
                    str(self.curr_lab_info_clip.clip_index),
                    "tier:",
                    str(self.curr_lab_info_clip.clip_tier),
                    "timestamp:",
                    str(self.curr_lab_info_clip.timestamp),
                    "clip length:",
                    str(self.curr_lab_info_clip.offset_time),
                    "clan file:",
                    str(self.curr_lab_info_clip.clan_file),
                    "coder:",
                    str(self.curr_lab_info_clip.coder),
                    "label:",
                    str(self.curr_lab_info_clip.classification),
                    "gender:",
                    str(self.curr_lab_info_clip.gender_label))

        self.lab_info_past_work_info.insert('1.0', info_string)

        self.lab_info_past_work_info.tag_add("label", 10.6, 11.0)
        self.lab_info_past_work_info.tag_add("gender", 11.7, 12.0)
        self.lab_info_past_work_info.tag_configure("label", foreground="red")
        self.lab_info_past_work_info.tag_configure("gender", foreground="#333ccc333")

        self.lab_info_past_work_info.tag_add("block_key", 1.0, 1.5)
        self.lab_info_past_work_info.tag_add("clip_key", 2.0, 2.4)
        self.lab_info_past_work_info.tag_add("tier_key", 3.0, 3.4)
        self.lab_info_past_work_info.tag_add("timestamp_key", 4.0, 4.9)
        self.lab_info_past_work_info.tag_add("clip_length_key", 5.0, 5.11)
        self.lab_info_past_work_info.tag_add("clan_file_key", 6.0, 6.9)
        self.lab_info_past_work_info.tag_add("coder_key", 7.0, 7.6)
        self.lab_info_past_work_info.tag_add("label_key", 10.0, 10.5)
        self.lab_info_past_work_info.tag_add("gender_key", 11.0, 11.6)

        self.lab_info_past_work_info.tag_add("block_value", 1.5, 2.0)
        self.lab_info_past_work_info.tag_add("clip_value", 2.4, 3.0)
        self.lab_info_past_work_info.tag_add("tier_value", 3.4, 4.0)
        self.lab_info_past_work_info.tag_add("timestamp_value", 4.9, 5.0)
        self.lab_info_past_work_info.tag_add("clip_length_value", 5.11, 6.0)
        self.lab_info_past_work_info.tag_add("coder_value", 7.5, 8.0)
        self.lab_info_past_work_info.tag_add("clan_file_value", 6.9, 7.0)
        self.lab_info_past_work_info.tag_add("label_value", 10.5, 11.0)
        self.lab_info_past_work_info.tag_add("gender_value", 11.6, 12.0)

        self.lab_info_past_work_info.tag_configure("block_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("clip_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("tier_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("timestamp_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("clip_length_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("coder_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("clan_file_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("label_key", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("gender_key", font=("System", "12", "bold"))

        self.lab_info_past_work_info.tag_configure("block_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("clip_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("tier_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("timestamp_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("clip_length_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("coder_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("clan_file_value", font=("System", "12"))
        self.lab_info_past_work_info.tag_configure("label_value", font=("System", "12", "bold"))
        self.lab_info_past_work_info.tag_configure("gender_value", font=("System", "12", "bold"))

        self.lab_info_past_work_info.configure(state="disabled")

    def update_user_list(self):
        payload = {"lab-key": self.server.lab_key}

        resp = requests.post(self.server.lab_info_url, json=payload, allow_redirects=False)

        if resp.ok:
            self.lab_data = json.loads(resp.content)

            self.lab_info_user_box.delete(0, END)
            i = 0
            for key, value in self.lab_data['users'].iteritems():
                self.lab_info_user_box.insert(i, value['name'])
                self.session.lab_users.append(value["name"])
                i += 1

            self.lab_info_user_work_box.delete(0, END)
            self.lab_info_user_past_work_box.delete(0, END)
            self.lab_info_user_past_work_attempt_box.delete(0, END)
            self.lab_info_past_work_box.delete(0, END)

            self.lab_info_past_work_info.configure(state="normal")
            self.lab_info_past_work_info.delete("1.0", END)
            self.lab_info_past_work_info.configure(state="disabled")

    def update_curr_user_refresh(self):
        self.server.lab_info_ping()

        user_data = self.session.lab_data["users"][str(self.session.lab_info_curr_user)]

        self.lab_info_user_work_box.delete(0, END)
        if user_data["active-work-items"]:
            for index, item_id in enumerate(user_data["active-work-items"]):
                self.lab_info_user_work_box.insert(index, item_id)

        self.lab_info_user_past_work_box.delete(0, END)
        if user_data["finished-work-items"]:
            for index, item_id in enumerate(user_data["finished-work-items"]):
                self.lab_info_user_past_work_box.insert(index, item_id)

        if user_data["finished-work-items"] and \
           self.curr_past_block.block_id() in user_data["finished-work-items"]:

            self.get_labels_refresh(self.curr_past_block.block_id())
        else:
            self.lab_info_user_past_work_attempt_box.delete(0, END)
            if user_data["finished-work-items"]:
                self.get_labels_refresh(user_data["finished-work-items"][0])

    def get_labels_refresh(self, block_id):
        work_item = block_id

        if not self.server.lab_info_url:
            self.server.parse_config()

        training = True if "train_" in work_item else False
        reliability = True if "reliability" in work_item else False

        payload = {"lab-key": self.server.lab_key,
                   "item-id": work_item,
                   "training": training,
                   "reliability": reliability,
                   "username": self.session.lab_info_curr_user}

        resp = requests.post(self.server.get_labels_url, json=payload, allow_redirects=False)

        block_data = None
        if resp.ok:
            block_data = json.loads(resp.content)
            self.curr_past_block_group = [idsblocks.json_to_block(block) for block in block_data]
            self.curr_past_block = self.curr_past_block_group[0]
            self.fill_attempt_list_lab_info()
            self.load_block_lab_info()
        else:
            showwarning("Bad Request", "Server: {}".format(resp.content))
            return
