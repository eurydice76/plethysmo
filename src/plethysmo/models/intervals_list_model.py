import time

from PyQt5 import QtCore

class IntervalsListModelError(Exception):
    """Error handler for exception related with IntervalsListModel class.
    """

class IntervalsListModel(QtCore.QAbstractListModel):
    """This class implements a model for the list of search intervals found for a given EDF file.
    """

    SelectedInterval = QtCore.Qt.UserRole + 1

    def __init__(self, intervals, dt, parent):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QObject): the parent object
        """

        super(IntervalsListModel, self).__init__(parent)

        self._intervals = intervals

        self._dt = dt

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

        row = index.row()

        selected_interval = self._intervals[row]

        if role == QtCore.Qt.DisplayRole:
            t_start = time.strftime('%H:%M:%S',time.gmtime(selected_interval[0]*self._dt))
            t_end = time.strftime('%H:%M:%S',time.gmtime(selected_interval[1]*self._dt))
            return '{} --- {}'.format(t_start,t_end)

        elif role == QtCore.Qt.ToolTipRole:
            return '{:d}:{:d}'.format(selected_interval[0],selected_interval[1])

        elif role == IntervalsListModel.SelectedInterval:
            return selected_interval

        else:
            return QtCore.QVariant()

    def remove_interval(self, index):
        """Remove an EDF file from its index
        """

        self.beginRemoveRows(QtCore.QModelIndex(), index, index)

        try:
            del self._intervals[index]
        except IndexError:
            pass

        self.endRemoveRows()

    def rowCount(self, parent=None):
        """Returns the number of row of the model.
        """

        return len(self._intervals)