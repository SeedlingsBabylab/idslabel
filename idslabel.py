import pyaudio
import wave
import json
import random
import datetime
import urllib2
import time
import csv
import re
import os
import requests
import cgi
import zipfile
import shutil
import subprocess as sp

from operator import itemgetter

from Tkinter import *
import tkFileDialog
import tkSimpleDialog
from tkMessageBox import showwarning


version = "0.0.7"


get_block_url = ""
lab_info_url = ""
all_lab_info_url = ""
add_user_url = ""
submit_labels_url = ""
get_labels_url = ""
get_lab_labels_url = ""
get_all_labels_url = ""
send_back_blocks_url = ""


class Block:
    def __init__(self, index, clan_file):

        self.index = index
        self.clan_file = clan_file
        self.num_clips = None
        self.clips = []
        self.sliced = False
        #self.contains_fan_or_man = False
        self.dont_share = False
        self.id = ""
        self.coder = None
        self.lab_key = None
        self.lab_name = None
        self.old = False

    def sort_clips(self):
        self.clips.sort(key=lambda x: x.clip_index)

    def to_dict(self):
        block = {}

        block["clips"] = []
        for clip in self.clips:
            block["clips"].append(clip.to_dict())

        block["coder"] = self.coder
        block["lab-key"] = self.lab_key
        block["lab-name"] = self.lab_name
        block["id"] = self.id
        #block["fan-or-man"] = self.contains_fan_or_man
        block["dont-share"] = self.dont_share
        block["clan-file"] = self.clan_file
        block["block-index"] = self.index

        return block


class Clip:
    def __init__(self, path, block_index, clip_index):
        self.audio_path = path
        self.parent_audio_path = None
        self.clan_file = None
        self.block_index = block_index
        self.clip_index = clip_index
        self.clip_tier = None
        self.multiline = False
        self.multi_tier_parent = None
        self.start_time = None
        self.offset_time = None
        self.timestamp = None
        self.classification = None
        self.gender_label = None
        self.label_date = None
        self.coder = None
        self.lab_key = None


    def to_dict(self):
        clip = {}

        #clip["audio-path"] = self.audio_path
        #clip["parent-audio-path"] = self.parent_audio_path
        clip["clan-file"] = self.clan_file
        clip["block-index"] = self.block_index
        clip["clip-index"] = self.clip_index
        clip["clip-tier"] = self.clip_tier
        clip["multiline"] = self.multiline
        clip["multi-tier-parent"] = self.multi_tier_parent
        clip["start-time"] = self.start_time
        clip["offset-time"] = self.offset_time
        clip["timestamp"] = self.timestamp
        clip["classification"] = self.classification
        clip["gender-label"] = self.gender_label
        clip["label-date"] = self.label_date
        clip["coder"] = self.coder

        return clip


    def __repr__(self):
        return "clip: {} - [block: {}] [tier: {}] [label: {}] [time: {}]"\
                .format(self.clip_index,
                        self.block_index,
                        self.clip_tier,
                        self.classification,
                        self.timestamp)

class MainWindow:

    def __init__(self, master):
        self.clan_file = None
        self.audio_file = None

        self.conversation_blocks = None

        self.current_clip = None

        self.current_block_index = None
        self.current_block = None
        self.processed_clips_in_curr_block = []
        self.processed_clips = []

        self.root = master                          # main GUI context
        self.root.title("IDS Label  v"+version)      # title of window
        self.root.geometry("1000x610")              # size of GUI window
        self.main_frame = Frame(root)               # main frame into which all the Gui components will be placed

        self.main_frame.bind("<Key>", self.key_select)
        self.main_frame.bind("<space>", self.shortcut_play_clip)
        self.main_frame.bind("<Shift-space>", self.shortcut_play_block)
        self.main_frame.bind("<Left>", self.shortcut_previous_clip)
        self.main_frame.bind("<Right>", self.shortcut_next_clip)
        self.main_frame.bind("<Up>", self.shortcut_previous_clip)
        self.main_frame.bind("<Down>", self.shortcut_next_clip)
        self.main_frame.bind("<Shift-Return>", self.shortcut_submit_block)

        if sys.platform == "darwin":
            self.main_frame.bind("<Command-s>", self.save_classifications)
            self.main_frame.bind("<Command-S>", self.save_as_classifications)
            self.main_frame.bind("<Command-l>", self.reload_classifications)
        if sys.platform == "linux2":
            self.main_frame.bind("<Control-s>", self.save_classifications)
            self.main_frame.bind("<Control-S>", self.save_as_classifications)
            self.main_frame.bind("<Control-l>", self.reload_classifications)
        if sys.platform == "win32":
            self.main_frame.bind("<Control-s>", self.save_classifications)
            self.main_frame.bind("<Control-S>", self.save_as_classifications)
            self.main_frame.bind("<Control-l>", self.reload_classifications)

        self.menubar = Menu(self.root)

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load Audio", command=self.load_audio)
        self.filemenu.add_command(label="Load Clan", command=self.load_clan)
        self.filemenu.add_command(label="Save Classifications", command=self.output_classifications)
        self.filemenu.add_command(label="Save As Classifications", command=self.set_classification_output)
        self.filemenu.add_command(label="Load Saved Classifications", command=self.load_classifications)
        self.filemenu.add_command(label="Set Block Path", command=self.set_clip_path)
        self.filemenu.add_command(label="Get Lab Info", command=self.get_lab_info)
        #self.filemenu.add_command(label="Get All Lab Info", command=self.get_all_lab_info)
        self.filemenu.add_command(label="Add User to Server", command=self.add_user_to_server)
        self.filemenu.add_command(label="Submit Block", command=self.submit_block)
        self.filemenu.add_command(label="Submit All Blocks", command=self.submit_all_blocks)
        self.filemenu.add_command(label="Send Blocks Back", command=self.send_blocks_back)

        self.menubar.add_cascade(label="File", menu=self.filemenu)


        self.helpmenu= Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="About", command=self.show_about)
        self.helpmenu.add_command(label="Show Shortcuts", command=self.show_shortcuts)

        self.menubar.add_cascade(label="Help", menu=self.helpmenu)

        self.root.config(menu=self.menubar)

        self.main_frame.bind("<FocusOut>", self.reset_frame_focus)

        self.main_frame.pack()

        self.load_clan_button = Button(self.main_frame,
                                          text= "Load Clan File",
                                          command=self.load_clan)

        self.load_audio_button = Button(self.main_frame,
                                           text= "Load Audio",
                                           command=self.load_audio)

        self.load_rand_block_button = Button(self.main_frame,
                                             text="Load Block",
                                             command=self.load_random_conv_block)

        self.load_previous_block_button = Button(self.main_frame,
                                                 text="Previous Block",
                                                 command=self.load_previous_block)

        self.play_clip_button = Button(self.main_frame,
                                       text="Play Clip",
                                       command=self.play_clip)

        self.play_block_button = Button(self.main_frame,
                                        text="Play Block",
                                        command=self.play_whole_block)

        self.next_clip_button = Button(self.main_frame,
                                       text="Next Clip",
                                       command=self.next_clip)

        self.output_classifications_button = Button(self.main_frame,
                                                    text="Save Current Block",
                                                    command=self.output_classifications)

        self.submit_labels_to_server_button = Button(self.main_frame,
                                                     text="Submit Block",
                                                     command=self.submit_block)

        self.submit_labels_to_server_and_save_button = Button(self.main_frame,
                                                     text="Submit + Save",
                                                     command=self.submit_block_and_save)

        self.submit_all_labels_to_server_button = Button(self.main_frame,
                                                     text="Submit All Blocks",
                                                     command=self.submit_all_blocks)

        self.load_classifications_button = Button(self.main_frame,
                                                  text="Load Classifications",
                                                  command=self.load_classifications)

        self.get_blocks_button = Button(self.main_frame,
                                        text="Get Blocks",
                                        command=self.get_blocks)

        self.send_block_back_button = Button(self.main_frame,
                                            text="Send Blocks Back",
                                            command=self.send_blocks_back)

        #self.load_clan_button.grid(row=0, column=0)
        #self.load_audio_button.grid(row=0, column=1)
        self.get_blocks_button.grid(row=0, column=2)

        #self.load_rand_block_button.grid(row=1, column=2)
        self.play_block_button.grid(row=2, column=2)
        self.play_clip_button.grid(row=3, column=2)
        self.next_clip_button.grid(row=4, column=2)
        self.output_classifications_button.grid(row=5, column=2)
        self.submit_labels_to_server_button.grid(row=6, column=2)
        self.submit_labels_to_server_and_save_button.grid(row=7, column=2)
        self.submit_all_labels_to_server_button.grid(row=8, column=2)
        self.send_block_back_button.grid(row=7, column=4)

        #self.load_classifications_button.grid(row=8, column=2, rowspan=2)

        self.block_list = Listbox(self.main_frame, width=15, height=25)
        self.block_list.grid(row=1, column=3, rowspan=24)

        self.block_list.bind('<<ListboxSelect>>', self.update_curr_clip)
        self.block_list.bind("<FocusIn>", self.reset_frame_focus)
        self.block_count_label = None


        self.curr_clip_info = Text(self.main_frame, width=50, height=15)
        self.curr_clip_info.tag_add("label", 1.0, 11.10)
        self.curr_clip_info.tag_add("gender", 11.6, 11.10)
        self.curr_clip_info.tag_configure("label", foreground="red")
        self.curr_clip_info.tag_configure("gender", foreground="blue")
        self.curr_clip_info.grid(row=3, column=0, rowspan=8, columnspan=2)


        self.codername_entry = Entry(self.main_frame, width=15, font="-weight bold")
        self.codername_entry.insert(END, "CODER_NAME")
        self.codername_entry.grid(row=0, column=4)
        self.codername_entry.bind("<Return>", self.codername_entered)


        self.num_blocks_to_get = 3
        self.block_request_num_entry = Entry(self.main_frame, width=7)
        self.block_request_num_entry.insert(END, str(self.num_blocks_to_get))
        self.block_request_num_entry.grid(row=1, column=4, sticky="E")
        self.block_request_num_entry.bind("<Return>", self.enter_block_request_num)

        self.block_num_label = Label(self.main_frame, text="  # blocks:", font="-weight bold")
        self.block_num_label.grid(row=1, column=4, sticky="W")

        self.classification_conflict_label = None

        self.clips_processed_label = None
        self.coded_block_label = None

        self.interval_regx = re.compile("\\x15\d+_\d+\\x15")

        self.clip_blocks = []
        self.randomized_blocks = []
        self.clip_path = None

        self.slicing_process = None

        self.main_frame.focus_set()

        self.shortcuts_menu = None

        self.curr_clip_info.configure(state="disabled")

        # self.block_condition_var = IntVar()
        # self.block_condition_button = Checkbutton(self.main_frame, text="only load blocks with\nat least 1 FAN/MAN\ntier", variable=self.block_condition_var)
        # self.block_condition_button.select()
        # self.block_condition_button.grid(row=2, column=4)

        self.dont_share_var = IntVar()
        self.dont_share_button = Checkbutton(self.main_frame,
                                             text="don't share this block",
                                             variable=self.dont_share_var,
                                             command=self.set_curr_block_dontshare)

        self.dont_share_button.grid(row=3, column=4)

        self.loaded_block_history = []
        self.on_first_block = False

        self.previous_block_label = Label(self.main_frame, text="Load Block:")
        self.previous_block_label.grid(row=4, column=4)

        self.previous_block_menu = Listbox(self.main_frame, width=14, height=10)

        self.previous_block_menu.bind("<Double-Button-1>", self.load_previous_block_downloaded)

        self.previous_block_menu.bind("<FocusIn>", self.reset_frame_focus)

        self.previous_block_menu.grid(row=5, column=4)

        self.classification_output = ""

        self.clip_directory = ""

        self.old_classifications_file = ""

        self.loaded_classification_file = []

        self.paths_text = None
        self.print_paths()

        self.reload_multiline_parents = []

        self.show_shortcuts()

        self.last_tried_block = 0

        self.key_label_map = {  "a": "ADS",
                                "c": "CDS",
                                "j": "JUNK",
                                "m": "MULTIPLE_ADDR",
                                "n": "CHILD_NOISE",
                                "r": "REGISTER_SWITCH"
                              }

        self.gender_label_map = {
            "M": "MALE",
            "F": "FEMALE",
            "U": "UNCLEAR"
        }

        self.num_blocks_to_get = 3

        self.lab_info_page = None
        self.lab_info_user_box = None
        self.lab_info_user_work_box = None
        self.lab_info_user_past_work_box = None
        self.lab_info_past_work_box = None
        self.lab_info_past_work_info = None
        self.curr_user = None
        self.lab_data = None
        self.past_work_item_data = []
        self.curr_past_block = None
        self.curr_lab_info_clip = None
        self.lab_users = []


        self.all_lab_info_page = None
        self.all_lab_info_lab_box = None
        self.all_lab_info_user_box = None
        self.all_lab_data = None
        self.curr_lab = None

        self.lab_key = ""
        self.lab_name = ""

        #self.parse_config()

        self.prev_downl_blocks = []

        self.send_blocks_back_page = None
        self.send_back_block_list = None

        self.session_output_file = None
        self.session_output_header_written = False

    def key_select(self, event):
        self.main_frame.focus_set()

        selected_key = event.char

        if selected_key in self.key_label_map:
            if not self.current_clip:
                self.set_curr_clip(0)
            if self.codername_entry.get() == "CODER_NAME":
                showwarning("Coder Name", "You need to set a coder name (upper right hand corner)")
                return

            if self.current_clip.clip_tier not in ["FAN", "MAN"]:
                return
            self.current_clip.classification = self.key_label_map[selected_key]
            self.current_clip.label_date = time.strftime("%m/%d/%Y")
            self.current_clip.coder = self.codername_entry.get()
            self.update_curr_clip_info()

        if selected_key in self.gender_label_map:
            if not self.current_clip:
                self.set_curr_clip(0)
            if self.codername_entry.get() == "CODER_NAME":
                showwarning("Coder Name", "You need to set a coder name (upper right hand corner)")
                return

            if self.current_clip.clip_tier not in ["FAN", "MAN"]:
                return
            self.current_clip.label_date = time.strftime("%m/%d/%Y")
            self.current_clip.coder = self.codername_entry.get()
            self.current_clip.gender_label = self.gender_label_map[selected_key]
            self.update_curr_clip_info()

        # if selected_key == "C":
        #     self.load_clan()
        # if selected_key == "A":
        #     self.load_audio()
        # if selected_key == "|":
        #     self.load_previous_block()
        if selected_key == "O":
            self.output_classifications()

    def shortcut_play_clip(self, event):
        if not self.current_clip:
            self.set_curr_clip(0)

        self.play_clip()

    def shortcut_play_block(self, event):
        self.play_whole_block()

    def shortcut_previous_clip(self, event):
        self.previous_clip()

    def shortcut_next_clip(self, event):
        self.next_clip()

    def shortcut_load_random_block(self, event):
        self.load_random_conv_block()

    def shortcut_submit_block(self, event):
        self.submit_block()

    def reset_frame_focus(self, event):
        self.main_frame.focus_set()

    def codername_entered(self, event):
        if not self.clip_directory:
            showwarning("Clips Directory", "Choose directory to store downloaded blocks")
            self.clip_directory = tkFileDialog.askdirectory()
        del self.clip_blocks[:]
        self.prev_downl_blocks = self.load_previously_downl_blocks()
        if self.prev_downl_blocks:
            self.clip_blocks.extend(self.prev_downl_blocks)
        self.load_downloaded_blocks()
        self.print_paths()
        self.main_frame.focus_set()

    def load_clan(self):
        try:
            self.check_github_for_latest_version()
        except Exception as e:
            print e.message

        self.clan_file = tkFileDialog.askopenfilename()

        showwarning("Clips", "Please choose a folder to store audio clips")
        self.set_clip_path()
        self.print_paths()
        if not self.classification_output:
            showwarning("Output", "Please create a classification output file (.csv)")
            self.set_classification_output()
            self.print_paths()

        showwarning("Note", "Remember to write your name in the 'CODER_NAME' box before starting")

        self.parse_clan(self.clan_file)

        if not os.path.isfile(self.classification_output):
            self.output_classifications()

        self.print_paths()

    def find_clip_and_update(self, entry):
        block_index = int(entry[4])-1
        block = self.clip_blocks[block_index]
        clip_index = int(entry[6]) - 1
        block.clips[clip_index].label_date = entry[0]
        block.clips[clip_index].coder = entry[1]
        block.clips[clip_index].classification = entry[8]

        if entry[9] != "N":
            block.clips[clip_index].multiline = True
            block.clips[clip_index].multi_tier_parent = entry[9]

    def reload_classifications(self, event):
        self.load_classifications()

    def load_classifications(self):

        if not self.clip_blocks:
            showwarning("Reload", "You need to load audio and cha file before reloading saved classifications")
            return
        self.old_classifications_file = tkFileDialog.askopenfilename()

        with open(self.old_classifications_file, "rU") as input:
            reader = csv.reader(input)
            reader.next()
            for row in reader:
                self.loaded_classification_file.append(row)


        if self.loaded_classification_file:
            completed_classifications = []
            for entry in self.loaded_classification_file:
                if entry[0]:
                    completed_classifications.append(entry)


            for entry in completed_classifications:
                self.find_clip_and_update(entry)

    def load_audio(self):
        self.audio_file = tkFileDialog.askopenfilename()
        self.print_paths()

    def play_clip(self):
        current_clip = self.block_list.curselection()
        clip_index = int(current_clip[0])

        clip_path = self.current_block.clips[clip_index].audio_path
        chunk = 1024

        f = wave.open(clip_path,"rb")

        p = pyaudio.PyAudio()

        stream = p.open(format = p.get_format_from_width(f.getsampwidth()),
                        channels = f.getnchannels(),
                        rate = f.getframerate(),
                        output = True)

        data = f.readframes(chunk)

        while data != '':
            stream.write(data)
            data = f.readframes(chunk)

        stream.stop_stream()
        stream.close()

        p.terminate()

    def play_whole_block(self):

        chunk = 1024

        p = pyaudio.PyAudio()
        first_clip = self.current_block.clips[0].audio_path
        f = wave.open(first_clip,"rb")

        stream = p.open(format = p.get_format_from_width(f.getsampwidth()),
                        channels = f.getnchannels(),
                        rate = f.getframerate(),
                        output = True)

        for clip in self.current_block.clips:

            clip_path = clip.audio_path


            f = wave.open(clip_path,"rb")

            data = f.readframes(chunk)

            while data != '':
                stream.write(data)
                data = f.readframes(chunk)

        stream.stop_stream()
        stream.close()

        p.terminate()

    def parse_clan(self, path):
        conversations = []

        curr_conversation = []
        with open(path, "rU") as file:
            for line in file:
                if line.startswith("@Bg:\tConversation"):
                    curr_conversation.append(line)
                    continue
                if curr_conversation:
                    curr_conversation.append(line)
                if line.startswith("@Eg:\tConversation"):
                    conversations.append(curr_conversation)
                    curr_conversation = []

        conversation_blocks = self.filter_conversations(conversations)


        for index, block in enumerate(conversation_blocks):
            self.clip_blocks.append(self.create_clips(block, path, index+1))

        self.find_multitier_parents()

        self.block_count_label = Label(self.main_frame,
                                       text=str(len(conversation_blocks))+\
                                       " blocks")

        self.block_count_label.grid(row=27, column=3, columnspan=1)

        self.create_random_block_range()

    def slice_block(self, block):

        clanfilename = block.clan_file[0:5]

        all_blocks_path = os.path.join(self.clip_directory, clanfilename)

        if not os.path.exists(all_blocks_path):
            os.makedirs(all_blocks_path)

        block_path = os.path.join(all_blocks_path, str(block.index))


        if not os.path.exists(block_path):
            os.makedirs(block_path)

        # showwarning("working directory", "{}".format(os.getcwd()))

        out, err = None, None
        for clip in block.clips:
            command = ["./ffmpeg",
                       "-ss",
                       str(clip.start_time),
                       "-t",
                       str(clip.offset_time),
                       "-i",
                       self.audio_file,
                       clip.audio_path,
                       "-y"]

            command_string = " ".join(command)
            print command_string

            pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10**8)
            out, err = pipe.communicate()
        # showwarning("command output", "{}".format(out))
        # showwarning("command err", "{}".format(err))

    def create_random_block_range(self):

        self.randomized_blocks = list(self.clip_blocks)
        random.shuffle(self.randomized_blocks)

    def filter_conversations(self, conversations):
        filtered_conversations = []

        last_tier = ""

        for conversation in conversations:
            conv_block = []
            for line in conversation:
                if line.startswith("%"):
                    continue
                elif line.startswith("@"):
                    continue
                elif line.startswith("*"):
                    last_tier = line[0:4]
                    conv_block.append(line)
                else:
                    conv_block.append(last_tier+line+"   MULTILINE")
            filtered_conversations.append(conv_block)
            conv_block = []

        return filtered_conversations

    def find_multitier_parents(self):

        for block in self.clip_blocks:
            for clip in block.clips:
                if clip.multiline:
                    self.reverse_parent_lookup(block, clip)

    def reverse_parent_lookup(self, block, multi_clip):
        for clip in reversed(block.clips[0:multi_clip.clip_index-1]):
            if clip.multiline:
                continue
            else:
                multi_clip.multi_tier_parent = clip.timestamp
                return

    def create_clips(self, clips, parent_path, block_index):

        parent_path = os.path.split(parent_path)[1]

        parent_audio_path = os.path.split(self.audio_file)[1]

        block = Block(block_index, parent_path)

        for index, clip in enumerate(clips):

            clip_path = os.path.join(self.clip_directory,
                                     parent_path[0:5],
                                     str(block_index),
                                     str(index+1)+".wav")

            curr_clip = Clip(clip_path, block_index, index+1)
            curr_clip.parent_audio_path = parent_audio_path
            curr_clip.clan_file = parent_path
            curr_clip.clip_tier = clip[1:4]
            if "MULTILINE" in clip:
                curr_clip.multiline = True

            interval_reg_result = self.interval_regx.search(clip)
            if interval_reg_result:
                interval_str = interval_reg_result.group().replace("\x15", "")
                curr_clip.timestamp = interval_str

            time = interval_str.split("_")
            time = [int(time[0]), int(time[1])]

            final_time = self.ms_to_hhmmss(time)

            curr_clip.start_time = str(final_time[0])
            curr_clip.offset_time = str(final_time[2])

            block.clips.append(curr_clip)

        block.num_clips = len(block.clips)

        #self.blocks_to_csv()

        for clip in block.clips:
            if clip.clip_tier == "FAN":
                block.contains_fan_or_man = True
            if clip.clip_tier == "MAN":
                block.contains_fan_or_man = True

        return block

    def create_block_from_zip(self, path_to_zip):
        # extract the zipped block
        zip = zipfile.ZipFile(path_to_zip)
        clips_path = os.path.dirname(path_to_zip)
        zip.extractall(clips_path)

        # read the block's metadata from the csv file
        csv_files = [x for x in os.listdir(clips_path) if ".csv" in x]
        csv_file = ""
        if len(csv_files) == 1:
            csv_file = csv_files[0]

        csv_data = []

        csv_path = os.path.join(clips_path, csv_file)
        with open(csv_path, "rU") as csv_input:
            reader = csv.reader(csv_input)
            reader.next()
            for row in reader:
                csv_data.append(row)

        block_index = int(os.path.basename(path_to_zip).replace(".zip", ""))

        block = Block(block_index, csv_data[0][2].replace(".cha", ""))

        block.coder = self.codername_entry.get()
        block.lab_key = self.lab_key

        for file in os.listdir(clips_path):
            if file.endswith(".wav"):
                clip_index = int(file.replace(".wav", ""))
                clip = Clip(os.path.join(clips_path, file), block_index, clip_index)
                clip = self.fill_in_clip_info_from_csv(csv_data, clip)
                clip.audio_path = os.path.join(clips_path, file)
                block.clips.append(clip)

        block.sort_clips()

        block.id = block.clan_file + ":::" + str(block.index)

        return block

    def create_block_from_clips(self, path_to_zip):
        clips_path = os.path.dirname(path_to_zip)

        # read the block's metadata from the csv file
        csv_files = [x for x in os.listdir(clips_path) if ".csv" in x]
        csv_file = ""
        if len(csv_files) == 1:
            csv_file = csv_files[0]

        csv_data = []

        csv_path = os.path.join(clips_path, csv_file)
        with open(csv_path, "rU") as csv_input:
            reader = csv.reader(csv_input)
            reader.next()
            for row in reader:
                csv_data.append(row)

        block_index = int(os.path.basename(path_to_zip).replace(".zip", ""))

        block = Block(block_index, csv_data[0][2].replace(".cha", ""))

        block.coder = self.codername_entry.get()
        block.lab_key = self.lab_key

        for file in os.listdir(clips_path):
            if file.endswith(".wav"):
                clip_index = int(file.replace(".wav", ""))
                clip = Clip(os.path.join(clips_path, file), block_index, clip_index)
                clip = self.fill_in_clip_info_from_csv(csv_data, clip)
                clip.audio_path = os.path.join(clips_path, file)
                block.clips.append(clip)

        block.sort_clips()

        block.id = block.clan_file + ":::" + str(block.index)

        return block

    def fill_in_clip_info_from_csv(self, csv_array, clip):
        clip_row = [row for row in csv_array if int(row[6]) == clip.clip_index]

        if len(clip_row) == 1:
            clip_row=clip_row[0]
        else:
            print "something wrong with the input csv. duplicate clips: clip# {}"\
                .format(clip.clip_index)

        clip.clan_file = clip_row[2]
        clip.audio_file = clip_row[3]
        clip.block_index = clip_row[4]
        clip.timestamp = clip_row[5]
        clip.clip_tier = clip_row[7]
        clip.multi_tier_parent = clip_row[9]

        if clip.multi_tier_parent != "N":
            clip.multiline = True
        else:
            clip.multiline = False

        time = clip.timestamp.split("_")
        time = [int(time[0]), int(time[1])]
        final_time = self.ms_to_hhmmss(time)

        clip.start_time = str(final_time[0])
        clip.offset_time = str(final_time[2])

        return clip

    def load_previous_block2(self, event):
        selected_block = self.previous_block_menu.curselection()
        randomized_index = int(self.previous_block_menu.get(selected_block[0])[1:6].strip())
        #print self.previous_block_menu.get(selected_block[0])[1:6].strip()
        self.load_block(randomized_index)

    def load_previous_block_downloaded(self, event):
        selected_block = self.previous_block_menu.curselection()
        index = int(selected_block[0])
        self.load_downloaded_block(index)

    def load_previous_block(self):

        if self.current_block_index is None:
            self.current_block_index = 0
        elif self.current_block_index == 0:
            return
        elif self.current_block_index == len(self.randomized_blocks):
            print "That's the last block"
        else:
            #self.current_block_index -= 1
            last_curr_block = self.loaded_block_history.index(self.current_block_index)
            self.current_block_index = self.loaded_block_history[last_curr_block-1]

        self.block_list.delete(0, END)

        self.current_block = self.randomized_blocks[self.current_block_index]

        self.slice_block(self.current_block)

        for index, element in enumerate(self.randomized_blocks[self.current_block_index].clips):
            if element.multiline:
                self.block_list.insert(index, element.clip_tier+" ^--")
            else:
                self.block_list.insert(index, element.clip_tier)

        self.coded_block_label = Label(self.main_frame, text="block #{}".format(self.current_block_index + 1))
        self.coded_block_label.grid(row=26, column=3)

        self.current_clip = self.current_block.clips[0]

        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(0)

        self.update_curr_clip_info()

    def load_random_conv_block(self):

        if not self.current_block:
            self.current_block_index = 0
            self.current_block = self.randomized_blocks[0]
            self.on_first_block = True
        else:
            self.on_first_block = False

        if self.block_condition_var.get() == 1:
            if not self.on_first_block:
                self.move_currblock_forward()
                self.current_block = self.randomized_blocks[self.current_block_index]
            while not self.current_block.contains_fan_or_man:
                self.move_currblock_forward()
                self.current_block = self.randomized_blocks[self.current_block_index]
        else:
            self.move_currblock_forward()
            self.current_block = self.randomized_blocks[self.current_block_index]

        self.block_list.delete(0, END)

        if self.current_block_index not in self.loaded_block_history:
            self.loaded_block_history.append((self.current_block_index, self.current_block.index))

        self.sort_and_prune_block_history()

        self.slice_block(self.current_block)

        for index, element in enumerate(self.current_block.clips):
            if element.multiline:
                self.block_list.insert(index, element.clip_tier+" ^--")
            else:
                self.block_list.insert(index, element.clip_tier)

        self.coded_block_label = Label(self.main_frame, text="block #{}".format(self.current_block_index + 1))
        self.coded_block_label.grid(row=26, column=3)

        self.current_clip = self.current_block.clips[0]

        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(0)

        self.update_curr_clip_info()

    def sort_and_prune_block_history(self):
        self.loaded_block_history = list(set(self.loaded_block_history))
        self.loaded_block_history = sorted(self.loaded_block_history, key=itemgetter(0))

        self.previous_block_menu.delete(0, END)
        for index, element in enumerate(self.loaded_block_history):
            self.previous_block_menu.insert(index, "#{:>5}:   block {:>6}".format(element[0]+1, element[1]))

        self.previous_block_menu.see(self.previous_block_menu.size()-1)

    def load_block(self, randomized_index):
        self.current_block = self.randomized_blocks[randomized_index-1]
        self.current_block_index = randomized_index

        self.block_list.delete(0, END)

        for index, element in enumerate(self.current_block.clips):
            if element.multiline:
                self.block_list.insert(index, element.clip_tier + " ^--")
            else:
                self.block_list.insert(index, element.clip_tier)

        self.coded_block_label = Label(self.main_frame, text="block #{}".format(self.current_block_index + 1))
        self.coded_block_label.grid(row=26, column=3)

        self.current_clip = self.current_block.clips[0]

        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(0)

        self.update_curr_clip_info()

    def load_downloaded_block(self, block_index):
        self.current_block = self.clip_blocks[block_index]
        self.current_block_index = block_index

        self.block_list.delete(0, END)

        for index, element in enumerate(self.current_block.clips):
            # if element.multiline:
            #     self.block_list.insert(index, element.clip_tier + " ^--")
            #     if element.clip_tier not in ["FAN", "MAN"]:
            #         self.block_list.itemconfig(index, fg="grey")
            # else:
            self.block_list.insert(index, element.clip_tier)
            if element.clip_tier not in ["FAN", "MAN"]:
                self.block_list.itemconfig(index, fg="grey")

        self.coded_block_label = Label(self.main_frame, text="block #{}".format(self.current_block_index + 1))
        self.coded_block_label.grid(row=26, column=3)

        self.current_clip = self.current_block.clips[0]

        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(0)

        self.update_curr_clip_info()

    def move_currblock_forward(self):
        if self.current_block_index is None:
            self.current_block_index = 0
        elif self.current_block_index == len(self.randomized_blocks):
            print "That's the last block"
        else:
            self.current_block_index = self.last_tried_block + 1
            self.last_tried_block += 1
            self.current_block = self.randomized_blocks[self.current_block_index]

    def update_curr_clip_info(self):

        self.curr_clip_info.configure(state="normal")
        self.curr_clip_info.delete("1.0", END)

        block       = "block:        {}\n".format(self.current_clip.block_index)
        clip        = "clip:         {}\n".format(self.current_clip.clip_index)
        tier        = "tier:         {}\n".format(self.current_clip.clip_tier)

        time        = "timestamp:    {}\n".format(self.current_clip.timestamp)
        clip_length = "clip length:  {}\n".format(self.current_clip.offset_time)
        coder       = "coder:        {}\n".format(self.current_clip.coder)
        clanfile    = "clan file:    {}\n\n\n".format(self.current_clip.clan_file)
        label       = "label:        {}\n".format(self.current_clip.classification)
        gender      = "gender:       {}\n".format(self.current_clip.gender_label)

        info_string = "{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n\n\n{}       {}\n{}   {}\n"\
                        .format("block:",
                                str(self.current_clip.block_index),
                                "clip:",
                                str(self.current_clip.clip_index),
                                "tier:",
                                str(self.current_clip.clip_tier),
                                "timestamp:",
                                str(self.current_clip.timestamp),
                                "clip length:",
                                str(self.current_clip.offset_time),
                                "clan file:",
                                str(self.current_clip.clan_file),
                                "coder:",
                                str(self.current_clip.coder),
                                "label:",
                                str(self.current_clip.classification),
                                "gender:",
                                str(self.current_clip.gender_label))

        # self.curr_clip_info.insert('1.0',
        #                             block+\
        #                             clip+\
        #                             tier+\
        #                             time+\
        #                             clip_length+\
        #                             coder+\
        #                             clanfile+\
        #                             label+\
        #                             gender)

        self.curr_clip_info.insert('1.0', info_string)

        self.curr_clip_info.tag_add("label", 10.6, 11.0)
        self.curr_clip_info.tag_add("gender", 11.7, 12.0)
        self.curr_clip_info.tag_configure("label", foreground="red")
        self.curr_clip_info.tag_configure("gender", foreground="#333ccc333")

        self.curr_clip_info.tag_add("block_key", 1.0, 1.5)
        self.curr_clip_info.tag_add("clip_key", 2.0, 2.4)
        self.curr_clip_info.tag_add("tier_key", 3.0, 3.4)
        self.curr_clip_info.tag_add("timestamp_key", 4.0, 4.9)
        self.curr_clip_info.tag_add("clip_length_key", 5.0, 5.11)
        self.curr_clip_info.tag_add("clan_file_key", 6.0, 6.9)
        self.curr_clip_info.tag_add("coder_key", 7.0, 7.6)
        self.curr_clip_info.tag_add("label_key", 10.0, 10.5)
        self.curr_clip_info.tag_add("gender_key", 11.0, 11.6)

        self.curr_clip_info.tag_add("block_value", 1.5, 2.0)
        self.curr_clip_info.tag_add("clip_value", 2.4, 3.0)
        self.curr_clip_info.tag_add("tier_value", 3.4, 4.0)
        self.curr_clip_info.tag_add("timestamp_value", 4.9, 5.0)
        self.curr_clip_info.tag_add("clip_length_value", 5.11, 6.0)
        self.curr_clip_info.tag_add("coder_value", 7.5, 8.0)
        self.curr_clip_info.tag_add("clan_file_value", 6.9, 7.0)
        self.curr_clip_info.tag_add("label_value", 10.5, 11.0)
        self.curr_clip_info.tag_add("gender_value", 11.6, 12.0)

        self.curr_clip_info.tag_configure("block_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("clip_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("tier_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("timestamp_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("clip_length_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("coder_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("clan_file_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("label_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("gender_key", font=("System", "12", "bold"))

        self.curr_clip_info.tag_configure("block_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("clip_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("tier_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("timestamp_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("clip_length_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("coder_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("clan_file_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("label_value", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("gender_value", font=("System", "12", "bold"))

        self.curr_clip_info.configure(state="disabled")

    def next_clip(self):

        if self.current_clip.clip_index == len(self.current_block.clips):
            return
        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(self.current_clip.clip_index)

        self.current_clip = self.current_block.clips[self.current_clip.clip_index]

        self.update_curr_clip_info()

        self.block_list.see(self.current_clip.clip_index-1)

    def previous_clip(self):

        if self.current_clip.clip_index == 1:
            return

        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(self.current_clip.clip_index-2)

        self.current_clip = self.current_block.clips[self.current_clip.clip_index-2]

        self.update_curr_clip_info()

        self.block_list.see(self.current_clip.clip_index-1)

    def set_curr_clip(self, index):
        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(index)

        self.current_clip = self.current_block.clips[index]

    def set_curr_block_dontshare(self):
        if self.current_block:
            if self.dont_share_var.get() == 1:
                self.current_block.dont_share = True
            else:
                self.current_block.dont_share = False

    def update_curr_clip(self, evt):
        if self.block_list.size() == 0:
            return
        box = evt.widget
        index = int(box.curselection()[0])
        value = box.get(index)
        self.current_clip = self.current_block.clips[index]
        self.update_curr_clip_info()

    def ms_to_hhmmss(self, interval):

        x_start = datetime.timedelta(milliseconds= interval[0])
        x_end = datetime.timedelta(milliseconds=interval[1])

        x_diff = datetime.timedelta(milliseconds=interval[1]-interval[0])

        start = ""
        if interval[0] == 0:
            start = "0"+x_start.__str__()[:11]+".000"
        else:

            start = "0"+x_start.__str__()[:11]
            if start[3] == ":":
                start = start[1:]
        end = "0"+x_end.__str__()[:11]
        if end[3] == ":":
            end = end[1:]

        return [start, end, x_diff]

    def set_clip_path(self):
        self.clip_directory = tkFileDialog.askdirectory()
        self.prev_downl_blocks = self.load_previously_downl_blocks()
        self.clip_blocks.extend(self.prev_downl_blocks)
        self.print_paths()

    def save_as_classifications(self, event):
        self.set_classification_output()

    def set_classification_output(self):
        self.classification_output = tkFileDialog.asksaveasfilename()
        self.print_paths()

    def save_classifications(self, event):
        self.output_classifications()

    def output_classifications(self):

        #[date, coder, clanfile, audiofile, block, timestamp, clip, tier, label, multi-tier]
        if not self.classification_output:
            self.classification_output = tkFileDialog.asksaveasfilename()

        with open(self.classification_output, "wb") as output:
            writer = csv.writer(output)
            writer.writerow(["date", "coder", "clan_file", "audiofile", "block",
                             "timestamp", "clip", "tier", "label", "gender", "dont_share"])

            block = self.current_block
            dont_share = False
            if block.dont_share:
                dont_share = True

            multitier_parent = None
            for clip in block.clips:
                # if clip.multiline:
                #     multitier_parent = clip.multi_tier_parent
                # else:
                #     multitier_parent = "N"

                writer.writerow([clip.label_date, clip.coder, clip.clan_file,
                                 clip.parent_audio_path, clip.block_index,
                                 clip.timestamp, clip.clip_index,clip.clip_tier,
                                 clip.classification, clip.gender_label, dont_share])

    def blocks_to_csv(self):

        with open("blocks.csv", "wb") as file:
            writer = csv.writer(file)
            writer.writerow(["block", "num_clips"])
            for block in self.clip_blocks:
                writer.writerow([block.index, block.num_clips])

    def show_shortcuts(self):
        self.shortcuts_menu = Toplevel()
        self.shortcuts_menu.title("Shortcuts")
        self.shortcuts_menu.geometry("540x470")
        textbox = Text(self.shortcuts_menu, width=90, height=30)
        textbox.pack()


        general = "General Keys:\n\n"
        load_audio      = "\tshift + a             : load audio file\n"
        load_clan       = "\tshift + c             : load clan file\n"
        submit_block    = "\tshift + enter         : submit block\n"
        load_prev_block = "\tshift + \             : load previous block\n"
        save_labels     = "\tcmd   + s             : save classifications     (Mac)\n"
        save_labels_win = "\tctrl  + s             : save classifications     (Linux/Windows)\n"
        save_as         = "\tcmd   + shift + s     : save as classifications  (Mac)\n"
        save_as_win     = "\tctrl  + shift + s     : save as classifications  (Linux/Windows)\n"

        classification = "\nClassification Keys:\n\n"
        ids        = "\tc : CDS\n"
        ads        = "\ta : ADS\n"
        noise      = "\tn : Child Noises\n"
        reg_switch = "\tr : Register Switch\n"
        mult_addr  = "\tm : Multiple Addressee\n"
        junk       = "\tj : Junk\n\n"

        male       = "\tM : Male\n"
        female     = "\tF : Female\n"
        unclear    = "\tU : Unclear\n"

        clips = "\nClip Navigation/Playback Keys:\n\n"
        up         = "\tup            : previous clip\n"
        left       = "\tleft          : previous clip\n"
        down       = "\tdown          : next clip\n"
        right      = "\tright         : next clip\n"
        space      = "\tspace         : play clip\n"
        shft_space = "\tshift + space : play whole block\n"

        textbox.insert('1.0', general+\
                                #load_audio+\
                                #load_clan+\
                                #load_block+\
                                #load_prev_block+\
                                submit_block+\
                                save_labels+\
                                save_labels_win+\
                                save_as+\
                                save_as_win+\
                                classification+\
                                ids+\
                                ads+
                                noise+\
                                reg_switch+\
                                mult_addr+\
                                junk+\
                                male+\
                                female+\
                                unclear+\
                                clips+\
                                up+
                                left+\
                                down+\
                                right+\
                                space+\
                                shft_space)

        textbox.configure(state="disabled")

    def show_about(self):
        global version
        self.about_page = Toplevel()
        self.about_page.title("About")
        self.about_page.geometry("450x400")
        textbox = Text(self.about_page, width=55, height=30)
        textbox.pack()

        textbox.tag_add("all", "1.0", END)
        textbox.tag_add("title", "1.0", "2.0")
        textbox.tag_config("all", justify="center")
        textbox.tag_config("title", font=("Georgia", "12", "bold"))

        name = "\n\n\n\nIDS Label\n"
        version = "v{}\n\n".format(version)
        author = "author: Andrei Amatuni\n"
        homepage = "homepage: https://github.com/SeedlingsBabylab/idslabel"
        textbox.insert('1.0', name+version+author+homepage)

        textbox.configure(state="disabled")

    def check_github_for_latest_version(self):
        resp = urllib2.urlopen("https://api.github.com/repos/SeedlingsBabylab/idslabel/tags")

        json_response =  json.loads(resp.read())

        git_version = json_response[0]["name"]
        split_version = git_version[1:].split(".")

        split_version = map(int, split_version)
        int_this_version = map(int, version.split("."))

        less = False
        for index, num in enumerate(int_this_version):
            if num < split_version[index]:
                less = True
                break

        if less:
            showwarning("Old Version",
                        "This isn't the latest version of IDSLabel\nGet the latest release from: "
                                       "\n\nhttps://github.com/SeedlingsBabylab/idslabel/releases")

    def print_paths(self):
        self.paths_text = Text(self.main_frame, width=65, pady=40)
        self.paths_text.grid(row=28, column=0, rowspan=4, columnspan=2)

        if not self.audio_file:
            audiofile = None
        else:
            audiofile = os.path.split(self.audio_file)[1]

        if not self.classification_output:
            outputfile = None
        else:
            outputfile = os.path.split(self.classification_output)[1]

        clipsdir = self.clip_directory

        if audiofile:
            audio_filepath =  "audio  file:        {}\n".format(audiofile)
        else:
            audio_filepath =  "audio  file:        {}\n".format("N/A")

        if outputfile:
            output_filepath = "output file:        {}\n".format(outputfile)
        else:
            output_filepath = "output file:        {}\n".format("N/A")

        if clipsdir:
            clips_dir =       "clips  directory:   {}\n".format(clipsdir)
        else:
            clips_dir =       "clips  directory:   {}\n".format("N/A")

        self.paths_text.insert("1.0",
                               audio_filepath+\
                               output_filepath+\
                               clips_dir)

        self.paths_text.configure(state="disabled")

    def get_blocks(self):
        if not self.clip_directory:
            showwarning("Set Audio Clips Directory", "You need to have a directory set before downloading blocks\n\n"+
                        "(File -> Set Block Path)")
            return
        if self.codername_entry.get() == "CODER_NAME":
            showwarning("Set Coder Name", "You need to set CODER_NAME before requesting blocks")
            return

        error_response = ""
        for i in range(self.num_blocks_to_get):
            error_response = self.get_block()

        if error_response:
            showwarning("Bad Request", "Server: " + error_response)
            #return

        self.load_downloaded_blocks()

    def get_block(self):
        payload = {}
        payload["lab-key"] = self.lab_key
        payload["username"] = self.codername_entry.get()

        if not get_block_url:
            self.parse_config()

        resp = requests.post(get_block_url, json=payload, stream=True, allow_redirects=False)

        if resp.status_code != 200:
            return resp.content

        if resp.ok:

            params = cgi.parse_header(resp.headers.get('Content-Disposition', ''))
            filename = params[1]['filename']
            file_end = os.path.basename(filename)
            file_root = "{}_{}_block{}".format(self.codername_entry.get(), os.path.dirname(filename), file_end)
            block_path = os.path.join(self.clip_directory, file_root)

            if not os.path.exists(block_path):
                os.makedirs(block_path)


            output_path = os.path.join(block_path, file_end)

            with open(output_path, "wb") as output:
                output.write(resp.content)

            block = self.create_block_from_zip(output_path)

            print block
            self.clip_blocks.append(block)

    def get_lab_info(self):
        self.lab_info_page = Toplevel()
        self.lab_info_page.title("Lab Info")
        self.lab_info_page.geometry("1040x400")

        users_label = Label(self.lab_info_page, text="Users")
        users_label.grid(row=0, column=0)

        work_item_label = Label(self.lab_info_page, text="Active Blocks")
        work_item_label.grid(row=0, column=1)

        work_item_label = Label(self.lab_info_page, text="Finished Blocks")
        work_item_label.grid(row=0, column=2)


        self.lab_info_user_box = Listbox(self.lab_info_page, width=15, height=20)
        self.lab_info_user_box.grid(row=1, column=0, rowspan=9)
        self.lab_info_user_box.bind('<<ListboxSelect>>', self.update_curr_user)

        self.lab_info_user_work_box = Listbox(self.lab_info_page, width=22, height=20)
        self.lab_info_user_work_box.grid(row=1, column=1, rowspan=9)


        self.lab_info_user_past_work_box = Listbox(self.lab_info_page, width=22, height=20)
        self.lab_info_user_past_work_box.grid(row=1, column=2, rowspan=9)
        self.lab_info_user_past_work_box.bind('<<ListboxSelect>>', self.get_labels)

        self.lab_info_past_work_box = Listbox(self.lab_info_page, width=10, height=20)
        self.lab_info_past_work_box.grid(row=1, column=3, rowspan=9)
        self.lab_info_past_work_box.bind('<<ListboxSelect>>', self.update_lab_info_curr_clip)

        self.lab_info_past_work_info = Text(self.lab_info_page, width=38, height=20)
        self.lab_info_past_work_info.grid(row=1, column=4, rowspan=9)

        save_this_block_button = Button(self.lab_info_page, text="Save This Block", command=self.lab_info_save_this_block)
        save_this_block_button.grid(row=0, column=5)

        save_all_lab_blocks_button = Button(self.lab_info_page, text="Save Lab Blocks", command=self.lab_info_save_lab_blocks)
        save_all_lab_blocks_button.grid(row=1, column=5, )

        save_all_blocks_button = Button(self.lab_info_page, text="Save All Blocks", command=self.lab_info_save_all_blocks)
        save_all_blocks_button.grid(row=2, column=5)

        payload = {"lab-key": self.lab_key}

        resp = requests.post(lab_info_url, json=payload, allow_redirects=False)

        if resp.ok:
            self.lab_data = json.loads(resp.content)

            i = 0
            for key, value in self.lab_data['users'].iteritems():
                self.lab_info_user_box.insert(i, value['name'])
                self.lab_users.append(value["name"])
                i+=1

    def get_all_lab_info(self):
        self.all_lab_info_page = Toplevel()
        self.all_lab_info_page.title("All Lab Info")
        self.all_lab_info_page.geometry("450x400")

        labs_label = Label(self.all_lab_info_page, text="Labs")
        labs_label.grid(row=0, column=0)

        users_label = Label(self.all_lab_info_page, text="Users")
        users_label.grid(row=0, column=1)

        self.all_lab_info_lab_box = Listbox(self.all_lab_info_page, width=15, height=20)
        self.all_lab_info_lab_box.grid(row=1, column=0)
        self.all_lab_info_lab_box.bind('<<ListboxSelect>>', self.update_curr_lab)

        self.all_lab_info_user_box = Listbox(self.all_lab_info_page, width=15, height=20)
        self.all_lab_info_user_box.grid(row=1, column=1)

        payload = {"lab-key": "1234567654321"}

        resp = requests.post(all_lab_info_url, json=payload, allow_redirects=False)

        if resp.ok:
            self.all_lab_data = json.loads(resp.content)

            for index, lab in enumerate(self.all_lab_data):
                self.all_lab_info_lab_box.insert(index, lab['key'])

    def lab_info_ping(self):
        if not lab_info_url:
            self.parse_config()

        payload = {"lab-key": self.lab_key}


        resp = requests.post(lab_info_url, json=payload, allow_redirects=False)

        if resp.ok:
            self.lab_data = json.loads(resp.content)
            return self.lab_data
        else:
            showwarning("Bad Request", "User: \"{}\" does not exist on the server.\n\n".format(self.codername_entry.get())+\
                                       "(File -> Add User to Server)")
            print resp.content
            return

    def update_curr_lab(self, evt):
        box = evt.widget
        index = int(box.curselection()[0])

        lab = self.all_lab_data[index]

        i = 0
        for name, user in lab["users"].iteritems():
            self.all_lab_info_user_box.insert(i, user["name"])
            i += 1


        print "index: {}".format(index)

    def update_curr_user(self, evt):
        box = evt.widget
        index = int(box.curselection()[0])

        user = box.get(index)
        user_data = self.lab_data["users"][str(user)]

        i = 0
        self.lab_info_user_work_box.delete(0, END)
        if user_data["active-work-items"]:
            for item in user_data["active-work-items"]:
                self.lab_info_user_work_box.insert(i, item["id"])
                i += 1

        i = 0
        self.lab_info_user_past_work_box.delete(0, END)
        if user_data["finished-work-items"]:
            for item in user_data["finished-work-items"]:
                self.lab_info_user_past_work_box.insert(i, item["id"])
                i += 1

    def add_user_to_server(self):
        name = tkSimpleDialog.askstring(title="Add User",
                                        prompt="Username:",
                                        initialvalue=self.codername_entry.get())

        payload = {"lab-key": self.lab_key,
                   "lab-name": self.lab_name,
                   "username": name}

        resp = requests.post(add_user_url, json=payload, allow_redirects=False)

    def parse_config(self):
        global get_block_url
        global lab_info_url
        global all_lab_info_url
        global add_user_url
        global submit_labels_url
        global get_labels_url
        global get_labels_url
        global get_lab_labels_url
        global get_all_labels_url
        global send_back_blocks_url

        showwarning("Config File", "Please choose a config.json file to load")
        config_path = tkFileDialog.askopenfilename()

        with open(config_path, "rU") as input:
            config = json.load(input)

            self.lab_key = config["lab-key"]
            self.lab_name = config["lab-name"]

            get_block_url = config["server-urls"]["get_block_url"]
            lab_info_url = config["server-urls"]["lab_info_url"]
            all_lab_info_url = config["server-urls"]["all_lab_info_url"]
            add_user_url = config["server-urls"]["add_user_url"]
            submit_labels_url = config["server-urls"]["submit_labels_url"]
            get_labels_url = config["server-urls"]["get_labels_url"]
            get_lab_labels_url = config["server-urls"]["get_lab_labels_url"]
            get_all_labels_url = config["server-urls"]["get_all_labels_url"]
            send_back_blocks_url = config["server-urls"]["send_back_blocks_url"]

    def submit_block(self):
        # check that the current block is completed before submitting
        block = self.current_block
        unfinished_clips = []
        for clip in block.clips:
            if clip.clip_tier == "FAN" or clip.clip_tier == "MAN":
                if not clip.classification:
                    unfinished_clips.append(clip)
                if not clip.gender_label:
                    unfinished_clips.append(clip)

        if not unfinished_clips:
            submission = block.to_dict()
            resp = requests.post(submit_labels_url, json=submission, allow_redirects=False)

            if resp.status_code != 200:
                showwarning("Bad Request", "Server: " + resp.content)
                return

            if resp.ok:
                print "everything is ok"
                self.cleanup_block_data(block)
                block_index = self.clip_blocks.index(block)
                del self.clip_blocks[block_index]
        else:
            showwarning("Incomplete Block", "You haven't classified all the FAN/MAN tiered clips within this block")
            return

        self.block_list.delete(0, END)
        self.load_downloaded_blocks()

    def submit_block_and_save(self):
        if not self.session_output_file:
            showwarning("Set Output File", "Please choose a csv file to save this session's blocks to")
            self.session_output_file = tkFileDialog.asksaveasfilename()

        # check that the current block is completed before submitting
        block = self.current_block
        unfinished_clips = []
        for clip in block.clips:
            if clip.clip_tier == "FAN" or clip.clip_tier == "MAN":
                if not clip.classification:
                    unfinished_clips.append(clip)
                if not clip.gender_label:
                    unfinished_clips.append(clip)

        if not unfinished_clips:
            self.write_block_to_session_out(block)
            self.submit_block()
        else:
            showwarning("Incomplete Block", "You haven't classified all the FAN/MAN tiered clips within this block")
            return

    def submit_all_blocks(self):
        blocks = self.get_completed_blocks()

        if len(blocks[1]) > 0:
            incomplete_blocks = ""
            for block in blocks[1]:
                incomplete_blocks += str(block.index) + " "
            showwarning("Incomplete Blocks", "You haven't finished some of the blocks\n\n"+
                        "blocks #: "+ incomplete_blocks + "\n\n" + "Only sending completed blocks")


        for block in blocks[0]:
            submission = block.to_dict()
            resp = requests.post(submit_labels_url, json=submission, allow_redirects=False)

            if resp.status_code != 200:
                showwarning("Bad Request", "Server: " + resp.content)
                return

            if resp.ok:
                print "everything is ok"
                self.cleanup_block_data(block)
                block_index = self.clip_blocks.index(block)
                del self.clip_blocks[block_index]

        self.block_list.delete(0, END)
        self.load_downloaded_blocks()

    def labels_to_json(self):

        blocks = {}
        blocks["blocks"] = {}

        for block in self.clip_blocks:
            blocks["blocks"][block.id] = []

        for block in self.clip_blocks:
            for clip in block.clips:
                blocks["blocks"][block.id].append(clip.to_dict())

        return blocks

    def get_completed_blocks(self):
        completed_blocks = []
        incomplete_blocks = []
        for block in self.clip_blocks:
            unfinished_clips = []
            for clip in block.clips:
                if clip.clip_tier == "FAN" or clip.clip_tier == "MAN":
                    if not clip.classification:
                        unfinished_clips.append(clip)
                    if not clip.gender_label:
                        unfinished_clips.append(clip)

            if len(unfinished_clips) > 0:
                incomplete_blocks.append(block)
            else:
                completed_blocks.append(block)

        return (completed_blocks, incomplete_blocks)

    def load_downloaded_blocks(self):

        self.previous_block_menu.delete(0, END)
        for index, block in enumerate(self.clip_blocks):
            block_string = "{} : {}".format(index+1, block.index)
            if block.old:
                block_string += "  [old]"
            else:
                block_string += "  [new]"
            self.previous_block_menu.insert(index, block_string)

    def load_previously_downl_blocks(self):
        blocks = []

        self.lab_info_ping()

        user = self.codername_entry.get()

        if not self.lab_data:
            return

        users = self.lab_data["users"]

        if user not in users:
            showwarning("Set Coder Name", "CODER_NAME: \"{}\" , is not known by the server.\n\n".format(user) +\
            "Either add it (File -> Add User to Server), or use an already registered name")
            return []

        user_data = users[user]
        user_active_blocks = user_data["active-work-items"]

        for root, dirs, files in os.walk(self.clip_directory):
            if any(".zip" in file for file in files):
                zips = [x for x in files if ".zip" in x]
                if len(zips) > 0:
                    zipfile = os.path.join(root, zips[0])
                    block = self.create_block_from_clips(zipfile)
                    block.old = True
                    if self.block_belongs_to_user(block, user_active_blocks):
                        blocks.append(block)

        return blocks

    def block_belongs_to_user(self, block, user_active_items):
        if user_active_items is None:
            return False

        for element in user_active_items:
            if element["id"] == block.id:
                return True
        return False

    def enter_block_request_num(self, event):
        self.main_frame.focus_set()
        self.num_blocks_to_get = int(self.block_request_num_entry.get())

    def cleanup_block_data(self, block):
        print block
        clips_path = ""
        for clip in block.clips:
            os.remove(clip.audio_path)
            clips_path = os.path.dirname(clip.audio_path)
        shutil.rmtree(clips_path)

    def get_labels(self, evt):
        box = evt.widget
        index = int(box.curselection()[0])

        work_item = box.get(index)

        if not lab_info_url:
            self.parse_config()

        payload = {"lab-key": self.lab_key,
                   "item-id": work_item}

        resp = requests.post(get_labels_url, json=payload, allow_redirects=False)

        block_data = None
        if resp.ok:
            block_data = json.loads(resp.content)
            self.curr_past_block = self.json_to_block(block_data)
            self.load_block_lab_info()
        else:
            showwarning("Bad Request", "Server: {}".format(resp.content))
            return

    def load_block_lab_info(self):

        self.lab_info_past_work_box.delete(0, END)

        for index, element in enumerate(self.curr_past_block.clips):
            self.lab_info_past_work_box.insert(index, element.clip_tier)
            if element.clip_tier not in ["FAN", "MAN"]:
                self.lab_info_past_work_box.itemconfig(index, fg="grey")

        self.lab_info_past_work_box.selection_clear(0, END)
        self.lab_info_past_work_box.selection_set(0)

        self.update_lab_info_curr_clip_initial()

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

    def update_lab_info_curr_clip_initial(self):
        self.lab_info_past_work_box.selection_set(0)
        self.curr_lab_info_clip = self.curr_past_block.clips[0]
        #work_item = box.get(index)

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
        with open(output_path, "wb") as out:
            writer = csv.writer(out)

            writer.writerow(["date", "coder", "clan_file", "audiofile", "block",
                             "timestamp", "clip", "tier", "label", "gender", "dont_share"])

            block = self.curr_past_block
            dont_share = False
            if block.dont_share:
                dont_share = True

            for clip in block.clips:
                writer.writerow([clip.label_date, clip.coder, clip.clan_file,
                                 clip.parent_audio_path, clip.block_index,
                                 clip.timestamp, clip.clip_index, clip.clip_tier,
                                 clip.classification, clip.gender_label, dont_share])

    def lab_info_save_lab_blocks(self):
        output_path = tkFileDialog.asksaveasfilename()

        if not self.lab_key:
            showwarning("Load Config", "You need to load the config.json first")
            return

        payload = {"lab-key": self.lab_key}

        resp = requests.post(get_lab_labels_url, json=payload, allow_redirects=False)

        block_data = None
        if resp.ok:
            block_data = json.loads(resp.content)

        print block_data
        blocks = []
        for block in block_data["blocks"]:
            blocks.append(self.json_to_block(block))

        with open(output_path, "wb") as out:
            writer = csv.writer(out)

            writer.writerow(["date", "coder", "clan_file", "audiofile", "block",
                             "timestamp", "clip", "tier", "label", "gender", "dont_share"])

            for block in blocks:
                dont_share = False
                if block.dont_share:
                    dont_share = True

                for clip in block.clips:
                    writer.writerow([clip.label_date, clip.coder, clip.clan_file,
                                     clip.parent_audio_path, clip.block_index,
                                     clip.timestamp, clip.clip_index, clip.clip_tier,
                                     clip.classification, clip.gender_label, dont_share])

    def lab_info_save_all_blocks(self):
        output_path = tkFileDialog.asksaveasfilename()

        if not self.lab_key:
            showwarning("Load Config", "You need to load the config.json first")
            return

        payload = {"lab-key": self.lab_key}

        resp = requests.post(get_all_labels_url, json=payload, allow_redirects=False)

        block_data = None
        if resp.ok:
            block_data = json.loads(resp.content)

        print block_data
        blocks = []
        for block in block_data["blocks"]:
            blocks.append(self.json_to_block(block))

        with open(output_path, "wb") as out:
            writer = csv.writer(out)

            writer.writerow(["date", "coder", "clan_file", "audiofile", "block",
                             "timestamp", "clip", "tier", "label", "gender", "dont_share"])


            for block in blocks:
                dont_share = False
                if block.dont_share:
                    dont_share = True

                for clip in block.clips:
                    writer.writerow([clip.label_date, clip.coder, clip.clan_file,
                                     clip.parent_audio_path, clip.block_index,
                                     clip.timestamp, clip.clip_index, clip.clip_tier,
                                     clip.classification, clip.gender_label, dont_share])

    def json_to_block(self, block_json):

        block = Block(block_json["block-index"], block_json["clan-file"])
        block.dont_share = block_json["dont-share"]

        for clip in block_json["clips"]:
            block.clips.append(self.json_to_clip(clip, block.index, block.clan_file))

        return block

    def json_to_clip(self, clip_json, block_index, clan_file):

        clip = Clip("", block_index, clip_json["clip-index"])

        clip.clan_file = clan_file
        clip.clip_tier = clip_json["clip-tier"]
        clip.start_time = clip_json["start-time"]
        clip.offset_time = clip_json["offset-time"]
        clip.timestamp = clip_json["timestamp"]
        clip.classification = clip_json["classification"]
        clip.gender_label = clip_json["gender-label"]
        clip.label_date = clip_json["label-date"]
        clip.coder = clip_json["coder"]

        return clip

    def send_blocks_back(self):
        self.send_blocks_back_page = Toplevel()
        self.send_blocks_back_page.title("Send Blocks Back")
        self.send_blocks_back_page.geometry("350x350")

        self.send_back_block_list = Listbox(self.send_blocks_back_page, selectmode=MULTIPLE, width=10, height=15)
        self.send_back_block_list.grid(row=1, column=1)

        send_back_button = Button(self.send_blocks_back_page, text="Send Back", command=self.send_back)
        send_back_button.grid(row=1, column=0)

        self.send_back_block_list.delete(0, END)
        for index, block in enumerate(self.clip_blocks):
            block_string = "{} : {}".format(index+1, block.index)
            if block.old:
                block_string += "  [old]"
            else:
                block_string += "  [new]"
            self.send_back_block_list.insert(index, block_string)

    def send_back(self):

        selections = self.send_back_block_list.curselection()
        selection_ids = []
        selection_blocks = []

        for selection in selections:
            block = self.clip_blocks[selection]
            selection_ids.append(block.id)
            selection_blocks.append(block)

        name = self.codername_entry.get()
        if name == "CODER_NAME":
            showwarning("Set Coder Name", "You need to set your coder name first")
            return

        payload = {"lab-key": self.lab_key,
                   "lab-name": self.lab_name,
                   "username": name,
                   "blocks": []
                   }

        for block in selection_ids:
            payload["blocks"].append(block)

        resp = requests.post(send_back_blocks_url, json=payload, allow_redirects=False)

        print payload

        for block in selection_blocks:
            self.cleanup_block_data(block)
            block_index = self.clip_blocks.index(block)
            del self.clip_blocks[block_index]

        self.send_back_block_list.delete(0, END)
        for index, block in enumerate(self.clip_blocks):
            block_string = "{} : {}".format(index+1, block.index)
            if block.old:
                block_string += "  [old]"
            else:
                block_string += "  [new]"
            self.send_back_block_list.insert(index, block_string)

        self.load_downloaded_blocks()

    def write_block_to_session_out(self, block):
        with open(self.session_output_file, "a") as out:
            writer = csv.writer(out)

            if not self.session_output_header_written:
                writer.writerow(["date", "coder", "clan_file", "audiofile", "block",
                                 "timestamp", "clip", "tier", "label", "gender", "dont_share"])
                self.session_output_header_written = True

            dont_share = False
            if block.dont_share:
                dont_share = True

            for clip in block.clips:
                writer.writerow([clip.label_date, clip.coder, clip.clan_file,
                                 clip.parent_audio_path, clip.block_index,
                                 clip.timestamp, clip.clip_index, clip.clip_tier,
                                 clip.classification, clip.gender_label, dont_share])

if __name__ == "__main__":

    root = Tk()
    MainWindow(root)
    root.mainloop()
