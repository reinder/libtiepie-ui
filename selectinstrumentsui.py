#
# This file is part of the libtiepie-ui program.
#
# Copyright (C) 2015 Reinder Feenstra <reinderfeenstra@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses>.
#
# Linking libtiepie-ui statically or dynamically with other modules is making
# a combined work based on libtiepie-ui. Thus, the terms and conditions of the
# GNU General Public License cover the whole combination.
#
# In addition, as a special exception, the copyright holders of libtiepie-ui
# give you permission to combine libtiepie-ui with free software programs or
# libraries that are released under the GNU LGPL and with code included in the
# standard release of libtiepie (or modified versions of such code). You may
# copy and distribute such a system following the terms of the GNU GPL for
# libtiepie-ui and the licenses of the other code concerned.
#

from __future__ import print_function
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import libtiepie
import utils


class SelectInstrumentsUI(QDialog):
    def __init__(self, parent=None):
        super(SelectInstrumentsUI, self).__init__(parent)

        mainLayout = QVBoxLayout()

        self._list = QListView(self)
        self._list_data = QStandardItemModel(self._list)
        self._list_data_rows = []
        self._list.setModel(self._list_data)
        mainLayout.addWidget(self._list)

        buttonLayout = QHBoxLayout()
        mainLayout.addLayout(buttonLayout)

        buttonLayout.addStretch()

        btn = QPushButton("Open")
        btn.clicked.connect(self._open_clicked)
        buttonLayout.addWidget(btn)

        self._update_list()

        self.setLayout(mainLayout)
        self.setWindowTitle("Select instruments")
        self.resize(400, 200)

    def _update_list(self):
        self._list_data.clear()

        for dev in libtiepie.device_list:
            item = QStandardItem(dev.name + " s/n " + str(dev.serial_number))
            item.setCheckable(True)
            item.setData(dev)
            self._list_data.appendRow(item)
            self._list_data_rows.append(item)

    def _open_clicked(self, checked):
        for row in self._list_data_rows:
            if row.checkState() == Qt.Checked:
                utils.create_ui(utils.unwrap_QVariant(row.data()), self.parent())

        self.hide()
