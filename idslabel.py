import pyaudio
import wave
import random

from Tkinter import *
import tkFileDialog


class MainWindow:

    def __init__(self, master):
        self.clan_file = None
        self.audio_file = None

        self.conversation_blocks = None

        self.current_clip = None    # [path, parent_path,
        self.current_block = None


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


        self.next_clip_button = Button(self.main_frame,
                                       text="Next Clip",
                                       command=self.next_clip)


        self.replay_clip_button = Button(self.main_frame,
                                         text="Replay Clip",
                                         command=self.replay_clip)



        self.load_clan_button.grid(row=0, column=0)
        self.load_audio_button.grid(row=0, column=1)
        self.load_rand_block_button.grid(row=0, column=2)

        self.next_clip_button.grid(row=3, column=2)
        self.replay_clip_button.grid(row=4, column=2)

        self.block_list = Listbox(self.main_frame, width=20, height=25)
        self.block_list.grid(row=1, column=3, rowspan=5)


        self.block_count_label = None



        self.ids_var = IntVar()
        self.ids_button = Checkbutton(self.main_frame, text="IDS", variable=self.ids_var)




    def load_clan(self):
        self.clan_file = tkFileDialog.askopenfilename()
        self.parse_clan(self.clan_file)

    def load_audio(self):
        self.audio_file = tkFileDialog.askopenfilename()


    def play_audio(self, path):

        #define stream chunk
        chunk = 1024

        #open a wav format music
        f = wave.open(path,"rb")

        #instantiate PyAudio
        p = pyaudio.PyAudio()

        #open stream
        stream = p.open(format = p.get_format_from_width(f.getsampwidth()),
                        channels = f.getnchannels(),
                        rate = f.getframerate(),
                        output = True)

        #read data
        data = f.readframes(chunk)

        #paly stream
        while data != '':
            stream.write(data)
            data = f.readframes(chunk)

        #stop stream
        stream.stop_stream()
        stream.close()

        #close PyAudio
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

        self.conversation_blocks = self.filter_conversations(conversations)

        self.block_count_label = Label(self.main_frame,
                                       text=str(len(self.conversation_blocks))+\
                                       " blocks")

        self.block_count_label.grid(row=0, column=4, columnspan=1)


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


    def load_random_conv_block(self):
        rand_index = random.randrange(0, len(self.conversation_blocks))
        while rand_index in self.previously_selected_blocks:
            rand_index = random.randrange(0, len(self.conversation_blocks))

        self.previously_selected_blocks.append(rand_index)

        self.block_list.delete(0, END)

        for index, element in enumerate(self.conversation_blocks[rand_index]):
            self.block_list.insert(index, element)

        self.current_block = self.conversation_blocks[rand_index]


    def next_clip(self):
        print "hello"

    def replay_clip(self):
        print "hello"



if __name__ == "__main__":

    root = Tk()
    MainWindow(root)
    root.mainloop()
