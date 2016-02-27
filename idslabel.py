import pyaudio
import wave
import random
import datetime
import re
import os
import subprocess as sp

from Tkinter import *
import tkFileDialog


class Block:

    def __init__(self, index, clan_file):

        self.index = index
        self.clan_file = clan_file
        self.num_clips = None
        self.clips = []

class Clip:

    def __init__(self, path, block_index, clip_index):
        self.audio_path = path
        self.clan_file = None
        self.block_index = block_index
        self.clip_index = clip_index
        self.start_time = None
        self.offset_time = None
        self.classification = None


class MainWindow:

    def __init__(self, master):
        self.clan_file = None
        self.audio_file = None

        self.conversation_blocks = None

        self.current_clip = [None]*6    #  [audio_clip_path,     0
                                        #   parent_audio_path,   1
                                        #   block_index,         2
                                        #   clip_index,          3
                                        #   classification,      4
                                        #   time-start,          5    HH:MM:SS.xxx
                                        #   time-end]            6    HH:MM:SS.xxx

        self.current_block_index = None
        self.current_block = None
        self.processed_clips_in_curr_block = []
        self.processed_clips = []

        # list of integers corresponding
        # to self.conversation_blocks
        self.previously_selected_blocks = []

        self.root = master                # main GUI context
        self.root.title("IDS Label")      # title of window
        self.root.geometry("800x600")     # size of GUI window
        self.main_frame = Frame(root)     # main frame into which all the Gui components will be placed
        self.main_frame.pack()            # pack() basically sets up/inserts the element (turns it on)

        # general
        self.load_clan_button = Button(self.main_frame,
                                          text= "Load Clan File",
                                          command=self.load_clan)

        self.load_audio_button = Button(self.main_frame,
                                           text= "Load Audio",
                                           command=self.load_audio)


        self.load_rand_block_button = Button(self.main_frame,
                                             text="Load Block",
                                             command=self.load_random_conv_block)


        self.play_clip_button = Button(self.main_frame,
                                       text="Play Clip",
                                       command=self.play_clip)

        self.next_clip_button = Button(self.main_frame,
                                       text="Next Clip",
                                       command=self.next_clip)


        self.replay_clip_button = Button(self.main_frame,
                                         text="Replay Clip",
                                         command=self.replay_clip)



        self.load_clan_button.grid(row=0, column=0)
        self.load_audio_button.grid(row=0, column=1)
        self.load_rand_block_button.grid(row=0, column=2)

        self.play_clip_button.grid(row=2, column=2)
        self.next_clip_button.grid(row=3, column=2)
        self.replay_clip_button.grid(row=4, column=2)

        self.block_list = Listbox(self.main_frame, width=20, height=25)
        self.block_list.grid(row=1, column=3, rowspan=5)


        self.block_count_label = None



        self.ids_var = IntVar()
        self.ids_button = Checkbutton(self.main_frame, text="IDS", variable=self.ids_var)

        self.ads_var = IntVar()
        self.ads_button = Checkbutton(self.main_frame, text="ADS", variable=self.ads_var)

        self.neither_var = IntVar()
        self.neither_button = Checkbutton(self.main_frame, text="Neither", variable=self.neither_var)

        self.junk_var = IntVar()
        self.junk_button = Checkbutton(self.main_frame, text="Junk", variable=self.junk_var)

        self.ids_button.grid(row=2, column=0)
        self.ads_button.grid(row=3, column=0)
        self.neither_button.grid(row=4, column=0)
        self.junk_button.grid(row=5, column=0)

        self.classification_conflict_label = None

        self.clips_processed_label = None
        self.current_block_label = None

        self.interval_regx = re.compile("\\x15\d+_\d+\\x15")

        self.clip_blocks = []
        self.randomized_blocks = []     # indices refer to original unrandomized order in self.clip_blocks
        self.clip_path = None


    def load_clan(self):
        self.clan_file = tkFileDialog.askopenfilename()
        self.parse_clan(self.clan_file)


    def load_audio(self):
        self.audio_file = tkFileDialog.askopenfilename()


    def play_clip(self):

        current_clip = self.block_list.curselection()
        clip_index = current_clip[0]

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
            self.clip_blocks.append(self.create_clips(block, path, index))

        self.block_count_label = Label(self.main_frame,
                                       text=str(len(conversation_blocks))+\
                                       " blocks")

        self.block_count_label.grid(row=0, column=4, columnspan=1)

        #self.slice_audio_file(self.clip_blocks)
        self.create_random_block_range()


    def slice_block(self, block, block_index):

        clanfilename = block.clan_file[0:5]

        #clanfilename = block[1][0][1][0:5]

        all_blocks_path = os.path.join("clips", clanfilename)

        if not os.path.exists(all_blocks_path):
            os.makedirs(all_blocks_path)

        block_path = os.path.join(all_blocks_path, str(block.index))

        #block_path = os.path.join(all_blocks_path, str(block[1][0][3]))


        if not os.path.exists(block_path):
            os.makedirs(block_path)

        # for clip in block[1]:
        #     command = ["ffmpeg",
        #                "-ss",
        #                str(clip[5]),
        #                "-t",
        #                str(clip[6]),
        #                "-i",
        #                self.audio_file,
        #                clip[2], # os.path.join(block_path, str(clip[3])+".wav"),
        #                "-y"]

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
            pipe.communicate()  # blocks until the subprocess is complete


    def create_random_block_range(self):

        self.randomized_blocks = list(self.clip_blocks)
        random.shuffle(self.randomized_blocks)


    def filter_conversations(self, conversations):
        filtered_conversations = []

        for conversation in conversations:
            conv_block = []
            for line in conversation:
                if line.startswith("%"):
                    continue
                elif line.startswith("@"):
                    continue
                else:
                    conv_block.append(line)
            filtered_conversations.append(conv_block)
            conv_block = []



        return filtered_conversations


    def create_clips(self, clips, parent_path, block_index):

        parent_path = os.path.split(parent_path)[1]

        block = Block(block_index, parent_path)


        for index, clip in enumerate(clips):

            clip_path = os.path.join("clips",
                                     parent_path[0:5],
                                     str(block_index),
                                     str(index)+".wav")

            curr_clip = Clip(clip_path, block_index, index)

            curr_clip.clan_file = parent_path


            # temp_clip = ["{}-{}-{}".format(parent_path[0:5], block_index, index),
            #              parent_path, clip_path, block_index,
            #              index, None, None, None]

            interval_reg_result = self.interval_regx.search(clip)
            if interval_reg_result:
                interval_str = interval_reg_result.group().replace("\x15", "")

            time = interval_str.split("_")
            time = [int(time[0]), int(time[1])]

            final_time = self.ms_to_hhmmss(time)

            curr_clip.start_time = str(final_time[0])
            curr_clip.offset_time = str(final_time[2])

            block.clips.append(curr_clip)

        return block


    def load_random_conv_block(self):

        self.block_list.delete(0, END)

        if self.current_block_index is None:
            self.current_block_index = 0
        elif self.current_block_index == len(self.randomized_blocks):
            print "That's the last block"
        else:
            self.current_block_index += 1

        self.current_block = self.randomized_blocks[self.current_block_index]

        self.slice_block(self.current_block, self.current_block_index)

        for index, element in enumerate(self.randomized_blocks[self.current_block_index].clips):
            self.block_list.insert(index, index)

        self.current_block_label = Label(self.main_frame, text="block #{}".format(self.current_block_index))
        self.current_block_label.grid(row=6, column=3)

        # self.current_block = self.conversation_blocks[rand_index]


    def next_clip(self):

        if self.ids_var.get() == 1 and self.ads_var.get() == 1:
            self.classification_conflict_label = Label(self.main_frame,
                                                       text="can't be both IDS and ADS")

            self.classification_conflict_label.grid(row=6, column=0)
            return

        if self.classification_conflict_label:
            self.classification_conflict_label.grid_remove()

        if self.ids_var.get() == 1:
            self.current_clip[3] = "ids"
        if self.ads_var.get() == 1:
            self.current_clip[3] = "ads"
        if self.neither_var.get() == 1:
            self.current_clip[3] = "neither"
        if self.junk_var.get() == 1:
            self.current_clip[3] = "junk"

        self.reset_classification_buttons()

        self.processed_clips_in_curr_block.append(self.current_clip)

        self.current_clip = self.current_block_index[self.current_clip[2]]

        self.clips_processed_label = Label(self.main_frame,
                                           text="{} total clips processed"
                                           .format(len(self.processed_clips_in_curr_block+\
                                                       self.processed_clips)))
        self.clips_processed_label.grid(row=6, column=3)


    def replay_clip(self):
        print "hello"


    def reset_classification_buttons(self):
        self.ids_button.deselect()
        self.ads_button.deselect()
        self.neither_button.deselect()
        self.junk_button.deselect()


    def slice_audio_file(self, clips):

        clanfilename = clips[0][0][0][0:5]
        all_blocks_path = os.path.join("clips", clanfilename)
        if not os.path.exists(all_blocks_path):
            os.makedirs(all_blocks_path)

        for block in clips:
            block_path = os.path.join(all_blocks_path, str(block[0][2]))
            if not os.path.exists(block_path):
                os.makedirs(block_path)

            for clip in block:
                command = ["ffmpeg",
                           "-ss",
                           str(clip[5]),
                           "-t",
                           str(clip[6]),
                           "-i",
                           self.audio_file,
                           os.path.join(block_path, str(clip[3])+".wav"),
                           "-y"]

                command_string = " ".join(command)
                print command_string

                pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10**8)
                pipe.communicate()  # blocks until the subprocess is complete


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



if __name__ == "__main__":

    root = Tk()
    MainWindow(root)
    root.mainloop()
