import os.path
import logging as log

from types import StringType, LongType, IntType, ListType, DictType
ints = (LongType, IntType)
strings = (StringType,unicode)
from re import compile
from sha import sha
from hashlib import md5

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def determine_torrent_name(files):
    # if they gave us a single path and it was a dir
    # than use the dir name as the torrent name
    if len(files) == 1 and os.path.isdir(files[0]):
        name = os.path.basename(files[0])
        # if for some reason we did not get an abs path
        # than use what we have
        name = files[0].replace(os.sep,'')
        log.debug('name: %s',name)
        return name

    return None

def validate_info_data(info_data):
    """ raises exceptions if data is bad """
    reg = compile(r'^[^/\\.~][^/\\]*$')

    # we must represent the info as a dict
    if type(info_data) != DictType:
        raise ValueError('invalid info: data must be a dictionary')

    # make sure our pieces are a string % 20
    pieces = info_data.get('pieces')
    if type(pieces) != StringType or len(pieces) % 20 != 0:
        raise ValueError('invalid info: bad piece key')

    # check our torrent's name
    name = info_data.get('name')
    log.debug('validating name: %s',name)
    if type(name) != StringType:
        raise ValueError('invalid info: bad name :: %s' % name)

    # check our security regex against the name
    if not reg.match(name):
        raise ValueError('invalid info: bad name for security reasons')

    # we can't have both a files list and a length value
    if 'files' in info_data and 'length' in info_data:
        raise ValueError('invalid info: single/multiple info')


    if 'files' in info_data:
        files = info_data.get('files')

        # our files must be a list
        if type(files) != ListType:
            raise ValueError('invalid info: files must be list')

        # check each of our sub files
        duplicate_check = {}
        for file_data in files:
            # they are represented as dicts
            if type(file_data) is not DictType:
                raise ValueError('invalid info: file data must be dict')

            # they have an int non 0 length
            length = file_data.get('length')
            if type(length) not in ints or length < 0:
                raise ValueError('invalid info: bad file length')

            # our path must be secure and a list of strings
            path = file_data.get('path')
            if type(path) != ListType or path == []:
                raise ValueError('invalid info: bad file path :: %s' % path)
            # check our path dirs, secure strings
            for path_piece in path:
                if type(path_piece) not in strings:
                    raise ValueError('invalid info: bad path dir: %s',                                          path_piece)
                if not reg.match(path_piece):
                    raise ValueError('invalid info: insecure path dir')

            # make sure we haven't seen this guy before
            if tuple(path) in duplicate_check:
                raise ValueError('invalid info: duplicate path')
            else:
                duplicate_check[tuple(path)] = True


    # if we are a single file we will have a length
    # represented as an int
    else:
        length = info_data.get('length')
        if type(length) not in ints or length < 0:
            raise ValueError('invalid info: bad length')


    return True


def convert_unicode(s,encoding):
    try:
        if type(s) is ListType:
            s = [unicode(x,encoding) for x in s]
        else:
            s = unicode(s,encoding)
    except UnicodeError:
        raise UnicodeError('bad filename: %s' % s)
    return s


def find_files(path,extension=None,exclude=None):
    """ returns abs list of paths found recursively 
        searching from passed path. excluding paths
        which contain exclude arg and only including
        paths which meet the extension arg """
    # absolute paths
    found = []

    for dir_path, dir_names, file_names in os.walk(path,followlinks=True):
        # remove paths which include the exclude string
        # this will keep them from being traversed
        if exclude:
            bad_dirs = [x for x in dir_names if exclude in dir_names]
            map(dir_names.remove,bad_dirs)

        # see if any of the current files meet our
        # extensio and exclude criteria
        for name in file_names:
            if (not extension or x.endswith(extension)) \
               and (not exclude or exclude not in x):
                found.append(os.path.join(dir_path,name))

    return [os.path.abspath(path) for path in found]


def get_file_name(path,rel_file_base=None):
    """ guesses from the path what the name should be,
        expects paths to be relative or base to be
        provided """
    base = rel_file_base or ''
    if path.startswith(base):
        path = path[len(base):]
    pieces = [x for x in path.split(os.sep) if x.strip()]
    if len(pieces) == 1:
        name = pieces[0]
    else:
        # we should receive a bas if these paths
        # are not relative
        name = pieces
    log.debug('get_name: %s %s',path,name)
    return name


def get_common_name(paths,rel_file_base=None):
    """ returns the basename of the common prefix
        if there are more than one paths. """

    base = rel_file_base or ''

    if len(paths) == 1:
        # we shouldn't find ourin this case,
        # but we'll go ahead and do the deed anyway
        name = get_file_name(paths[0],rel_file_base)

    else:
        # see if they share a common prefix
        prefix = os.path.commonprefix(paths)

        # see if we are left w/ anything after we take out the base
        if prefix.startswith(base):
            prefix = prefix[len(base):]

        if prefix.endswith(os.sep):
            prefix = prefix[:-1]

        # if they do than lets go ahead and make the base of that the name
        if prefix:
            name = os.path.basename(prefix)
            log.debug('name: %s',name)

        # if they don't than we are going to return None
        else:
            name = None

    log.debug('get_common_name: %s %s' % (paths,name))
    return name


def determine_file_sizes(file_paths):
    """ recursively walks through files / dirs return lookup of sizes """
    to_return = {}
    for path in file_paths:
        to_return[path] =  os.path.getsize(path)

    return to_return


def md5sum(path):
    log.debug('creating md5: %s',path)
    # create the md5 for the given file
    if not os.path.exists(path):
        raise Exception('File not found')

    file_sum = md5()
    with file(path,'rb') as fh:
        while True:
            chunk = fh.read(128)
            if not chunk:
                break
            file_sum.update(chunk)

    digest = file_sum.digest()
    return digest


def determine_piece_size(total_size):
    exponent = 15 # < 4mb, 32k pieces
    if total_size   > 8L*1024*1024*1024: # > 8gb, 2mb pieces
        exponent = 21
    elif total_size > 2L*1024*1024*1024: # > 2gb, 1mb pieces
        exponent = 20
    elif total_size > 512L*1024*1024: # > 512mb, 512k pieces
        exponent = 19
    elif total_size > 64L*1024*1024: # > 64mb, 265k pieces
        exponent = 18
    elif total_size > 16L*1024*1024: # > 16mb, 128k pieces
        exponent = 17
    elif total_size > 4L*1024*1024: # > 4mb, 64k pieces
        exponent = 16
    return 2 ** exponent

