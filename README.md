# idslabel

Note: This is a work in progress.

![IDSLabel](include/screenshot.png)


## requirements

This application depends on FFmpeg, PortAudio and PyAudio.

#### ffmpeg
To install the ffmpeg binary, download from [here](https://www.ffmpeg.org/download.html). OS specific binaries are under the "Get the packages" section. The binary should be put in the same directory as the idslabel.py file.

#### portaudio
To install PortAudio, the easiest way is to use your operating system's package manager.

For OS X, you can use [homebrew](http://brew.sh/):
```bash
$: brew install portaudio
```

For Debian/Ubuntu Linux:
```bash
$: sudo apt-get install portaudio
```

#### pyaudio

The easiest way to install is with pip:
```bash
$: sudo pip install pyaudio
```

## usage


#### new workflow:    

- You launch the idslabel executable (double click the icon, or launch it from the command line)
- You type your name into the CODER_NAME box and press enter
 - Something should pop up asking you to set the path to the blocks directory. This is the directory where the conversation blocks will be downloaded.
 - This should be a dedicated path that you always use (try not to change it each time you run the application). When you exit the application and start it again, it'll look through the blocks already sitting there from previous sessions (unfinished, haven't submitted classifications back to the server, after submission they're deleted) and loads them again into the application so that you can continue to work on them.
 - **Do not delete the contents in that blocks directory**. If you want to get rid of things that are sitting there, label them within the running idslabel application and submit those classifications. The application will delete them after you submit the block.
- The application will then ask you to choose a config.json file. The value in the "lab-key" field is your lab's unique identifier.
- If you're running this for the first time, the next thing that should pop up is a message saying: "User: "xyz" doesn't exist on the server".
 - In the menu, go to File -> Add User to Server.
 - This will register that username as being a member of your lab. Next time when you type that name into the CODER_NAME box, the server will recognize it as being a registered name
- Next, press the "Get Blocks" button
 - this will ask the server to send X number of blocks to your computer
 - there are only 6 CLAN files sitting on the server right now, and it picks blocks based on whether or not the user already has a block checked out from that specific CLAN file. So, if you already have a block from 6 different clan files, the server won't be able to send you any more until you submit at least 1 of those blocks back with labels, and unlock that CLAN file from being a source of blocks.
   - There are 5146 blocks in total across these 6 CLAN files, so this should be enough to test things out for the time being. When we upload the whole dataset to the server, you'll be able to check out 20-50 (or more) blocks at a time.
   - You can set how many blocks the application will request from the server in the box labeled "# blocks". It should be set to 3 by default.
- Now, there should be a list of blocks sitting in the small box labeled "Load Block"
 - Blocks that were reloaded from previous sessions will have "old" next to them. Blocks you received in this current session will have "new" next to them
 - Double click one of these blocks to load it.
 - You can now select clips within this block to play and decide what they should be labeled as.
   - There's a small window that should pop up upon starting the idslabel application that lists all the shortcuts. The keys for selecting classifications are listed here. If you close this window, you can get it back by going to the menu (Help -> Show Shortcuts)
- You're only able to submit blocks that have every clip within them labeled.
 - Once you label every clip within a given block press the "Submit Labels to Server" button.
   - This will submit your classifications to the server, delete the block's data from the blocks directory, and remove it from the "Load Block" list.
- You can query the server to show you all the members of your lab and which blocks they're currently in possession of, and which blocks they've successfully submitted back to the server. This is in File -> Get Lab Info

#### shortcut keys

- General Keys
 - cmd   + s         : save classifications (Mac)
 - ctrl  + s         : save classifications (Linux/Windows)
 - cmd   + shift + s : save as classification (Mac)
 - ctrl  + shift + s : save as classification (Linux/Windows)

- Classification Keys
 - c : CDS
 - a : ADS
 - n : Child Noises
 - m : Multiple Addressee
 - r : Register Switch
 - j : Junk

- Clip Keys
 - up : previous clip
 - down: next clip
 - left          : previous clip
 - right         : next clip
 - space         : play clip
 - shift + space : play whole block



Tiers which are composed of multiple lines, e.g. :
```
*CHN:	0 2662230_2662370
  &=vocalization 2662370_2663380
  0 . 2663380_2663480
```
have a symbol associated with them to signify they're part of the unit ( " ^-- " , it's supposed to be an arrow pointing to the parent tier)

In the classification output, if clips are associated together as part of a multi-line tier, the value in the "multi-tier"
column will be the timestamp of the parent line that they're associated to. In the example provided above, the line with
the timestamp of 2662230_2662370 will be the parent to the following 2 lines.



## status

### implemented

- parsing cha file and extracting Conversation blocks
- chopping up associated audio file
 - each conversation block is chopped as a unit (upon loading)
 - each tier (except comments and *SIL) within a block is chopped into a new audio clip given its timestamp in the cha file
- randomize the blocks and allow the user to load a random one for classification
- list the clips within the currently loaded block, and allow the user to play the audio for a given clip.
- allow the user to select a classification for the currently playing clip
 - cds
 - ads
 - child noises
 - register switch
 - multiple addressee
 - junk
- export classifications to csv
- check github if current IDSLabel is the latest version

### not implemented yet

- connect to server and checkout cha/audio file for labeling
- lots of UI things (make it more convenient)
