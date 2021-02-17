import collections

from PyQt5 import QtCore

from plethysmo.kernel.edf_file_reader import EDFFileReader, EDFFileReaderError

class EDFFilesListModelError(Exception):
    """Error handler for exception related with EDFFilesListModel class.
    """

class EDFFilesListModel(QtCore.QAbstractListModel):
    """This class implements a model for a list of loaded EDF files which contain plethysmography data.
    """

    Reader = QtCore.Qt.UserRole + 1

    def __init__(self, parent):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QObject): the parent object
        """

        super(EDFFilesListModel, self).__init__(parent)

        self._edf_files = collections.OrderedDict()

    def add_edf_file(self, edf_filename):
        """Add a new edf file to the model.

        Args:
            edf_filename (str): the name of the EDF file to add
        """

        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())

        try:
            reader = EDFFileReader(edf_filename)
        except EDFFileReaderError as e:
            raise EDFFilesListModelError from e
        else:
            self._edf_files[edf_filename] = reader

        self.endInsertRows()

    def data(self, index, role):
        """Return the data for given index and role.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index
            role (int): the role

        Return:
           PyQt5.QtCore.QVariant: the data 
        """

        if not index.isValid():
            return QtCore.QVariant()

        edf_filenames = list(self._edf_files.keys())

        selected_edf_file = edf_filenames[index.row()]

        reader = self._edf_files[selected_edf_file]

        if role == QtCore.Qt.DisplayRole:
            return selected_edf_file
        elif role == QtCore.Qt.ToolTipRole:
            return reader.metadata
        elif role == EDFFilesListModel.Reader:
            return reader
        else:
            return QtCore.QVariant()

    def get_reader(self, filename):
        """Get a EDF file reader from its filename.

        Args:
            filename: the name of the EDF file to get
        """

        try:
            return self._edf_files[filename]
        except KeyError:
            return None

    def remove_reader(self, filename):
        """Remove an EDF file from its filename
        """

        edf_filenames = list(self._edf_files.keys())

        try:            
            index = edf_filenames.index(filename)
        except ValueError:
            return

        self.beginRemoveRows(QtCore.QModelIndex(), index, index)

        del self._edf_files[filename]

        self.endRemoveRows()

    def remove_reader_from_index(self, index):
        """Remove an EDF file from its index
        """

        edf_filenames = list(self._edf_files.keys())

        try:
            filename = edf_filenames[index]
        except IndexError:
            return

        self.beginRemoveRows(QtCore.QModelIndex(), index, index)

        del self._edf_files[filename]

        self.endRemoveRows()

    def rowCount(self, parent=None):
        """Returns the number of row of the model.
        """

        return len(self._edf_files)