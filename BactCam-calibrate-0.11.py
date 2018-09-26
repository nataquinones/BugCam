# python3
'''
BactCam-calibrate-0.1.py

BactCam-calibrate assists with the computing of light and dark
thresholds for BactCam.
'''

from PIL import Image, ImageStat, ExifTags
import os
import pandas as pd

__author__ = 'Natalia Quinones-Olvera'
__email__ = "nquinones@g.harvard.edu"

# .............................FUNCTIONS................................



def brigthness values(folder, sample=True, xtension='*'):
    '''
    '''
    df = pd.DataFrame()

    files = []

    print('Finding files...')
    for file in os.listdir(folder):
        if extension == '*':
            files.append(file)
        else:
            if file.endswith(extension):
                files.append(file)

    print('Done.')

    dates_list = []
    avgpx_list = []

    print('Reading images...')

    i = 1
    tot = len(files)


    for img_path in files:
        print('\tProcessing {}, {}/{}'.format(img_path, i, tot))
        # read imgae file with PIL
        img = Image.open(img_path)
        # fetch original date from img metadata
        date = img._getexif()[36867]
        # convert image to black and white
        bwimg = img.convert('L')
        # compute average brightness
        avgpx = ImageStat.Stat(bwimg).mean[0]

        dates_list.append(date)
        avgpx_list.append(avgpx)

        i = i + 1

    print('Done.')

    print('Making df...')

    df['file'] = files
    df['date'] = dates_list
    df['brightness'] = avgpx_list

    df = df.sort_values(by='date')
    df = df.reset_index(drop=True)

    print('Done.')

    print('Getting deltas...')

    deltas_list = []
    for i in range(1, len(df['brightness'])):
        delta = df['brightness'][i] - df['brightness'][i-1]
        deltas_list.append(delta)

    print('Done')

    deltas_list = [np.nan] + deltas_list

    df['delta'] = deltas_list

    return df
