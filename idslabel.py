import pyaudio
import wave
import json
import urllib2
import time
import csv
import re
import os
import requests
import shutil

from Tkinter import *
import tkFileDialog
from tkMessageBox import showwarning, askyesno

from distutils.version import LooseVersion


import labinfo
import getblock
import idsserver
import idsblocks
import idssession

version = "1.0.0"

class MainWindow:

    def __init__(self, master):
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
        if sys.platform == "linux2":
            self.main_frame.bind("<Control-s>", self.save_classifications)
            self.main_frame.bind("<Control-S>", self.save_as_classifications)
        if sys.platform == "win32":
            self.main_frame.bind("<Control-s>", self.save_classifications)
            self.main_frame.bind("<Control-S>", self.save_as_classifications)

        self.menubar = Menu(self.root)

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Save Classifications", command=self.output_classifications)
        self.filemenu.add_command(label="Save As Classifications", command=self.set_classification_output)
        self.filemenu.add_command(label="Set Block Path", command=self.set_clip_path)
        self.filemenu.add_command(label="Load config.json File", command=self.load_config_json)
        self.filemenu.add_command(label="Get Lab Info", command=self.get_lab_info)
        self.filemenu.add_command(label="Choose Blocks From Server", command=self.get_specific_blocks)
        self.filemenu.add_command(label="Add User to Server", command=self.add_user_to_server)
        self.filemenu.add_command(label="Submit Block", command=self.submit_block_and_save)
        self.filemenu.add_command(label="Send Blocks Back", command=self.send_blocks_back)
        self.filemenu.add_command(label="Get Training Blocks", command=self.get_training_blocks)

        self.menubar.add_cascade(label="File", menu=self.filemenu)


        self.helpmenu= Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="About", command=self.show_about)
        self.helpmenu.add_command(label="Show Info & Shortcuts", command=self.show_shortcuts)

        self.menubar.add_cascade(label="Help", menu=self.helpmenu)

        self.root.config(menu=self.menubar)

        self.main_frame.bind("<FocusOut>", self.reset_frame_focus)

        self.main_frame.pack()

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
                                                    text="Save Block",
                                                    command=self.output_classifications)

        self.submit_labels_to_server_and_save_button = Button(self.main_frame,
                                                     text="Submit + Save",
                                                     command=self.submit_block_and_save)



        self.get_blocks_button = Button(self.main_frame,
                                        text="Get Blocks",
                                        command=self.get_blocks)

        self.get_training_blocks_button = Button(self.main_frame,
                                                 text="Get Training Blocks",
                                                 command=self.get_training_blocks)

        self.get_reliability_blocks_button = Button(self.main_frame,
                                                 text="Get Reliability Blocks",
                                                 command=self.get_reliability_blocks)


        self.send_block_back_button = Button(self.main_frame,
                                            text="Send Blocks Back",
                                            command=self.send_blocks_back)

        self.get_blocks_button.grid(row=0, column=2)
        self.get_training_blocks_button.grid(row=1, column=2)
        self.get_reliability_blocks_button.grid(row=2, column=2)

        self.play_block_button.grid(row=4, column=2)
        self.play_clip_button.grid(row=5, column=2)
        self.next_clip_button.grid(row=6, column=2)
        self.output_classifications_button.grid(row=7, column=2)
        self.submit_labels_to_server_and_save_button.grid(row=9, column=2)
        self.send_block_back_button.grid(row=7, column=4)

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

        self.clips_processed_label = None
        self.coded_block_label = None

        self.interval_regx = re.compile("\\x15\d+_\d+\\x15")

        self.main_frame.focus_set()

        self.shortcuts_menu = None

        self.curr_clip_info.configure(state="disabled")

        self.dont_share_var = IntVar()
        self.dont_share_button = Checkbutton(self.main_frame,
                                             text="don't share this block",
                                             variable=self.dont_share_var,
                                             command=self.set_curr_block_dontshare)

        self.dont_share_button.grid(row=3, column=4)

        self.previous_block_label = Label(self.main_frame, text="Load Block:")
        self.previous_block_label.grid(row=4, column=4)

        self.previous_block_menu = Listbox(self.main_frame, width=14, height=10)
        self.previous_block_menu.bind("<Double-Button-1>", self.load_previous_block_downloaded)
        self.previous_block_menu.bind("<FocusIn>", self.reset_frame_focus)
        self.previous_block_menu.grid(row=5, column=4)

        self.classification_output = ""

        #self.show_shortcuts()

        self.key_label_map = {
            "a": "ADS",
            "c": "CDS",
            "j": "JUNK"
        }

        self.gender_label_map = {
            "m": "MALE",
            "f": "FEMALE",
        }

        self.lab_info_page = None
        self.get_block_page = None

        self.send_blocks_back_page = None
        self.send_back_block_list = None

        self.session_output_file = None
        self.session_output_header_written = False

        self.dont_share_applied = False

        self.choose_block_page = None

        self.temp_clip_dir = None

        self.server = idsserver.IDSServer()
        self.session = idssession.Session(self.server)
        self.lab_info_page = None


    def key_select(self, event):
        self.main_frame.focus_set()

        selected_key = event.char

        if selected_key in self.key_label_map:
            if not self.current_clip:
                self.set_curr_clip(0)
            if self.session.codername == "CODER_NAME":
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

            if self.current_clip.classification == "JUNK":
                return
            self.current_clip.label_date = time.strftime("%m/%d/%Y")
            self.current_clip.coder = self.codername_entry.get()
            self.current_clip.gender_label = self.gender_label_map[selected_key]
            self.update_curr_clip_info()

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

    def shortcut_submit_block(self, event):
        self.submit_block_and_save()

    def reset_frame_focus(self, event):
        self.main_frame.focus_set()

    def codername_entered(self, event):
        try:
            self.check_github_for_latest_version()
        except Exception as e:
            print e.message

        if not self.session.clip_directory or not self.temp_clip_dir:
            showwarning("Clips Directory", "Choose directory to store downloaded blocks")
            self.temp_clip_dir = tkFileDialog.askdirectory()
        del self.session.clip_blocks[:]
        self.parse_config()
        self.session.codername = self.codername_entry.get()
        self.session.clip_directory = self.temp_clip_dir
        self.session.prev_downl_blocks = self.load_previously_downl_blocks()
        if self.session.prev_downl_blocks:
            self.session.clip_blocks.extend(self.session.prev_downl_blocks)
        self.load_downloaded_blocks()
        self.main_frame.focus_set()

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

    def load_previous_block_downloaded(self, event):
        selected_block = self.previous_block_menu.curselection()
        index = int(selected_block[0])
        self.load_downloaded_block(index)

    def load_downloaded_block(self, block_index):
        self.dont_share_applied = False
        self.current_block = self.session.clip_blocks[block_index]
        self.current_block_index = block_index

        self.block_list.delete(0, END)

        for index, element in enumerate(self.current_block.clips):
            self.block_list.insert(index, element.clip_tier)
            if element.clip_tier not in ["FAN", "MAN"]:
                self.block_list.itemconfig(index, fg="grey", selectforeground="grey")

        self.coded_block_label = Label(self.main_frame, text="block #{}".format(self.current_block_index + 1))
        self.coded_block_label.grid(row=26, column=3)

        self.current_clip = self.current_block.clips[0]

        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(0)

        self.dont_share_button.deselect()

        self.update_curr_clip_info()

    def update_curr_clip_info(self):

        self.curr_clip_info.configure(state="normal")
        self.curr_clip_info.delete("1.0", END)

        info_string = "{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n{}   {}\n\n\n{}       {}\n{}   {}\n"\
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
                                "block length:",
                                str(self.current_block.length),
                                "clan file:",
                                str(self.current_clip.clan_file),
                                "coder:",
                                str(self.current_clip.coder),
                                "label:",
                                str(self.current_clip.classification),
                                "gender:",
                                str(self.current_clip.gender_label))

        self.curr_clip_info.insert('1.0', info_string)

        self.curr_clip_info.tag_add("label", 11.6, 12.0)
        self.curr_clip_info.tag_add("gender", 12.7, 13.0)
        self.curr_clip_info.tag_configure("label", foreground="red")
        self.curr_clip_info.tag_configure("gender", foreground="#333ccc333")

        self.curr_clip_info.tag_add("block_key", 1.0, 1.5)
        self.curr_clip_info.tag_add("clip_key", 2.0, 2.4)
        self.curr_clip_info.tag_add("tier_key", 3.0, 3.4)
        self.curr_clip_info.tag_add("timestamp_key", 4.0, 4.9)
        self.curr_clip_info.tag_add("clip_length_key", 5.0, 5.11)
        self.curr_clip_info.tag_add("block_length_key", 6.0, 6.13)
        self.curr_clip_info.tag_add("clan_file_key", 7.0, 7.9)
        self.curr_clip_info.tag_add("coder_key", 8.0, 8.6)
        self.curr_clip_info.tag_add("label_key", 11.0, 11.5)
        self.curr_clip_info.tag_add("gender_key", 12.0, 12.6)

        self.curr_clip_info.tag_add("block_value", 1.5, 2.0)
        self.curr_clip_info.tag_add("clip_value", 2.4, 3.0)
        self.curr_clip_info.tag_add("tier_value", 3.4, 4.0)
        self.curr_clip_info.tag_add("timestamp_value", 4.9, 5.0)
        self.curr_clip_info.tag_add("clip_length_value", 5.11, 6.0)
        self.curr_clip_info.tag_add("block_length_value", 6.14, 7.0)
        self.curr_clip_info.tag_add("coder_value", 8.5, 9.0)
        self.curr_clip_info.tag_add("clan_file_value", 7.9, 8.0)
        self.curr_clip_info.tag_add("label_value", 11.5, 12.0)
        self.curr_clip_info.tag_add("gender_value", 12.6, 13.0)

        self.curr_clip_info.tag_configure("block_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("clip_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("tier_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("timestamp_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("clip_length_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("block_length_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("coder_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("clan_file_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("label_key", font=("System", "12", "bold"))
        self.curr_clip_info.tag_configure("gender_key", font=("System", "12", "bold"))

        self.curr_clip_info.tag_configure("block_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("clip_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("tier_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("timestamp_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("clip_length_value", font=("System", "12"))
        self.curr_clip_info.tag_configure("block_length_value", font=("System", "12"))
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
                self.dont_share_applied = True
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

    def set_clip_path(self):
        self.session.clip_directory = tkFileDialog.askdirectory()
        self.session.prev_downl_blocks = self.load_previously_downl_blocks()
        self.session.clip_blocks.extend(self.session.prev_downl_blocks)

    def save_as_classifications(self, event):
        self.set_classification_output()

    def set_classification_output(self):
        self.classification_output = tkFileDialog.asksaveasfilename()
        self.output_classifications()

    def save_classifications(self, event):
        self.output_classifications()

    def output_classifications(self):
        if not self.classification_output:
            self.classification_output = tkFileDialog.asksaveasfilename()

        idsblocks.save_blocks_to_csv([self.current_block], self.classification_output)

    def show_shortcuts(self):
        self.shortcuts_menu = Toplevel()
        self.shortcuts_menu.title("Shortcuts & Info")
        self.shortcuts_menu.geometry("540x500")
        textbox = Text(self.shortcuts_menu, width=90, height=35)
        textbox.pack()

        welcome_message = "Welcome to IDSLabel. For instructions on how to get started, see:\n\n" +\
            "github repo:  https://github.com/SeedlingsBabylab/idslabel\n"+\
            "osf wiki:     https://osf.io/d9ac4/wiki/home/\n\n\n"

        general = "General Keys:\n\n"
        submit_block    = "\tshift + enter         : submit + save block\n"
        save_labels     = "\tcmd   + s             : save classifications     (Mac)\n"
        save_labels_win = "\tctrl  + s             : save classifications     (Linux/Windows)\n"
        save_as         = "\tcmd   + shift + s     : save as classifications  (Mac)\n"
        save_as_win     = "\tctrl  + shift + s     : save as classifications  (Linux/Windows)\n"

        classification = "\nClassification Keys:\n\n"
        ids        = "\tc : CDS\n"
        ads        = "\ta : ADS\n"
        junk       = "\tj : Junk\n\n"

        male       = "\tm : Male\n"
        female     = "\tf : Female\n"


        clips = "\nClip Navigation/Playback Keys:\n\n"
        up         = "\tup            : previous clip\n"
        left       = "\tleft          : previous clip\n"
        down       = "\tdown          : next clip\n"
        right      = "\tright         : next clip\n"
        space      = "\tspace         : play clip\n"
        shft_space = "\tshift + space : play whole block\n"

        textbox.insert('1.0', welcome_message+\
                                general+\
                                submit_block+\
                                save_labels+\
                                save_labels_win+\
                                save_as+\
                                save_as_win+\
                                classification+\
                                ids+\
                                ads+
                                junk+\
                                male+\
                                female+\
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
        resp = urllib2.urlopen(self.server.github_tags_url)

        json_response =  json.loads(resp.read())

        git_version = json_response[0]["name"][1:]

        if LooseVersion(git_version) > LooseVersion(version):
            showwarning("Old Version",
                        "This isn't the latest version of IDSLabel\nGet the latest release from: "
                                       "\n\nhttps://github.com/SeedlingsBabylab/idslabel/releases")

    def get_blocks(self):
        if not self.session.clip_directory:
            showwarning("Set Audio Clips Directory", "You need to have a directory set before downloading blocks\n\n"+
                        "(File -> Set Block Path)")
            return
        if self.session.codername == "CODER_NAME":
            showwarning("Set Coder Name", "You need to set CODER_NAME before requesting blocks")
            return

        error_response = ""
        for i in range(self.session.num_blocks_to_get):
            error_response = self.server.get_block()

        if error_response:
            showwarning("Bad Request", "Server: " + error_response)

        self.load_downloaded_blocks()

    def get_lab_info(self):
        self.lab_info_page = labinfo.LabInfoPage(self.server, self.session)

    def get_specific_blocks(self):
        self.get_block_page = getblock.GetBlockPage(self.server, self.session, self)

    def add_user_to_server(self):

        self.server.add_user_to_server()

    def load_config_json(self):
        config_path = tkFileDialog.askopenfilename(title="Load Config File")
        self.parse_config(config_path)

        self.session.codername = self.codername_entry.get()
        self.session.clip_directory = self.temp_clip_dir
        del self.session.clip_blocks[:]
        self.server.lab_info_ping()
        self.session.prev_downl_blocks = self.load_previously_downl_blocks()
        if self.session.prev_downl_blocks:
            self.session.clip_blocks.extend(self.session.prev_downl_blocks)
        self.load_downloaded_blocks()
        self.main_frame.focus_set()

    def parse_config(self, path=None):

        curr_workdir = None
        if getattr(sys, 'frozen', False):
            curr_workdir = os.path.dirname(sys.executable)
        elif __file__:
            curr_workdir = os.path.dirname(os.path.abspath(__file__))

        files_in_cwd = os.listdir(curr_workdir)
        filtered_files = filter(lambda x: "config" in x and x.endswith(".json"), files_in_cwd)

        if len(filtered_files) == 1 and not path:
            config_path = os.path.join(curr_workdir, filtered_files[0])
        elif path is None:
            showwarning("Config File", "Please choose a config.json file to load")
            config_path = tkFileDialog.askopenfilename(title="Load Config File")
        else:
            config_path = path

        self.server = idsserver.IDSServer(config_path, self.session)
        self.session.server = self.server
        self.server.session = self.session
        self.session.lab_name = self.server.lab_name
        self.session.lab_key = self.server.lab_key

    def submit_block(self):
        # check that the current block is completed before submitting
        block = self.current_block

        block.username = self.session.codername
        block.lab_name = self.session.lab_name

        unfinished_clips = []
        for clip in block.clips:
            if clip.clip_tier == "FAN" or clip.clip_tier == "MAN":
                if not clip.classification:
                    unfinished_clips.append(clip)
                if not clip.gender_label:
                    if clip.classification == "JUNK":
                        continue
                    else:
                        unfinished_clips.append(clip)

        if not unfinished_clips:
            submission = block.to_dict()
            resp = requests.post(self.server.submit_labels_url, json=submission, allow_redirects=False)

            if resp.status_code != 200:
                showwarning("Bad Request", "Server: " + resp.content)
                return

            if resp.ok:
                #print "block: {}:::{}  sent back to the server".format(block.clan_file, block.index)
                self.cleanup_block_data(block)
                block_index = self.session.clip_blocks.index(block)
                del self.session.clip_blocks[block_index]
        else:
            showwarning("Incomplete Block", "You haven't classified all the FAN/MAN tiered clips within this block")
            return

        self.block_list.delete(0, END)
        self.load_downloaded_blocks()
        if self.session.clip_blocks:
            self.load_downloaded_block(0)

    def submit_block_and_save(self):
        if not self.dont_share_applied:
            result = askyesno("Personal Information", "Is block ok to share?")
            if result:
                self.current_block.dont_share = False
            else:
                self.current_block.dont_share = True
                self.dont_share_applied = True
        else:
            result = askyesno("Personal Information", "Is block ok to share?\n\nCurrent value: No")
            if result:
                self.current_block.dont_share = False
            else:
                self.current_block.dont_share = True
        if not self.session_output_file:
            showwarning("Set Output File", "Please choose a csv file to save this session's blocks to")
            self.session_output_file = tkFileDialog.asksaveasfilename()
            if os.path.isfile(self.session_output_file):
                if not os.stat(self.session_output_file).st_size == 0:
                    showwarning("Nonempty Output File", "Please choose a new csv file. This file already has data from a previous session in it.")
                    self.session_output_file = None
                    return
        # check that the current block is completed before submitting
        block = self.current_block

        unfinished_clips = []
        for clip in block.clips:
            if clip.clip_tier == "FAN" or clip.clip_tier == "MAN":
                if not clip.classification:
                    unfinished_clips.append(clip)
                if not clip.gender_label:
                    if clip.classification == "JUNK":
                        continue
                    else:
                        unfinished_clips.append(clip)
        if not unfinished_clips:
            self.write_block_to_session_out(block)
            self.submit_block()
        else:
            showwarning("Incomplete Block", "You haven't classified all the FAN/MAN tiered clips within this block")
            return

    def get_completed_blocks(self):
        completed_blocks = []
        incomplete_blocks = []
        for block in self.session.clip_blocks:
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
        self.block_list.delete(0, END)
        self.previous_block_menu.delete(0, END)
        for index, block in enumerate(self.session.clip_blocks):
            block_string = "{} : {}".format(index+1, block.index)
            if block.old:
                block_string += "  [old]"
            else:
                block_string += "  [new]"
            self.previous_block_menu.insert(index, block_string)

    def load_previously_downl_blocks(self):
        blocks = []
        self.server.lab_info_ping()
        user = self.codername_entry.get()

        if not self.session.lab_data:
            return

        users = self.session.lab_data["users"]

        if user not in users:
            showwarning("Set Coder Name", "CODER_NAME: \"{}\" , is not known by the server.\n\n".format(user) +\
            "Either add it (File -> Add User to Server), or use an already registered name")
            return []

        user_data = users[user]
        user_active_blocks = user_data["active_work_items"]

        for root, dirs, files in os.walk(self.session.clip_directory):
            if any(".zip" in file for file in files):
                zips = [x for x in files if ".zip" in x]
                if len(zips) > 0:
                    zipfile = os.path.join(root, zips[0])
                    block = idsblocks.create_block_from_clips(zipfile, self.session.codername, self.session.lab_key)
                    block.old = True
                    root_basename = os.path.basename(root)
                    if user not in root_basename:
                        continue
                    if self.block_belongs_to_user(block, user_active_blocks):
                        blocks.append(block)

        return blocks

    def block_belongs_to_user(self, block, user_active_items):
        if user_active_items is None:
            return False

        if block.id in user_active_items:
            return True
        return False

    def enter_block_request_num(self, event):
        self.main_frame.focus_set()
        self.session.num_blocks_to_get = int(self.block_request_num_entry.get())

    def cleanup_block_data(self, block):
        clips_path = ""
        for clip in block.clips:
            os.remove(clip.audio_path)
            clips_path = os.path.dirname(clip.audio_path)
        shutil.rmtree(clips_path)

    def send_blocks_back(self):
        self.send_blocks_back_page = Toplevel()
        self.send_blocks_back_page.title("Send Blocks Back")
        self.send_blocks_back_page.geometry("350x350")

        self.send_back_block_list = Listbox(self.send_blocks_back_page, selectmode=MULTIPLE, width=10, height=15)
        self.send_back_block_list.grid(row=1, column=1)

        send_back_button = Button(self.send_blocks_back_page, text="Send Back", command=self.send_back)
        send_back_button.grid(row=1, column=0)

        self.select_all_send_back_var = IntVar()
        self.send_all_back_radio = Checkbutton(self.send_blocks_back_page,
                                               text="Select All",
                                               variable=self.select_all_send_back_var,
                                               command=self.send_back_select_all)
        self.send_all_back_radio.grid(row=2, column=0)

        self.send_back_block_list.delete(0, END)

        for index, block in enumerate(self.session.clip_blocks):
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
            block = self.session.clip_blocks[selection]
            selection_ids.append(block.id)
            selection_blocks.append(block)

        name = self.codername_entry.get()
        if name == "CODER_NAME":
            showwarning("Set Coder Name", "You need to set your coder name first")
            return

        payload = {"lab_key": self.session.lab_key,
                   "lab_name": self.session.lab_name,
                   "username": name,
                   "blocks": []
                   }

        for block in selection_ids:
            payload["blocks"].append(block)

        resp = requests.post(self.server.send_back_blocks_url, json=payload, allow_redirects=False)

        for block in selection_blocks:
            self.cleanup_block_data(block)
            block_index = self.session.clip_blocks.index(block)
            del self.session.clip_blocks[block_index]

        self.send_back_block_list.delete(0, END)
        for index, block in enumerate(self.session.clip_blocks):
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
                                 "timestamp", "clip", "tier", "label", "gender",
                                 "dont_share", "training", "reliability"])
                self.session_output_header_written = True

            dont_share = False
            if block.dont_share:
                dont_share = True

            for clip in block.clips:
                writer.writerow([clip.label_date, clip.coder, clip.clan_file,
                                 clip.parent_audio_path, clip.block_index,
                                 clip.timestamp, clip.clip_index, clip.clip_tier,
                                 clip.classification, clip.gender_label, dont_share,
                                 block.training, block.reliability])

    def send_back_select_all(self):
        if self.select_all_send_back_var:
            self.send_back_block_list.selection_set(0, END)
        else:
            self.send_back_block_list.selection_clear(0, END)

    def get_training_blocks(self):
        if not self.session.clip_directory:
            showwarning("Set Audio Clips Directory", "You need to have a directory set before downloading blocks\n\n" +
                        "(File -> Set Block Path)")
            return
        if self.codername_entry.get() == "CODER_NAME":
            showwarning("Set Coder Name", "You need to set CODER_NAME before requesting blocks")
            return

        error_response = ""
        for i in range(self.session.num_training_blocks_to_get):
            error_response = self.server.get_training_block()

        if error_response:
            showwarning("Bad Request", "Server: " + error_response)

        self.load_downloaded_blocks()

    def get_reliability_blocks(self):
        if not self.session.clip_directory:
            showwarning("Set Audio Clips Directory", "You need to have a directory set before downloading blocks\n\n" +
                        "(File -> Set Block Path)")
            return
        if self.codername_entry.get() == "CODER_NAME":
            showwarning("Set Coder Name", "You need to set CODER_NAME before requesting blocks")
            return

        error_response = ""
        for i in range(self.session.num_blocks_to_get):
            error_response = self.server.get_reliability_block()

        if error_response:
            showwarning("Bad Request", "Server: " + error_response)

        self.load_downloaded_blocks()


if __name__ == "__main__":

    root = Tk()
    idslabel_main = MainWindow(root)
    root.mainloop()
