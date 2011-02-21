#!/usr/bin/python

"""
we are going to have a python importable command line
runnable bittorent creating tool.

goals:
Can create a meta file from N files
"""

from helpers import validate_info_data, convert_unicode, find_files, \
                    get_file_name, get_common_name, \
                    determine_file_sizes, md5sum, determine_piece_size, \
                    determine_torrent_name

from hasher import StraitHasher as Hasher

import os.path
import logging as log

from types import StringType, LongType, IntType, ListType, DictType
ints = (LongType, IntType)
strings = (StringType,unicode)
from re import compile
from hashlib import md5

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


# figure out what encoding the system wants
get_system_encoding = lambda: 'ascii'
try:
    from sys import getfilesystemencoding as get_system_encoding
except:
    from sys import getdefaultencoding as get_system_encoding

class MetaCreator:
    def __init__(self, encoding=None, piece_size=None, create_md5=False):
        """ values passed @ construction are used as defaults for creation """

        # what kind of text encoding does this machine use?
        self.encoding = encoding or get_system_encoding()

        # if we didn't get passed a piece size we'll pick later
        self.piece_size = piece_size

        # should we include the files md5s?
        self.create_md5 = create_md5

    def create_info_dict(self,file_paths,pieces=None,file_sizes=None,
                         piece_size=None,total_size=None,
                         private=False,create_md5=False,file_name=None,
                         rel_file_base=None):
        """ creates a dict of the 'info' part of the meta data """
        # fill out our data
        if not file_sizes:
            file_sizes = determine_file_sizes(file_paths)
        if not total_size:
            total_size = sum(file_sizes.itervalues())
        if not piece_size:
            piece_size = determine_piece_size(total_size)

        # create our meta data dict
        info_data = {
            'piece length': piece_size,
            'pieces': ''.join(pieces),
            'private': 1 if private else 0,
        }

        # don't have to have a file name
        if file_name:
            info_data['name'] = file_name

        # we need to determine common prefix for all the files
        # it will be our rel base, any paths for the info will
        # be relative to it
        rel_file_base = os.path.commonprefix(file_paths)

        log.debug('rel file base: %s',rel_file_base)

        # length only appropriate if there is a single file
        if len(file_paths) == 1:
            info_data['length'] = total_size

            # if they want us to create the optional md5
            # for the files than lets do so
            if create_md5:
                info_data['md5sum'] = md5sum(file_paths[0])

            if not info_data.get('name'):
                # we'll go ahead and put a name
                info_data['name'] = get_file_name(file_paths[0],
                                                  rel_file_base)

        # if it's multiple files we give it each one individually
        else:
            info_data['files'] = self.create_files_info(file_paths,
                                                        file_sizes,
                                                        create_md5,
                                                        rel_file_base)

            if not info_data.get('name'):
                # guess a name
                name = get_common_name(file_paths)
                if name:
                    info_data['name'] = name

        # make sure our meta info is valid
        try:
            validate_info_data(info_data)
        except Exception, ex:
            raise

        # encode our strings into UTF-8
        self.encode_meta_info_strings(info_data)

        return info_data

    def hash_pieces(self,file_paths,file_sizes=None,piece_size=None):
        """ returns back a string hash of the pieces """

        hasher = Hasher(file_paths)
        hash_string = hasher.digest(piece_size)
        return hash_string

    def create_files_info(self,file_paths,file_sizes=None,
                               create_md5=False,rel_file_base=None):
        """ create dict of file info for the info section of meta data.
            file_paths can also be a dict who's key is the file path
            and the value is the file size """

        if not file_sizes:
            file_sizes = determine_file_sizes(file_paths)

        files_info = []
        # go through our files adding thier info dict
        for path in file_paths:
            name = get_file_name(path,rel_file_base)
            file_info = {
                'length': file_sizes.get(path),
                'path': [x for x in name.split(os.sep) if x.strip()]
            }
            if create_md5:
                file_info['md5sum'] = md5sum(path)
            files_info.append(file_info)

        return files_info

    def encode_meta_info_strings(self,info_data,encoding=None):
        """ encodes file/path names (UTF-8) """
        # pick our encoding
        if not encoding:
            encoding = self.encoding or 'ascii'
        self.encoding = encoding # keep track of what encoding use

        if info_data.get('name'):
            u = unicode(info_data.get('name'))
            info_data['name'] = u.encode('UTF-8')

        # shortcut
        cu = convert_unicode

        if info_data.get('files'):
            for file_info in info_data.get('files'):
                if file_info.get('path'):
                    file_info['path'] = cu(file_info['path'],encoding)
                if file_info.get('name'):
                    file_info['name'] = cu(file_info['name'],encoding)

        return True

    def create_info_data(self,files,encoding=None,
                         piece_size=None,validate=True,private=False):
        """ creates dict which is the info part of a meta data file
             from a list of files / directories.
            if the list contains a directory the directory is recursively
            searched. values passed (other than file list) take priorty over
            defaults passed in @ instantiation """

        # get list of files to index
        file_paths = []
        for path in files:
            file_paths += find_files(path)

        # make sure there are any files to be had
        if not file_paths:
            raise Exception('No Files Found!')

        # get the file sizes
        file_sizes = determine_file_sizes(file_paths)

        # determine our total
        total_size = sum(file_sizes.itervalues())

        # lets figure out what our piece size will be
        if not piece_size: # did they pass us a value ?
            if self.piece_size:
                piece_size = self.piece_size # did they set a default ?
            else:
                piece_size = determine_piece_size(total_size)

        # lets get our hash
        piece_hashes = self.hash_pieces(file_paths,file_sizes,piece_size)

        # figure out what the "name" of our torrent is
        torrent_name = determine_torrent_name(files)

        # create our info dict
        info_data = self.create_info_dict(file_paths,
                                          piece_hashes,
                                          file_sizes,
                                          piece_size,
                                          total_size,
                                          private,
                                          torrent_name)

        # success ?
        try:
            validate_info_data(info_data)
        except Exception, ex:
            raise

        return info_data


if __name__ == '__main__':
    from bencode import bencode
    """
    we need to take in the following params:
     files - what do we include in the torrent? can be abs
             path or relative path to files or directories.
             the file / dir @ the most root point in the paths
             given will be considered @ root for the torrent

     announce - flat list of tracker urls, comma seperated
                or listed as seperate arguments
     announce-list - nested list of tracker urls. comma
                     seperated with double commas considered
                     lower proprity lists
     creation date - default is current system date + time.
                     to be expressed in form such as: "YYY-MM-DD HH:MM:SS".
     comment - default is blank
     created by - default is blank
    """

    from cmdline_utils import EnhancedOptionParser
    usage = "usage: %prog [options] file file2 file3 ..."
    parser = EnhancedOptionParser(usage=usage)

    # verbose
    parser.add_option("-v", "--verbose",
                      action="store_true",
                      dest="verbose",
                      default=False,
                      help="show details")

    # quite
    parser.add_option("-q", "--quite",
                      action="store_true",
                      dest="quite",
                      default=True,
                      help="no output")

    # file list
    parser.add_option("-f", "--file","--files",
                      dest="file_paths",
                      type="abspath",
                      action="extend",
                      help="list of files or directories")

    # announce
    parser.add_option("-a", "--announce",
                      dest="annouce",
                      action="store",
                      help="list of trackers")

    # announce-list
    parser.add_option("-l", "--announce-list",
                      dest="announce-list",
                      action="sublist",
                      help="prioritized list of trackers by arg #")

    # creation date
    parser.add_option("--creation-date",
                      dest="creation date",
                      type="epoch",
                      help="YYY-MM-DD HH:MM:SS")

    # comment
    parser.add_option("-c","--comment",
                      dest="comment",
                      help="comment")

    # created by
    parser.add_option("-b","--created-by",
                      dest="created by",
                      help="created by")

    # output file
    parser.add_option("-o", "--outfile",
                      action="store",
                      dest='outfile',
                      type="abspath",
                      help="where do we save the resulting file?")

    (options, args) = parser.parse_args()

    log.debug('options: %s',options)
    log.debug('args: %s',args)

    # figure out our file list
    # it can be defined in kw args or as loose args
    file_list = options.get('file_paths',[]) + args
    log.debug('file_list: %s' % file_list)

    # lets make some meta data !
    meta_creator = MetaCreator()
    info_data = meta_creator.create_info_data(file_list)

    # the info is the only non-optional data
    meta_data = {
        'info': info_data
    }

    # now optional info
    optional_options = ['announce','announce_list','creation date',
                        'comment','created by']

    # if they defined it, it should be in the neccisary format
    for attr in optional_options:
        if attr in options:
            meta_data[attr] = options.get(attr)

    # now figure out our encoding
    if meta_creator.encoding:
        meta_data['encoding'] = meta_creator.encoding

    log.debug('meta_data: %s',len(meta_data))

    # now lets save it
    log.debug('outfile: %s',options.get('outfile'))
    if options.get('outfile'):
        bencoded = bencode(meta_data)
        with file(options.get('outfile'),'wb') as fh:
            fh.write(bencoded)
