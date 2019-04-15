"""
Function to watch an electronic referrals folder (filled with CSV) and look for line feed characters to remove.
"""

import os
import time
import stat
import shutil
import sys
import logging
import logging.handlers
from optparse import OptionParser

# Constants
LF = 10
CR = 13
SPACE = 32


def create_logger(filepath, backupCount=1, formatting=None, name=None):
    if name:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if formatting:
        formatter = logging.Formatter(formatting)
    else:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    rfh = logging.handlers.RotatingFileHandler(filepath, maxBytes=10*1024*1024, backupCount=backupCount)
    rfh.setLevel(logging.INFO)
    rfh.setFormatter(formatter)
    logger.addHandler(rfh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def check_file(filepath):
    with open(filepath, 'rb') as F:
        raw = F.read()

    is_valid = True
    fixed_file = []
    chars = [c for c in raw]
    for i in range(0, len(chars)):
        # If the character is a LF character and the character before 
        # is not a CR then mark as bad
        if chars[i] == LF and chars[i-1] == CR:
            fixed_file.append(chars[i])
        elif chars[i] == LF and chars[i-1] != CR:
            fixed_file.append(SPACE)
            is_valid = False
        else:
            fixed_file.append(chars[i])
    return (is_valid, bytes(fixed_file))


def fix_file(filepath, fixed_file):
    with open(filepath, 'wb') as F:
        F.write(fixed_file)


def run(path, file):
    logger.debug('Checking file: {}'.format(file))
    filepath = os.path.join(path, file)

    is_valid, fixed_file = check_file(filepath)
    if not is_valid:
        logger.info('Error found in {}'.format(file))
        fix_file(filepath, fixed_file)
    else:
        logger.info('Checked {}. Okay'.format(file))


if __name__ == "__main__":
    # Get the command line parameters
    parser = OptionParser()
    parser.add_option("-p", "--path", dest="path", help="The filepath to watch", default=None)
    parser.add_option("-l", "--log", dest="logfilepath", help="The path of the log file", default=None)
    parser.add_option("-e", "--extension", dest="extension", help="The extension of the files (ie. .TXT)", default='TXT')
    (options, args) = parser.parse_args()

    logger = create_logger(options.logfilepath)
    logger.info('---Starting script---')
    logger.info('Settings: {}'.format(options))

    path = options.path
    if not os.path.isdir(path):
        logger.error('Invalid path: {}'.format(path))

    extension = options.extension
    if not extension:
        logger.error('No extension supplied')

    processed_files = []
    files = []
    current_file = None

    while True:
        try:
            if len(files) > 0:
                for file in files:
                    current_file = file
                    try:
                        run(path, file)
                    except (PermissionError, FileNotFoundError, FileExistsError):
                        logger.exception('Error processing file: {}'.format(current_file))
                processed_files += files
            all_files = [f for f in os.listdir(path) if f.lower().endswith(extension.lower())]
            processed_files = list(set([f for f in processed_files if f in all_files]))
            files = [f for f in all_files if f not in processed_files]
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info('Closed with keyboard interrupt')
            break
        except:
            logger.exception('Unhandled exception while processing file: {}'.format(current_file))
            break
