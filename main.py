import os
import time
import stat
import shutil
import sys
import logging
import logging.handlers
from optparse import OptionParser


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


def file_is_valid(filepath):
    with open(filepath, 'rb') as F:
        raw = F.read()
    is_valid = True
    chars = [c for c in raw]
    for i in range(0, len(chars)):
        # If the character is a LF character and the character before 
        # is not a CR then mark as bad
        if chars[i] == 10 and chars[i-1] != 13:
            is_valid = False
    return is_valid


def get_first_file(path):
    try:
        f1 = sorted([f for f in os.listdir(path) if f.endswith('.AST')])
    except FileNotFoundError:
        logger.error('Error listing files (FileNotFound)')
    if len(f1) > 0:
        return f1[0]
    else:
        return None


def file_age_in_seconds(filepath):
    return time.time() - os.stat(filepath)[stat.ST_MTIME] 


def move_file(path, file):
    src = os.path.join(path, file)
    dest = os.path.join(path, 'ERROR', file)
    if not os.path.isdir(os.path.join(path, 'ERROR')):
        os.mkdir(os.path.join(path, 'ERROR'))
    try:
        shutil.move(src, dest)
    except (PermissionError, FileExistsError, FileNotFoundError):
        logger.error('Unable to move {}'.format(src))


def run(PATH):
    filename = get_first_file(PATH)
    if not filename:
        return
    logger.debug('Checking file: {}'.format(filename))
    filepath = os.path.join(PATH, filename)
    time.sleep(2)

    try:
        age = file_age_in_seconds(filepath)
    except FileNotFoundError:
        logger.debug('File not found: {}'.format(filename))
        return

    if age > 10 and not file_is_valid(filepath):
        move_file(PATH, filename)
        logger.info('Error found in {}'.format(filename))
    else:
        logger.debug('File {} is okay'.format(filename))
        return


if __name__ == "__main__":
    # Get the command line parameters
    parser = OptionParser()
    parser.add_option("-p", "--path", dest="path", help="The filepath to watch", default=None)
    parser.add_option("-l", "--log", dest="logfilepath", help="The path of the log file", default=None)
    (options, args) = parser.parse_args()

    logger = create_logger(options.logfilepath)
    logger.info('---Starting script---')
    logger.info('Settings: {}'.format(options))

    path = options.path
    if not os.path.isdir(path):
        logger.error('Invalid path: {}'.format(path))

    while True:
        try:
            run(path)
        except:
            logger.exception('Unhandled exception')
