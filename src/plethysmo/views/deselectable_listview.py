from PyQt5 import QtCore, QtGui, QtWidgets


class DeselectableListView(QtWidgets.QListView):

    deselectItem = QtCore.pyqtSignal(QtWidgets.QListView)

    def __init__(self, parent):
        """Constructor.
        """

        super(DeselectableListView, self).__init__(parent)

        self._current_index = None

    def mousePressEvent(self, event):
        """Event handler for mouse press event.

        Args:
            event (QtCore.QEvent): the mouse press event
        """

        super(DeselectableListView, self).mousePressEvent(event)

        if event.type() == QtCore.QEvent.MouseButtonPress:

            if self.currentIndex() != self._current_index:
                self._current_index = self.currentIndex()
            else:
                self.selectionModel().clear()
                self.deselectItem.emit(self)
                self._current_index = None
