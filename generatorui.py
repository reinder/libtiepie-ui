#!/usr/bin/env python
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

SIGNAL_TYPES = [
    {"value": libtiepie.ST_SINE, "name": "Sine"},
    {"value": libtiepie.ST_TRIANGLE, "name": "Triangle"},
    {"value": libtiepie.ST_SQUARE, "name": "Square"},
    {"value": libtiepie.ST_PULSE, "name": "Pulse"},
    {"value": libtiepie.ST_DC, "name": "DC"},
    {"value": libtiepie.ST_NOISE, "name": "Noise"},
]

ROW_OUTPUT_ON = 0
ROW_OUTPUT_INVERT = 1
ROW_SIGNAL_TYPE = 2
ROW_FREQUENCY = 3
ROW_PERIOD = 4
ROW_WIDTH = 5
ROW_AMPLITUDE = 6
ROW_OFFSET = 7
ROW_PHASE = 8
ROW_SYMMETRY = 9
ROW_BUTTONS = 10


class GeneratorUI(QDialog):
    def __init__(self, gen, parent=None):
        super(GeneratorUI, self).__init__(parent)

        self._gen = gen

        mainLayout = QGridLayout()

        # Output on:
        cb = QCheckBox()
        cb.clicked.connect(self._output_on_clicked)
        mainLayout.addWidget(QLabel("Output on:"), ROW_OUTPUT_ON, 0)
        mainLayout.addWidget(cb, ROW_OUTPUT_ON, 1)
        self._output_on = cb

        # Output invert:
        cb = QCheckBox()
        cb.clicked.connect(self._output_invert_clicked)
        mainLayout.addWidget(QLabel("Output invert:"), ROW_OUTPUT_INVERT, 0)
        mainLayout.addWidget(cb, ROW_OUTPUT_INVERT, 1)
        self._output_invert = cb

        # Signal Type:
        cb = QComboBox()
        for st in SIGNAL_TYPES:
            if (gen.signal_types & st["value"]) != 0:
                cb.addItem(st["name"], st["value"])
                if gen.signal_type == st["value"]:
                    cb.setCurrentIndex(cb.count() - 1)
        cb.currentIndexChanged.connect(self._signal_type_changed)
        mainLayout.addWidget(QLabel("Signal type:"), ROW_SIGNAL_TYPE, 0)
        mainLayout.addWidget(cb, ROW_SIGNAL_TYPE, 1)
        self._signal_type = cb

        # Frequency:
        dsb = QDoubleSpinBox()
        dsb.setDecimals(6)
        mainLayout.addWidget(QLabel("Frequency:"), ROW_FREQUENCY, 0)
        mainLayout.addWidget(dsb, ROW_FREQUENCY, 1)
        mainLayout.addWidget(QLabel("Hz"), ROW_FREQUENCY, 2)
        self._frequency = dsb

        # Period:
        dsb = QDoubleSpinBox()
        dsb.setDecimals(9)
        dsb.valueChanged.connect(self._period_changed)
        mainLayout.addWidget(QLabel("Period:"), ROW_PERIOD, 0)
        mainLayout.addWidget(dsb, ROW_PERIOD, 1)
        mainLayout.addWidget(QLabel("s"), ROW_PERIOD, 2)
        self._period = dsb

        # Width:
        dsb = QDoubleSpinBox()
        dsb.setDecimals(9)
        dsb.valueChanged.connect(self._width_changed)
        mainLayout.addWidget(QLabel("Width:"), ROW_WIDTH, 0)
        mainLayout.addWidget(dsb, ROW_WIDTH, 1)
        mainLayout.addWidget(QLabel("s"), ROW_WIDTH, 2)
        self._width = dsb

        # Amplitude:
        dsb = QDoubleSpinBox()
        dsb.setDecimals(3)
        dsb.valueChanged.connect(self._amplitude_changed)
        mainLayout.addWidget(QLabel("Amplitude:"), ROW_AMPLITUDE, 0)
        mainLayout.addWidget(dsb, ROW_AMPLITUDE, 1)
        mainLayout.addWidget(QLabel("V"), ROW_AMPLITUDE, 2)
        self._amplitude = dsb

        # Offset:
        dsb = QDoubleSpinBox()
        dsb.setDecimals(3)
        dsb.valueChanged.connect(self._offset_changed)
        mainLayout.addWidget(QLabel("Offset:"), ROW_OFFSET, 0)
        mainLayout.addWidget(dsb, ROW_OFFSET, 1)
        mainLayout.addWidget(QLabel("V"), ROW_OFFSET, 2)
        self._offset = dsb

        # Phase:
        dsb = QDoubleSpinBox()
        dsb.valueChanged.connect(self._phase_changed)
        mainLayout.addWidget(QLabel("Phase:"), ROW_PHASE, 0)
        mainLayout.addWidget(dsb, ROW_PHASE, 1)
        mainLayout.addWidget(QLabel("deg"), ROW_PHASE, 2)
        self._phase = dsb

        # Symmetry:
        dsb = QDoubleSpinBox()
        dsb.valueChanged.connect(self._symmetry_changed)
        mainLayout.addWidget(QLabel("Symmetry:"), ROW_SYMMETRY, 0)
        mainLayout.addWidget(dsb, ROW_SYMMETRY, 1)
        mainLayout.addWidget(QLabel("%"), ROW_SYMMETRY, 2)
        self._symmetry = dsb

        # Buttons:
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        mainLayout.addLayout(button_layout, ROW_BUTTONS, 0, 1, 3)

        pb = QPushButton("Start")
        pb.clicked.connect(self._start_clicked)
        button_layout.addWidget(pb)
        self._start = pb

        pb = QPushButton("Stop")
        pb.clicked.connect(self._stop_clicked)
        button_layout.addWidget(pb)
        self._stop = pb

        self.setLayout(mainLayout)
        self.setWindowTitle(gen.name + " s/n " + str(gen.serial_number))
        self._update_controls()
        self._frequency.valueChanged.connect(self._frequency_changed)

    def _output_on_clicked(self, value):
        self._gen.output_on = value

    def _output_invert_clicked(self, value):
        self._gen.output_invert = value

    def _signal_type_changed(self, index):
        self._gen.signal_type = self._signal_type.itemData(index).toInt()[0]
        self._update_controls()

    def _frequency_changed(self, value):
        self._gen.frequency = value

    def _period_changed(self, value):
        self._gen.frequency = 1 / value
        self._update_width()

    def _width_changed(self, value):
        self._gen.width = value

    def _amplitude_changed(self, value):
        self._gen.amplitude = value
        self._update_offset()

    def _offset_changed(self, value):
        self._gen.offset = value
        if self._gen.signal_type != libtiepie.ST_DC:
            self._update_amplitude()

    def _phase_changed(self, value):
        self._gen.phase = value / 360

    def _symmetry_changed(self, value):
        self._gen.symmetry = value / 100

    def _start_clicked(self, value):
        self._gen.start()

    def _stop_clicked(self, value):
        self._gen.stop()

    def _update_controls(self):
        if self._update_row_visible(ROW_FREQUENCY, (self._gen.signal_type & libtiepie.STM_FREQUENCY) != 0 and self._gen.signal_type != libtiepie.ST_PULSE):
            self._update_frequency()
        if self._update_row_visible(ROW_PERIOD, (self._gen.signal_type & libtiepie.STM_FREQUENCY) != 0 and self._gen.signal_type == libtiepie.ST_PULSE):
            self._update_period()
        if self._update_row_visible(ROW_WIDTH, (self._gen.signal_type & libtiepie.STM_WIDTH) != 0):
            self._update_width()
        if self._update_row_visible(ROW_AMPLITUDE, (self._gen.signal_type & libtiepie.STM_AMPLITUDE) != 0):
            self._update_amplitude()
        if self._update_row_visible(ROW_OFFSET, (self._gen.signal_type & libtiepie.STM_OFFSET) != 0):
            self._update_offset()
        if self._update_row_visible(ROW_PHASE, (self._gen.signal_type & libtiepie.STM_PHASE) != 0):
            self._update_phase()
        if self._update_row_visible(ROW_SYMMETRY, (self._gen.signal_type & libtiepie.STM_SYMMETRY) != 0):
            self._update_symmetry()

    def _update_row_visible(self, row, visible):
        for column in range(self.layout().columnCount()):
            w = self.layout().itemAtPosition(row, column).widget()
            if w:
                w.setVisible(visible)
        return visible

    def _update_frequency(self):
        self._frequency.setRange(self._gen.frequency_min, self._gen.frequency_max)
        self._frequency.setValue(self._gen.frequency)

    def _update_period(self):
        self._period.setRange(1 / self._gen.frequency_max, 1 / self._gen.frequency_min)
        self._period.setValue(1 / self._gen.frequency)

    def _update_width(self):
        self._width.setRange(self._gen.width_min, self._gen.width_max)
        self._width.setValue(self._gen.width)

    def _update_amplitude(self):
        self._amplitude.setRange(self._gen.amplitude_min, self._gen.verify_amplitude(self._gen.amplitude_max))
        self._amplitude.setValue(self._gen.amplitude)

    def _update_offset(self):
        self._offset.setRange(self._gen.verify_offset(self._gen.offset_min), self._gen.verify_offset(self._gen.offset_max))
        self._offset.setValue(self._gen.offset)

    def _update_phase(self):
        self._phase.setRange(self._gen.phase_min * 360, self._gen.phase_max * 360)
        self._phase.setValue(self._gen.phase * 360)

    def _update_symmetry(self):
        self._symmetry.setRange(self._gen.symmetry_min * 100, self._gen.symmetry_max * 100)
        self._symmetry.setValue(self._gen.symmetry * 100)


if __name__ == '__main__':
    import sys

    libtiepie.device_list.update()

    try:
        dev = utils.try_open_device(sys.argv, libtiepie.DEVICETYPE_GENERATOR)

        app = QApplication(sys.argv)

        frm = GeneratorUI(dev)
        frm.show()

        sys.exit(app.exec_())
    except Exception, e:
        print(e.message, file=sys.stderr)
        sys.exit(1)
