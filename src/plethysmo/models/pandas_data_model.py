import numpy as np

import pandas as pd

from PyQt5 import QtCore, QtGui


class PandasDataModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, data_frame=None):
        """Constructor.        
        """
        super(PandasDataModel, self).__init__(parent)

        if data_frame is None:
            self._data_frame = pd.DataFrame()
        else:
            self._data_frame = data_frame

    def clear(self):
        """Clear the data frame.
        """

        self._data_frame = pd.DataFrame()
        self.layoutChanged.emit()

    def columnCount(self, parent=None):
        return self._data_frame.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        value = self._data_frame.iloc[index.row(), index.column()]

        if role == QtCore.Qt.DisplayRole:
            return str(value)

        elif role == QtCore.Qt.ToolTipRole:
            return str(value)

        elif role == QtCore.Qt.BackgroundRole:

            try:
                return QtGui.QBrush(QtGui.QColor(255, 119, 51)) if np.isnan(float(value)) else QtGui.QBrush(QtCore.Qt.white)
            except ValueError:
                return QtGui.QBrush(QtCore.Qt.white)

        return None

    def headerData(self, index, orientation, role):
        """Returns the header data for a given index, orientation and role.

        Args:
            index (int): the index
            orientation (int): the orientation
            role (int): the role
        """

        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self._data_frame.columns[index])
            else:
                return str(self._data_frame.index[index])
        return None

    def rowCount(self, parent=None):
        """Returns the number of row of the pandas data frame.
        """

        return self._data_frame.shape[0]

    def set_data_frame(self, data_frame):
        """Set the data frame.

        Args:
            data_frame (pandas.DataFrame): the data frame
        """

        self._data_frame = data_frame

        self.layoutChanged.emit()
