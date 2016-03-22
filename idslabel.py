import pyaudio
import wave
import random
import datetime
import time
import csv
import re
import os
import subprocess as sp

from Tkinter import *
import tkFileDialog
from tkMessageBox import showwarning


version = "0.0.1"

class Block:
    def __init__(self, index, clan_file):

        self.index = index
        self.clan_file = clan_file
        self.num_clips = None
        self.clips = []
        self.sliced = False

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
        self.label_date = None
        self.coder = None

    def __repr__(self):
        return "clip: {} - [block: {}] [tier: {}] [label: {}] [time: {}]".format(self.clip_index,
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

        self.root = master                # main GUI context
        self.root.title("IDS Label  "+version)      # title of window
        self.root.geometry("850x600")     # size of GUI window
        self.main_frame = Frame(root)     # main frame into which all the Gui components will be placed

        self.main_frame.bind("<Key>", self.key_select)
        self.main_frame.bind("<space>", self.shortcut_play_clip)
        self.main_frame.bind("<Shift-space>", self.shortcut_play_block)
        self.main_frame.bind("<Left>", self.shortcut_previous_clip)
        self.main_frame.bind("<Right>", self.shortcut_next_clip)
        self.main_frame.bind("<Up>", self.shortcut_previous_clip)
        self.main_frame.bind("<Down>", self.shortcut_next_clip)
        self.main_frame.bind("<Shift-Return>", self.shortcut_load_random_block)


        self.menubar = Menu(self.root)

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load Audio", command=self.load_audio)
        self.filemenu.add_command(label="Load Clan", command=self.load_clan)
        self.filemenu.add_command(label="Save Classifications", command=self.output_classifications)

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
                                                    text="Output Classifications",
                                                    command=self.output_classifications)

        self.load_clan_button.grid(row=0, column=0)
        self.load_audio_button.grid(row=0, column=1)
        self.load_rand_block_button.grid(row=0, column=2)

        self.load_previous_block_button.grid(row=1, column=2)
        self.play_clip_button.grid(row=2, column=2)
        self.play_block_button.grid(row=3, column=2)
        self.next_clip_button.grid(row=4, column=2)
        self.output_classifications_button.grid(row=7, column=2)

        self.block_list = Listbox(self.main_frame, width=15, height=25)
        self.block_list.grid(row=1, column=3, rowspan=5)

        self.block_list.bind('<<ListboxSelect>>', self.update_curr_clip)
        self.block_list.bind("<FocusIn>", self.reset_frame_focus)
        self.block_count_label = None


        self.curr_clip_info = Text(self.main_frame, width=50, height=10)
        self.curr_clip_info.grid(row=1, column=0, rowspan=3, columnspan=2)


        self.codername_entry = Entry(self.main_frame, width=10, font="-weight bold")
        self.codername_entry.insert(END, "CODER NAME")
        self.codername_entry.grid(row=0, column=4)

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

    def key_select(self, event):
        self.main_frame.focus_set()

        selected_key = event.char

        if selected_key == "i":
            if not self.current_clip:
                self.set_curr_clip(0)
            self.current_clip.classification = "IDS"
            self.current_clip.label_date = time.strftime("%m/%d/%Y")
            self.current_clip.coder = self.codername_entry.get()
            self.update_curr_clip_info()

        if selected_key == "a":
            if not self.current_clip:
                self.set_curr_clip(0)
            self.current_clip.classification = "ADS"
            self.current_clip.label_date = time.strftime("%m/%d/%Y")
            self.current_clip.coder = self.codername_entry.get()
            self.update_curr_clip_info()
        if selected_key == "n":
            if not self.current_clip:
                self.set_curr_clip(0)
            self.current_clip.classification = "NEITHER"
            self.current_clip.label_date = time.strftime("%m/%d/%Y")
            self.current_clip.coder = self.codername_entry.get()
            self.update_curr_clip_info()

        if selected_key == "j":
            if not self.current_clip:
                self.set_curr_clip(0)
            self.current_clip.classification = "JUNK"
            self.current_clip.label_date = time.strftime("%m/%d/%Y")
            self.current_clip.coder = self.codername_entry.get()
            self.update_curr_clip_info()

        if selected_key == "C":
            self.load_clan()
        if selected_key == "A":
            self.load_audio()
        if selected_key == "|":
            self.load_previous_block()
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

    def reset_frame_focus(self, event):
        self.main_frame.focus_set()

    def load_clan(self):
        self.clan_file = tkFileDialog.askopenfilename()
        showwarning("Note", "Remember to write your name in the 'CODER NAME' box before starting")
        self.parse_clan(self.clan_file)

    def load_audio(self):
        self.audio_file = tkFileDialog.askopenfilename()

    def play_clip(self):

        current_clip = self.block_list.curselection()
        clip_index = current_clip[0]

        clip_path = self.current_block.clips[clip_index].audio_path
        chunk = 1024

        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(self.current_clip.clip_index)

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

        self.block_count_label.grid(row=7, column=3, columnspan=1)

        self.create_random_block_range()

    def slice_block(self, block):

        clanfilename = block.clan_file[0:5]

        all_blocks_path = os.path.join("clips", clanfilename)

        if not os.path.exists(all_blocks_path):
            os.makedirs(all_blocks_path)

        block_path = os.path.join(all_blocks_path, str(block.index))

        if not os.path.exists(block_path):
            os.makedirs(block_path)

        for clip in block.clips:
            command = ["ffmpeg",
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
            pipe.communicate()

    def slice_all_randomized_blocks(self):

        for block in self.randomized_blocks:
            self.slice_block(block)

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

            clip_path = os.path.join("clips",
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

        self.blocks_to_csv()

        return block

    def load_previous_block(self):

        if self.current_block_index is None:
            self.current_block_index = 0
        elif self.current_block_index == 0:
            return
        elif self.current_block_index == len(self.randomized_blocks):
            print "That's the last block"
        else:
            self.current_block_index -= 1

        self.block_list.delete(0, END)

        self.current_block = self.randomized_blocks[self.current_block_index]

        self.slice_block(self.current_block)

        for index, element in enumerate(self.randomized_blocks[self.current_block_index].clips):
            if element.multiline:
                self.block_list.insert(index, element.clip_tier+" ^--")
            else:
                self.block_list.insert(index, element.clip_tier)

        self.coded_block_label = Label(self.main_frame, text="coded block #{}".format(self.current_block_index + 1))
        self.coded_block_label.grid(row=6, column=3)

        self.current_clip = self.current_block.clips[0]

        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(0)

        self.update_curr_clip_info()

    def load_random_conv_block(self):

        if self.current_block_index is None:
            self.current_block_index = 0
        elif self.current_block_index == len(self.randomized_blocks):
            print "That's the last block"
        else:
            self.current_block_index += 1

        self.block_list.delete(0, END)

        self.current_block = self.randomized_blocks[self.current_block_index]

        self.slice_block(self.current_block)

        for index, element in enumerate(self.randomized_blocks[self.current_block_index].clips):
            if element.multiline:
                self.block_list.insert(index, element.clip_tier+" ^--")
            else:
                self.block_list.insert(index, element.clip_tier)

        self.coded_block_label = Label(self.main_frame, text="coded block #{}".format(self.current_block_index + 1))
        self.coded_block_label.grid(row=6, column=3)

        self.current_clip = self.current_block.clips[0]

        self.block_list.selection_clear(0, END)
        self.block_list.selection_set(0)

        self.update_curr_clip_info()

    def update_curr_clip_info(self):

        self.curr_clip_info.configure(state="normal")
        self.curr_clip_info.delete("1.0", END)

        self.curr_clip_info.insert('1.0',
                                   "clip:         {}\nblock:        {}\ntier:         {}\nlabel:        {}\ntime:         {}\nclip length:  {}\ncoder:        {}\nclan file:    {}".
                                                            format(self.current_clip.clip_index,
                                                                   self.current_clip.block_index,
                                                                   self.current_clip.clip_tier,
                                                                   self.current_clip.classification,
                                                                   self.current_clip.timestamp,
                                                                   self.current_clip.offset_time,
                                                                   self.current_clip.coder,
                                                                   self.current_clip.clan_file))

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

        if interval[0] == 0:
            start = "0"+x_start.__str__()[:11]+".000"
        else:
            start = "0"+x_start.__str__()[:11]
        end = "0"+x_end.__str__()[:11]

        return [start, end, x_diff]

    def output_classifications(self):

        #[date, coder, clanfile, audiofile, block, timestamp, clip, tier, label, multi-tier]
        output_path = tkFileDialog.asksaveasfilename()

        with open(output_path, "wb") as output:
            writer = csv.writer(output)
            writer.writerow(["date", "coder", "clan_file", "audiofile", "block",
                             "timestamp", "clip", "tier", "label", "multi-tier-parent"])

            for block in self.randomized_blocks:
                multitier_parent = None
                for clip in block.clips:
                    if clip.multiline:
                        multitier_parent = clip.multi_tier_parent
                    else:
                        multitier_parent = "N"

                    writer.writerow([clip.label_date, clip.coder, clip.clan_file,
                                     clip.parent_audio_path, clip.block_index+1,
                                     clip.timestamp, clip.clip_index,clip.clip_tier,
                                     clip.classification, multitier_parent])

    def blocks_to_csv(self):

        with open("blocks.csv", "wb") as file:
            writer = csv.writer(file)
            writer.writerow(["block", "num_clips"])
            for block in self.clip_blocks:
                writer.writerow([block.index, block.num_clips])

    def show_shortcuts(self):
        self.shortcuts_menu = Toplevel()
        self.shortcuts_menu.title("Shortcuts")
        self.shortcuts_menu.geometry("350x400")
        textbox = Text(self.shortcuts_menu)
        textbox.pack()


        general = "General Keys:\n\n"
        load_audio      = "\tshift + a     : load audio file\n"
        load_clan       = "\tshift + c     : load clan file\n"
        load_block      = "\tshift + enter : load random block\n"
        load_prev_block = "\tshift + \     : load previous block\n"
        output_labels   = "\tshift + o     : output classifications\n"

        classification = "\nClassification Keys:\n\n"
        ids = "\ti : IDS\n"
        ads = "\ta : ADS\n"
        neith = "\tn : Neither\n"
        junk = "\tj : Junk\n"

        clips = "\nClip Navigation/Playback Keys:\n\n"
        up         = "\tup            : previous clip\n"
        left       = "\tleft          : previous clip\n"
        down       = "\tdown          : next clip\n"
        right      = "\tright         : next clip\n"
        space      = "\tspace         : play clip\n"
        shft_space = "\tshift + space : play whole block\n"

        textbox.insert('1.0', general+\
                                load_audio+\
                                load_clan+\
                                load_block+\
                                load_prev_block+\
                                output_labels+\
                                classification+\
                                ids+\
                                ads+
                                neith+\
                                junk+\
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
        version = "{}\n\n".format(version)
        author = "author: Andrei Amatuni\n"
        homepage = "homepage: https://github.com/SeedlingsBabylab/idslabel"
        textbox.insert('1.0', name+version+author+homepage)

        textbox.configure(state="disabled")

if __name__ == "__main__":

    root = Tk()
    MainWindow(root)
    root.mainloop()
