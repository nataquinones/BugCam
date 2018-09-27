# python3
'''
BugCam-run.py

BugCam monitors timelapse photography experiments.
It checks a Dropbox folder's pictures, and sends Slack messages if it
finds problems:
- No new picture in specified time period.
- Significantly different brightness from one picture to the next.

TO_DO
- Add apscheduler listener: https://apscheduler.readthedocs.io/en/latest/userguide.html#missed-job-executions-and-coalescing
- Add support to read link and time from config file
- Add browser-based(?) GUI, that displays current image and log.
'''

import argparse
import json
import os
from io import BytesIO
from datetime import datetime
import time
import dropbox
from slackclient import SlackClient
import colors
from PIL import Image, ImageStat
from apscheduler.schedulers.background import BackgroundScheduler

__author__ = 'Natalia Quinones-Olvera'
__email__ = "nquinones@g.harvard.edu"

LAST_FILE_MEM = None
DPX_CLIENT = None
SLACK_CLIENT = None
CONFIG = None
NEWPHOTO_STATUS = None
BRIGHTNESS_STATUS = None

# .............................FUNCTIONS................................
# ...............................init...................................


def main_argparser():
    """
    Command line argument parser.
    """

    script_path = os.path.split(os.path.realpath(__file__))[0]
    default_config = os.path.join(script_path, 'config/config.json')

    parser = argparse.ArgumentParser()

    parser.add_argument('url',
                        metavar='<dropbox_url>',
                        help='Dropbox share url of the folder to monitor.',
                        type=str)

    parser.add_argument('time',
                        metavar='<time>',
                        help='''Monitoring time interval in minutes.
                                (Should be the time interval of timelapse.)''',
                        type=int)

    parser.add_argument('name',
                        metavar='<name>',
                        help='''Name of the project being monitored.''')

    parser.add_argument('-c', '--config',
                        metavar='<json>',
                        help='''Path for .json config file. If not specified,
                                it will look in in the script's path for
                                config/config.json''',
                        default=default_config)

    if parser.parse_args().time == 0:
        parser.error('Time can\'t be 0 minutes! ¯\\_(ツ)_/¯')

    return parser.parse_args()


def init(args):
    '''
    Initializes Dropbox and Slack clients. Fetches metadata of Dropbox folder.
    '''
    global CONFIG
    global DPX_CLIENT
    global SLACK_CLIENT

    CONFIG = json.load(open(args.config))

    DPX_CLIENT = dropbox.Dropbox(CONFIG['private_tokens']['dropbox'])
    SLACK_CLIENT = SlackClient(CONFIG['private_tokens']['slack_bot'])

    folder_info = DPX_CLIENT.sharing_get_shared_link_metadata(args.url)

    return folder_info


# ...............................general...................................


def get_timestamps(folder_info):
    '''
    Fetches folder metadata from Dropbox,
    returns sorted list of timestamps in photos.
    '''
    # list files in folder
    dir_content = DPX_CLIENT.files_list_folder(folder_info.id,
                                               include_media_info=True,
                                               recursive=False)
    time_stamps = []

    # fetch timestamps from metadata
    for entry in dir_content.entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            filename = entry.name
            date = entry.media_info.get_metadata().time_taken
            time_stamps.append((filename, date))

    # sort time stamps
    timestamps_list = sorted(time_stamps, key=lambda x: x[1], reverse=True)

    return timestamps_list


def download_photo(folder_info, file):
    '''
    Downloads the picture from Dropbox, returns bytes object.
    '''

    # path in dropbox that files_downloads requires
    path = '{0}/{1}'.format(folder_info.path_lower, file)

    metadata, response = DPX_CLIENT.files_download(path)

    data = response.content

    img = BytesIO(data)

    return img


def get_brightness(img, mask=None):
    '''
    Using a bytes object, opens uses PIL to convert to grayscale, get hist,
    and compute mean.
    '''

    # read image as grayscale
    bwimg = Image.open(img).convert('L')

    # average pixel level for each band (1) in the image
    avgpx = ImageStat.Stat(bwimg, mask=mask).mean[0]

    return avgpx


# ...............................checks...................................

def check_newphoto(timestamps_list):
    '''
    Checks if most recent file from sorted timestamps_list is the same as
    the last file stored in memory. Updates LAST_FILE_MEM.
    '''
    global NEWPHOTO_STATUS
    global LAST_FILE_MEM

    most_recent = timestamps_list[0]

    if most_recent == LAST_FILE_MEM:
        NEWPHOTO_STATUS = 'absent'
    else:
        NEWPHOTO_STATUS = 'present'

    LAST_FILE_MEM = most_recent


def check_brightness(folder_info, timestamps_list):
    '''
    Checks if the 2 last most recent pictures have a difference in
    mean brigthness and updates BRIGHTNESS STATUS. It uses threshold
    defined in json config file.
    '''
    global BRIGHTNESS_STATUS

    th_light = CONFIG['brightness_threshold']['light']
    th_dark = CONFIG['brightness_threshold']['dark']

    file1 = timestamps_list[0][0]
    file2 = timestamps_list[1][0]

    img1 = download_photo(folder_info, file1)
    img2 = download_photo(folder_info, file2)

    brightness_diff = get_brightness(img1) - get_brightness(img2)

    if brightness_diff < th_dark:
        BRIGHTNESS_STATUS = 'decrease'
    elif brightness_diff > th_light:
        BRIGHTNESS_STATUS = 'increase'
    else:
        BRIGHTNESS_STATUS = 'stable'


def checks_response():
    '''
    Sees status variables (affected by checks) and conditionally performs
    actions based on status. (Prints statuses, sends slack messages.)
    '''

    current_time = datetime.now().isoformat(' ', 'seconds')

    # LAST FILE CHECK

    # new photo missing
    if NEWPHOTO_STATUS is 'absent':
        # local response
        print('{note} {desc: <25} {time}'.format(note=colors.red('WARNING!'),
                                                 desc='No new photo.',
                                                 time=current_time))
        # slack response
        SLACK_CLIENT.api_call("chat.postMessage",
                              channel="monitor_test",
                              text=":warning:\t*{name}*: New photo missing\t{time}".format(name=NAME,
                                                                                           time=current_time))

    # BRIGHTNESS CHECK
    elif NEWPHOTO_STATUS is 'present':

        # decrease in brightness
        if BRIGHTNESS_STATUS is 'decrease':
            # local response
            print('{note} {desc: <25} {time}'.format(note=colors.red('WARNING!'),
                                                     desc='Brightness decrease.',
                                                     time=current_time))
            # slack response
            SLACK_CLIENT.api_call("chat.postMessage",
                              channel="monitor_test",
                              text=":warning:\t*{name}*:\tBrightness decrease\t{time}".format(name=NAME,
                                                                                              time=current_time))

        # increase in brightness
        elif BRIGHTNESS_STATUS is 'increase':
            # local response
            print('{note} {desc: <25} {time}'.format(note=colors.red('WARNING!'),
                                                     desc='Brightness increase.',
                                                     time=current_time))
            # slack response
            SLACK_CLIENT.api_call("chat.postMessage",
                              channel="monitor_test",
                              text=":warning:\t*{name}*:\tBrightness increase\t{time}".format(name=NAME,
                                                                                              time=current_time))

        # stable brightness
        elif BRIGHTNESS_STATUS is 'stable':
            # local response
            print('{note} {desc: <25} {time}'.format(note='ok',
                                                     desc='',
                                                     time=current_time))

# .................................main............................................


def main():
    '''
    Main function: fetches timestamps list, performs checks on filenames and
    brightness, performs actions based on statuses.
    '''
    # fetch file list
    timestamps_list = get_timestamps(FOLDER_INFO)

    # do newphoto check
    check_newphoto(timestamps_list)
    # do brightness check
    check_brightness(FOLDER_INFO, timestamps_list)

    # respond according to STATUS
    checks_response()


# .............................................................................

if __name__ == '__main__':

    arguments = main_argparser()

    FOLDER_INFO = init(arguments)

    NAME = arguments.name

    scheduler = BackgroundScheduler(daemon=False)
    scheduler.add_job(main, 'interval', minutes=arguments.time)
    scheduler.start()

    print('# -----------------------------------------------------------')
    print('# BugCam Daemon')
    print('# -----------------------------------------------------------')
    print('# Project: {0}'.format(NAME))
    print('# Monitoring folder: {0}, every {1} minutes.'.format(FOLDER_INFO.name,
                                                         arguments.time))
    print('# Started at: {0}'.format(datetime.now().isoformat(' ', 'seconds')))
    print('# (Press Ctrl+{0} to exit)'.format('Break' if os.name == 'nt' else 'C'))
    print('#')

    SLACK_CLIENT.api_call("chat.postMessage",
                              channel="monitor_test",
                              text="*BugCam START:* {name}\t{time}".format(name=NAME,
                                                                             time=datetime.now().isoformat(' ', 'seconds')))

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        print('#')
        print('# Stopped at {0}'.format(datetime.now()))
        print('# -----------------------------------------------------------')

        SLACK_CLIENT.api_call("chat.postMessage",
                              channel="monitor_test",
                              text="*BugCam STOP:* {name}\t{time}".format(name=NAME,
                                                                             time=datetime.now().isoformat(' ', 'seconds')))
        scheduler.shutdown()
