"""This module implements the following classes and functions:
    - copy_selection
    - CopyFilter
    - CopyPastableTableView
"""

import csv
import io

from PyQt5 import QtCore, QtGui, QtWidgets


def _copy_selection(tableview, delimiter=','):
    """Copy the selected data of a table view to the clipboard

    Args:
        tableview (PyQt5.QtWidgets.QTableView): the table view to copy data from
    """
    selection = tableview.selectedIndexes()
    if selection:
        rows = sorted(set(index.row() for index in selection))
        columns = sorted(set(index.column() for index in selection))

        selected_column_names = [tableview.model().headerData(i, QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole) for i in columns]
        selected_row_names = [tableview.model().headerData(i, QtCore.Qt.Vertical, role=QtCore.Qt.DisplayRole) for i in rows]

        rowcount = rows[-1] - rows[0] + 1
        colcount = columns[-1] - columns[0] + 1
        table = [[''] * (colcount + 1) for _ in range(rowcount + 1)]

        table[0][0] = 'data'

        for i, v in enumerate(selected_column_names):
            table[0][i+1] = v

        for i, v in enumerate(selected_row_names):
            table[i+1][0] = v

        for index in selection:
            row = index.row() - rows[0]
            column = index.column() - columns[0]
            table[row+1][column+1] = index.data()

        stream = io.StringIO()
        csv.writer(stream, delimiter=delimiter).writerows(table)
        QtWidgets.QApplication.clipboard().setText(stream.getvalue())


class _CopyFilter(QtCore.QObject):
    """This class implements an event filter when the user press Ctrl-C on a copy-pastable table view.
    """

    def __init__(self, delimiter, *args, **kwargs):

        super(_CopyFilter, self).__init__(*args, **kwargs)

        self._delimiter = delimiter

    def eventFilter(self, source, event):
        """Event filter when the user press Ctrl-C on a copy-pastable table view.

        Args:
            source (pigcel.gui.widgets.copy_pastable_tableview.CopyPastableTableView): the table view
            event (PyQt5.QtCore.QEvent): the event 
        """

        if (event.type() == QtCore.QEvent.KeyPress and event.matches(QtGui.QKeySequence.Copy)):
            _copy_selection(source, delimiter=self._delimiter)
            return True
        return super(_CopyFilter, self).eventFilter(source, event)


class CopyPastableTableView(QtWidgets.QTableView):
    """This class implements a table view whose selection can be copy and pasted to the clipboard
    """

    def __init__(self, delimiter, *args, **kwargs):

        super(CopyPastableTableView, self).__init__(*args, **kwargs)

        copy_filter = _CopyFilter(delimiter, self)
        self.installEventFilter(copy_filter)
