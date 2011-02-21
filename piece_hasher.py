from helpers import determine_file_sizes
from sha import sha

class PieceHasher(object):
    """
    generates "pieces" hash
    """
    def add(self):
        """ add a file to be included """
        pass

    def remove(self):
        """ remove an already included file """
        pass

    def digest(self):
        """ generate the pieces string """
        pass

class StraitPieceHasher(PieceHasher):
    """
    will generate a pieces hash for the given files. nothing fancy.
    """
    def __init__(self,paths=[]):
        # lookup of file data key'd off abs path
        self.files = dict(( (p, None) for p in paths))

    def add(self,path):
        """
        will add given path to files to be hashed
        """
        path = os.path.abspath(path)
        self.files[path] = None
        return True

    def remove(self):
        """
        will remove path from those to be hashed
        """
        path = os.path.abspath(path)
        if path in self.files:
            del self.files[path]
            return True
        return False

    def digest(self,piece_size=None):
        # we are going strait up and down with this

        # fill in our datas
        file_paths = self.files.keys()
        file_sizes = determine_file_sizes(file_paths)
        total_size = sum(file_sizes.itervalues())
        piece_size = piece_size or determine_piece_size(total_size)

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
                while file_pos < file_size:
                    # b/c we might hit the end of the file or
                    # the end of a piece
                    # we don't just want to read a while piece
                    read_len = min(file_size-file_pos,piece_size-piece_pos)
                    data = fh.read(read_len)
                    sh.update(data)

                    # update our positions
                    file_pos += read_len
                    data_pos += read_len
                    piece_pos += read_len

                    # if we hit the end of a piece hash our data collected
                    if piece_pos == piece_size:
                        pieces.append(sh.digest())
                        piece_pos = 0L


        # if we finished w/ some data left over add it
        if piece_pos > 0:
            pieces.append(sh.digest())

        return ''.join(pieces)















        # we are going to fill out the info for the files
        # we don't have info for
        for path, info in self.files.iteritems():
            # first check and see if we have the size
            # we need to be sure to include 0 size files
            if info.get('size') is None:
                info['size'] = os.path.getsize(path)


