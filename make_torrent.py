"""
we are going to have a python importable command line
runnable bittorent creating tool.

goals:
Can create a meta file from N files
"""


import os.path

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

    @classmethod
    def determine_piece_size(cls, total_size):
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

    @classmethod
    def determine_file_sizes(cls, file_paths):
        """ recursively walks through files / dirs return lookup of sizes """
        to_return = {}
        for path in file_paths:
            to_return[path] =  os.path.getsize(path)

        return to_return

    @classmethod
    def create_info_dict(cls,file_paths,pieces=None,file_sizes=None,
                         piece_size=None,total_size=None,
                         private=False,create_md5=False):
        """ creates a dict of the 'info' part of the meta data """
        # fill out our data
        if not file_sizes:
            file_sizes = self.determine_file_sizes(file_paths)
        if not total_size:
            total_size = sum(file_sizes.itervalues())
        if not piece_size:
            piece_size = self.determine_piece_size(total_size)

        # create our meta data dict
        info_data = {
            'piece length': piece_size,
            'pieces': ''.join(pieces),
            'private': 1 if private else 0,
        }

        # don't have to have a file name
        if file_name:
            info_data['name'] = file_name

        # length only appropriate if there is a single file
        if len(file_paths) > 1:
            info_data['length'] = total_size

            # if they want us to create the optional md5
            # for the files than lets do so
            if create_md5:
                info_data['md5sum'] = self.md5sum(file_paths[0])

        # if it's multiple files we give it each one individually
        else:
            info_data['files'] = self.create_files_info(file_paths,
                                                        file_sizes,
                                                        create_md5)

        # make sure our meta info is valid
        try:
            validate_meta_info(info_data)
        except, ex:
            raise

        # encode our strings into UTF-8
        self.encode_meta_info_strings(info_data)

        return info_data

    @classmethod
    def hash_pieces(cls,file_paths,file_sizes=None,piece_size=None):
        """ returns back a string hash of the pieces """
        # fill in our data
        if not file_sizes:
            file_sizes = self.determine_file_sizes(file_paths)

        if not piece_size:
            total_size = sum(file_sizes.itervalues())
            piece_size = self.determine_piece_size(total_size)

        # now we go through the files data concatenated end to end
        # hashing pieces along the way
        data_pos = 0L
        pieces = []
        piece_pos = 0L
        sh = sha()
        for path in file_paths:
            # pull this file's size
            file_size = file_sizes.get(path)

            # keep track of our pos w/in the file
            file_pos = 0L

            # open the file
            with file(path,'rb') as fh:
                # loop through the files data
                while file_pos < size:
                    # b/c we might hit the end of the file or the end of a piece
                    # we don't just want to read a while piece
                    read_len = min(file_size-file_pos,piece_length-piece_position)
                    data = fh.read(read_len)
                    sh.update(data)

                    # update our positions
                    file_pos += read_len
                    data_pos += read_len
                    piece_pos += read_len

                    # if we hit the end of a piece hash our data collected
                    if piece_pos == piece_len:
                        pieces.append(sh.digest())
                        piece_pos = 0L


        # if we finished w/ some data left over add it
        if piece_pos > 0:
            pieces.append(sh.digest())

        return ''.join(pieces)

    @classmethod
    def create_files_info(cls,file_paths,file_sizes=None,create_md5=False):
        """ create dict of file info for the info section of meta data.
            file_paths can also be a dict who's key is the file path
            and the value is the file size """

        if not file_sizes:
            file_sizes = self.determine_file_sizes(file_paths)

        files_info = []
        # go through our files adding thier info dict
        for path in file_paths:
            file_info = {
                'length': file_sizes.get(path),
                'name': self.get_name(path)
            }
            if create_md5:
                file_info['md5sum'] = self.md5sum(path)
            files_info.append(file_info)

        return files_info

    @classmethod
    def encode_meta_info_strings(cls,info_data,encoding=None):
        """ encodes file/path names (UTF-8) """
        # pick our encoding
        if not encoding:
            encoding = self.encoding or 'ascii'

        if info_data.get('name'):
            u = unicode(info_data.get('name'))
            info_data['name'] = u.encode('UTF-8')

        if info_data.get('files'):
            for file_info in info_data.get('files'):
                if file_info.get('path'):
                    file_info['path'] = 
                if file_info.get('name'):
                    file_info['name'] = 

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

        # get the file sizes
        file_sizes = self.determine_file_sizes(file_paths)

        # determine our total
        total_size = sum(file_sizes.itervalues())

        # lets figure out what our piece size will be
        if not piece_size: # did they pass us a value ?
            if self.piece_size:
                piece_size = self.piece_size # did they set a default ?
            else:
                piece_size = self.determine_piece_size(total_size)

        # lets get our hash
        piece_hashes = self.hash_pieces(file_paths,file_sizes,piece_size)

        # create our info dict
        info_data = self.create_info_dict(file_paths,
                                          pieces,
                                          file_sizes,
                                          piece_size,
                                          total_size,
                                          private)


        # success ?
        try:
            self.validate_info_data(info_data)
        except ex:
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

    parser = OptionParser(usage=usage,
                          option_class=CleverOption)

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
                      help="no output"

    # file list
    parser.add_option("-f", "--file","--files",
                      dest="info",
                      type="abs_path",
                      action="extend",
                      help="list of files or directories")

    # announce
    parser.add_option("-a", "--announce",
                      dest="annouce",
                      action="store",
                      help="list of trackers")

    # announce-list
    parser.add_option("-al", "--announce-list",
                      dest="announce-list",
                      action="sub_list",
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
    parser.add_option("-cb","--created-by",
                      dest="created by",
                      help="created by")
