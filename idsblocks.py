import os
import zipfile
import datetime
import csv

class Block(object):
    def __init__(self, index, clan_file):

        self.index = index
        self.instance = 0
        self.clan_file = clan_file
        self.num_clips = None
        self.clips = []
        self.sliced = False
        self.dont_share = False
        self.id = ""
        self.coder = None
        self.lab_key = None
        self.lab_name = None
        self.username = None
        self.old = False
        self.length = 0
        self.training = False
        self.reliability = False

    def sort_clips(self):
        self.clips.sort(key=lambda x: x.clip_index)

    def to_dict(self):
        block = {}

        block["clips"] = []
        for clip in self.clips:
            block["clips"].append(clip.to_dict())

        block["coder"] = self.coder
        block["lab_key"] = self.lab_key
        block["lab_name"] = self.lab_name
        block["id"] = self.id
        block["dont_share"] = self.dont_share
        block["clan_file"] = self.clan_file
        block["block_index"] = self.index
        block["training"] = self.training
        block["reliability"] = self.reliability
        block["username"] = self.username

        return block

    def block_id(self):
        return "{}:::{}".format(self.clan_file, self.index)

def json_to_block(block_json):
    block = Block(block_json["block_index"], block_json["clan_file"])
    block.instance = block_json["block_instance"]
    block.dont_share = block_json["dont_share"]
    block.lab_name = block_json["lab_name"]
    block.coder = block_json["coder"]

    block.training = block_json["training"]
    block.reliability = block_json["reliability"]

    for clip in block_json["clips"]:
        block.clips.append(json_to_clip(clip, block.index, block.clan_file))

    return block


class Clip(object):
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

        clip["clan_file"] = self.clan_file
        clip["block_index"] = self.block_index
        clip["clip_index"] = self.clip_index
        clip["clip_tier"] = self.clip_tier
        clip["multiline"] = self.multiline
        clip["multi_tier_parent"] = self.multi_tier_parent
        clip["start_time"] = self.start_time
        clip["offset_time"] = self.offset_time
        clip["timestamp"] = self.timestamp
        clip["classification"] = self.classification
        clip["gender_label"] = self.gender_label
        clip["label_date"] = self.label_date
        clip["coder"] = self.coder

        return clip

    def __repr__(self):
        return "clip: {} - [block: {}] [tier: {}] [label: {}] [time: {}]"\
                .format(self.clip_index,
                        self.block_index,
                        self.clip_tier,
                        self.classification,
                        self.timestamp)

def json_to_clip(clip_json, block_index, clan_file):
    clip = Clip("", block_index, clip_json["clip_index"])

    clip.clan_file = clan_file
    clip.clip_tier = clip_json["clip_tier"]
    clip.start_time = clip_json["start_time"]
    clip.offset_time = clip_json["offset_time"]
    clip.timestamp = clip_json["timestamp"]
    clip.classification = clip_json["classification"]
    clip.gender_label = clip_json["gender_label"]
    clip.label_date = clip_json["label_date"]
    clip.coder = clip_json["coder"]

    return clip


def create_block_from_zip(path_to_zip, codername, lab_key):
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
    if csv_data[0][11] == "True":
        block.training = True
    if csv_data[0][12] == "True":
        block.reliability = True

    block.coder = codername
    block.lab_key = lab_key

    for file in os.listdir(clips_path):
        if file.endswith(".wav"):
            clip_index = int(file.replace(".wav", ""))
            clip = Clip(os.path.join(clips_path, file), block_index, clip_index)
            clip = fill_in_clip_info_from_csv(csv_data, clip)
            clip.audio_path = os.path.join(clips_path, file)
            block.clips.append(clip)

    block.sort_clips()

    block.id = block.clan_file + ":::" + str(block.index)

    block_length = 0
    for clip in block.clips:
        time_split = clip.timestamp.split("_")
        time_split = [int(x) for x in time_split]
        block_length += time_split[1] - time_split[0]

    time = ms_to_hhmmss([0, block_length])

    block.length = time[2]

    return block


def ms_to_hhmmss(interval):
    x_start = datetime.timedelta(milliseconds=interval[0])
    x_end = datetime.timedelta(milliseconds=interval[1])

    x_diff = datetime.timedelta(milliseconds=interval[1] - interval[0])

    start = ""
    if interval[0] == 0:
        start = "0" + x_start.__str__()[:11] + ".000"
    else:

        start = "0" + x_start.__str__()[:11]
        if start[3] == ":":
            start = start[1:]
    end = "0" + x_end.__str__()[:11]
    if end[3] == ":":
        end = end[1:]

    return [start, end, x_diff]


def fill_in_clip_info_from_csv(csv_array, clip):
    clip_row = [row for row in csv_array if int(row[6]) == clip.clip_index]

    if len(clip_row) == 1:
        clip_row = clip_row[0]
    else:
        print "something wrong with the input csv. duplicate clips: clip# {}" \
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
    final_time = ms_to_hhmmss(time)

    clip.start_time = str(final_time[0])
    clip.offset_time = str(final_time[2])

    return clip


def create_block_from_clips(path_to_zip, codername, lab_key):
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

    if csv_data[0][11] == "True":
        block.training = True
    if csv_data[0][12] == "True":
        block.reliability = True

    block.coder = codername
    block.lab_key = lab_key

    for file in os.listdir(clips_path):
        if file.endswith(".wav"):
            clip_index = int(file.replace(".wav", ""))
            clip = Clip(os.path.join(clips_path, file), block_index, clip_index)
            clip = fill_in_clip_info_from_csv(csv_data, clip)
            clip.audio_path = os.path.join(clips_path, file)
            block.clips.append(clip)

    block.sort_clips()

    block.id = block.clan_file + ":::" + str(block.index)

    block_length = 0
    for clip in block.clips:
        time_split = clip.timestamp.split("_")
        time_split = [int(x) for x in time_split]
        block_length += time_split[1] - time_split[0]

    time = ms_to_hhmmss([0, block_length])

    block.length = time[2]

    return block


def save_blocks_to_csv(blocks, output_path):
    with open(output_path, "wb") as out:
        writer = csv.writer(out)

        writer.writerow(["date", "coder", "lab_name", "clan_file", "audiofile", "block", "instance",
                         "timestamp", "clip", "tier", "label", "gender",
                         "dont_share", "training", "reliability"])

        for block in blocks:
            dont_share = False
            if block.dont_share:
                dont_share = True

            for clip in block.clips:
                writer.writerow([clip.label_date, clip.coder, block.lab_name, clip.clan_file,
                                 clip.parent_audio_path, clip.block_index, block.instance,
                                 clip.timestamp, clip.clip_index, clip.clip_tier,
                                 clip.classification, clip.gender_label, dont_share,
                                 block.training, block.reliability])
