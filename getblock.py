from Tkinter import *
import tkFileDialog

import idsserver
import idsblocks
import idssession


class GetBlockPage(object):
    def __init__(self, server, session, main_page):
        self.server = server
        self.session = session
        self.main_page = main_page

        self.get_block_page_root = Toplevel()
        self.get_block_page_root.title("Get Blocks")
        self.get_block_page_root.geometry("800x450")

        self.available_blocks_label = Label(self.get_block_page_root,
                                            text="Available Blocks")
        self.available_blocks_label.grid(row=0, column=0)

        self.selected_blocks_label = Label(self.get_block_page_root,
                                           text="Selected Blocks")
        self.selected_blocks_label.grid(row=0, column=1)

        self.available_blocks_box = Listbox(self.get_block_page_root,
                                            width=31, height=20)
        self.available_blocks_box.grid(row=1, column=0, rowspan=9)
        self.available_blocks_box.bind('<Double-Button-1>', self.select_block)

        self.selected_blocks_box = Listbox(self.get_block_page_root,
                                           width=31, height=20,
                                           selectmode=MULTIPLE)
        self.selected_blocks_box.grid(row=1, column=1, rowspan=9)

        self.delete_selected = Button(self.get_block_page_root,
                                      text="Delete Selected",
                                      command=self.delete_selected)
        self.delete_selected.grid(row=10, column=1)

        self.delete_all = Button(self.get_block_page_root,
                                 text="Delete All", command=self.delete_all)
        self.delete_all.grid(row=11, column=1)

        self.get_blocks_button = Button(self.get_block_page_root,
                                        text="Get Blocks",
                                        command=self.get_blocks)
        self.get_blocks_button.grid(row=5, column=2)

        self.block_list = None

        self.load_block_list_from_server()

    def load_block_list_from_server(self):
        if not self.server.get_block_list_url:
            showwarning("Load Config",
                        "You need to load the config.json file first")
            return
        self.server.get_block_list_from_server()

        i = 0
        for blockID, info in sorted(self.session.block_list_from_server.iteritems()):
            self.available_blocks_box.insert(i, blockID)
            i += 1

    def select_block(self, event):
        box = event.widget
        index = int(box.curselection()[0])

        block_id = box.get(index)

        already_selected = self.selected_blocks_box.get(0, END)

        if block_id not in already_selected:
            self.selected_blocks_box.insert(END, block_id)

    def delete_selected(self):
        selected_items = self.selected_blocks_box.curselection()

        new_items = []
        for x in range(self.selected_blocks_box.size()):
            if x not in selected_items:
                new_items.append(self.selected_blocks_box.get(x))

        self.selected_blocks_box.delete(0, END)
        for index, element in enumerate(new_items):
            self.selected_blocks_box.insert(index, element)

    def delete_all(self):
        self.selected_blocks_box.delete(0, END)

    def get_blocks(self):
        selected_items = self.selected_blocks_box.get(0, END)
        print selected_items

        for item in selected_items:
            self.server.get_specific_block(item)

        self.main_page.load_downloaded_blocks()
