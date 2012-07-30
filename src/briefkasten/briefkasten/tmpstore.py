import os
from StringIO import StringIO
from json import load, dump
from tempfile import mkdtemp
from shutil import rmtree
from deform.interfaces import FileUploadTempStore
import codecs


class TempFileTempStore(FileUploadTempStore):
    """
        Temporary file storage using python's builtin tempfile, writing the metadata
        to a json file.
    """

    def __init__(self):
        self.tempdir = mkdtemp()

    def preview_url(self, name):
        return None

    def get(self, name, default=None):
        try:
            return self.__getitem__(name)
        except KeyError:
            return default

    def __contains__(self, name):
        return os.path.exists(os.path.join(self.tempdir, name))

    def __getitem__(self, name):
        try:
            metadatafile = open(os.path.join(self.tempdir, '%s.json' % name))
            metadata = load(metadatafile)
            datafile = os.path.join(self.tempdir, name)
            metadata['fp'] = StringIO(codecs.open(datafile, encoding='utf-8').read())
            return metadata
        except Exception:
            raise KeyError

    def __delitem__(self, name):
        if self.__contains__(name):
            os.remove(os.path.join(self.tempdir, name))
            os.remove(os.path.join(self.tempdir, '%s.json' % name))
        else:
            raise KeyError

    def __setitem__(self, name, value):
        """ name: a unique string
            value: {
                'fp': a file handle,
                'filename': name of the filename, is only stored in metadata,
                            it won't be used for the temporary file.
            }
            any other values are stored, too.
        """
        datafile = open(os.path.join(self.tempdir, name), 'w')
        for line in value['fp'].readlines():
            datafile.write(line)
        datafile.close()
        metadatafile = open(os.path.join(self.tempdir, '%s.json' % name), 'w')
        metadata = value.copy()
        del metadata['fp']
        dump(metadata, metadatafile)
        metadatafile.close()

    def destroy(self):
        rmtree(self.tempdir)
