class Session(object):
    def __init__(self, server):

        self.server = server
        self.lab_users = []
        self.lab_data = None

        self.codername = None
        self.lab_name = None
        self.lab_key = None
        self.clip_directory = None

        self.lab_info_curr_user = None

        self.num_blocks_to_get = 3
        self.num_training_blocks_to_get = 10

        self.clip_blocks = []

        self.prev_downl_blocks = []

        self.block_list_from_server = None




