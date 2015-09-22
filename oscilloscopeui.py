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
import pyqtgraph
import numpy as np
import ctypes as ct
import libtiepie
import utils

SAMPLE_FREQUENCY_MIN = 50

RECORD_LENGTH_MIN = 100
RECORD_LENGTH_MAX = 1000000

PRE_SAMPLE_RATIOS = range(0, 100, 10)

COUPLINGS = [
    {"value": libtiepie.CK_DCV, "name": "DCV"},
    {"value": libtiepie.CK_ACV, "name": "ACV"},
    {"value": libtiepie.CK_DCA, "name": "DCA"},
    {"value": libtiepie.CK_ACA, "name": "ACA"},
    {"value": libtiepie.CK_OHM, "name": "Ohm"},
]

TRIGGER_TIMEOUTS = [
    {"value": 0, "name": "Disabled"},
    {"value": 10e-3, "name": "10 ms"},
    {"value": 100e-3, "name": "100 ms"},
    {"value": 1, "name": "1 s"},
    {"value": 10, "name": "10 s"},
    {"value": libtiepie.TO_INFINITY, "name": "Infinite"},
]

TRIGGER_KINDS = [
    {"value": libtiepie.TK_RISINGEDGE, "name": "Rising edge"},
    {"value": libtiepie.TK_FALLINGEDGE, "name": "Falling edge"},
    {"value": libtiepie.TK_ANYEDGE, "name": "Any edge"},
    {"value": libtiepie.TK_INWINDOW, "name": "In window"},
    {"value": libtiepie.TK_OUTWINDOW, "name": "Out window"},
    {"value": libtiepie.TK_ENTERWINDOW, "name": "Enter window"},
    {"value": libtiepie.TK_EXITWINDOW, "name": "Exit window"},
    {"value": libtiepie.TK_PULSEWIDTHPOSITIVE, "name": "Pulse width positive"},
    {"value": libtiepie.TK_PULSEWIDTHNEGATIVE, "name": "Pulse width negative"},
]

TRIGGER_LEVELS = [87.5, 75, 62.5, 50, 37.5, 25, 12.5]

TRIGGER_HYSTERESES = [10, 5, 2, 1]

TRIGGER_CONDITIONS = [
    {"value": libtiepie.TC_NONE, "name": "None"},
    {"value": libtiepie.TC_SMALLER, "name": "Smaller"},
    {"value": libtiepie.TC_LARGER, "name": "Larger"},
]

LINE_COLORS = ["00ff00", "00ffff", "0000ff", "ff0000"]

MENU_CHANNEL_RANGE_INDEX = 3


class OscilloscopeUI(QMainWindow):
    def __init__(self, scp, parent=None):
        super(OscilloscopeUI, self).__init__(parent)

        self._scp = scp

        if scp.has_trigger_hold_off:
            scp.trigger_holf_off_count = libtiepie.TH_ALLPRESAMPLES

        self._setup_menu()
        self._setup_toolbar()
        self._setup_events()

        glw = pyqtgraph.GraphicsLayoutWidget(self)
        for i in range(len(scp.channels)):
            glw.addPlot(i, 0)
        self.setCentralWidget(glw)

        self.setWindowTitle(scp.name + " s/n " + str(scp.serial_number))
        self.resize(800, 600)

    def _setup_menu(self):
        scp = self._scp

        # Timebase:
        menu = self.menuBar().addMenu("Timebase")

        self._menu_sample_frequency = menu.addMenu("Sample frequency")
        self._menu_sample_frequency_act_group = QActionGroup(self)

        self._menu_record_length = menu.addMenu("Record length")
        self._menu_record_length_act_group = QActionGroup(self)

        submenu = menu.addMenu("Pre sample ratio")
        act_group = QActionGroup(self)
        for value in PRE_SAMPLE_RATIOS:
            action = submenu.addAction("{:3.0f} %".format(value))
            action.setCheckable(True)
            action.setChecked(scp.pre_sample_ratio == value)
            action.setData(value * 0.01)
            action.toggled.connect(self._pre_sample_ratio_changed)
            act_group.addAction(action)

        # Channels:
        self._menu_channels = []
        for i in range(len(scp.channels)):
            ch = scp.channels[i]

            menu = self.menuBar().addMenu("Ch" + str(i + 1))

            action = menu.addAction("Enabled")
            action.setCheckable(True)
            action.setChecked(ch.enabled)
            action.setData(i)
            action.toggled.connect(self._channel_enabled_changed)

            submenu = menu.addMenu("Coupling")
            act_group = QActionGroup(self)
            for ck in COUPLINGS:
                if ch.couplings & ck["value"] != 0:
                    action = submenu.addAction(ck["name"])
                    action.setCheckable(True)
                    action.setChecked(ch.coupling == ck["value"])
                    action.setData({"ch": i, "ck": ck["value"]})
                    action.toggled.connect(self._channel_coupling_changed)
                    act_group.addAction(action)

            menu.addMenu("Range")
            act_group = QActionGroup(self)

            self._menu_channels.append({"menu": menu, "range_action_group": act_group})
            self._update_channel_range(i)

        # Trigger:
        self._menu_trigger = self.menuBar().addMenu("Trigger")

        submenu = self._menu_trigger.addMenu("Timeout")
        act_group = QActionGroup(self)
        for to in TRIGGER_TIMEOUTS:
            action = submenu.addAction(to["name"])
            action.setCheckable(True)
            action.setChecked(scp.trigger_time_out == to["value"])
            action.setData(to["value"])
            action.toggled.connect(self._trigger_timeout_changed)
            act_group.addAction(action)

        submenu = self._menu_trigger.addMenu("Source")
        act_group = QActionGroup(self)
        for i in range(len(scp.channels)):
            action = submenu.addAction("Ch" + str(i + 1))
            action.setCheckable(True)
            action.setChecked(scp.channels[i].trigger.enabled)
            action.setData({"ch": i})
            action.toggled.connect(self._trigger_source_changed)
            act_group.addAction(action)
            if action.isChecked():
                self._trigger_source = scp.channels[i].trigger
        for i in range(len(scp.trigger_inputs)):
            trin = scp.trigger_inputs[i]
            action = submenu.addAction(trin.name)
            action.setCheckable(True)
            action.setChecked(trin.enabled)
            action.setData({"trin": i})
            action.toggled.connect(self._trigger_source_changed)
            act_group.addAction(action)
            if action.isChecked():
                self._trigger_source = trin

        self._menu_trigger.addSeparator()

        self._menu_trigger_kind = self._menu_trigger.addMenu("Kind")
        self._menu_trigger_kind_act_group = QActionGroup(self)

        self._menu_trigger_levels = [self._menu_trigger.addMenu("Level")]
        self._menu_trigger_hystereses = [self._menu_trigger.addMenu("Hysteresis")]
        self._menu_trigger_levels.append(self._menu_trigger.addMenu("Level 2"))
        self._menu_trigger_hystereses.append(self._menu_trigger.addMenu("Hysteresis 2"))
        self._menu_trigger_condition = self._menu_trigger.addMenu("Condition")
        self._menu_trigger_times = [self._menu_trigger.addMenu("Time")]
        self._menu_trigger_times_act_group = [QActionGroup(self)]

        i = 0
        for submenu in self._menu_trigger_levels:
            act_group = QActionGroup(self)
            for value in TRIGGER_LEVELS:
                action = submenu.addAction("{:3.0f} %".format(value))
                action.setCheckable(True)
                action.setData({"index": i, "value": value * 0.01})
                action.toggled.connect(self._trigger_level_changed)
                act_group.addAction(action)
            i += 1

        i = 0
        for submenu in self._menu_trigger_hystereses:
            act_group = QActionGroup(self)
            for value in TRIGGER_HYSTERESES:
                action = submenu.addAction("{:3.0f} %".format(value))
                action.setCheckable(True)
                action.setData({"index": i, "value": value * 0.01})
                action.toggled.connect(self._trigger_hysteresis_changed)
                act_group.addAction(action)
            i += 1

        self._update_sample_frequency()
        self._update_record_length()
        self._update_trigger_source()

    def _setup_toolbar(self):
        self._toolbar = self.addToolBar("")

        self._toolbar_start = self._toolbar.addAction("Start")
        self._toolbar_start.triggered.connect(self._start)

        self._toolbar_oneshot = self._toolbar.addAction("One shot")
        self._toolbar_oneshot.triggered.connect(self._oneshot)

        self._toolbar_stop = self._toolbar.addAction("Stop")
        self._toolbar_stop.triggered.connect(self._stop)

    def _setup_events(self):

        self._fd_dataready = utils.eventfd()
        self._scp.set_event_data_ready(self._fd_dataready)
        self._notifier_dataready = QSocketNotifier(self._fd_dataready, QSocketNotifier.Read, self)
        self._notifier_dataready.activated.connect(self._event_dataready)

    def _sample_frequency_changed(self, checked):
        if checked:
            self._scp.sample_frequency = utils.unwrap_QVariant(self.sender().data())

            self._update_record_length()
            # TODO: self._update_trigger_time_out()
            self._update_trigger_times()

    def _record_length_changed(self, checked):
        if checked:
            self._scp.record_length = utils.unwrap_QVariant(self.sender().data())

    def _pre_sample_ratio_changed(self, checked):
        if checked:
            self._scp.pre_sample_ratio = utils.unwrap_QVariant(self.sender().data())

    def _channel_enabled_changed(self, checked):
        self._scp.channels[utils.unwrap_QVariant(self.sender().data())].enabled = checked
        self._update_sample_frequency()

    def _channel_coupling_changed(self, checked):
        if checked:
            data = utils.unwrap_QVariant(self.sender().data())
            self._scp.channels[data["ch"]].coupling = data["ck"]
            self._update_channel_range(data["ch"])

    def _channel_range_changed(self, checked):
        if checked:
            data = utils.unwrap_QVariant(self.sender().data())
            if data["range"] is None:
                self._scp.channels[data["ch"]].auto_ranging = True
            else:
                self._scp.channels[data["ch"]].range = data["range"]

    def _trigger_timeout_changed(self, checked):
        if checked:
            self._scp.trigger_time_out = utils.unwrap_QVariant(self.sender().data())

    def _trigger_source_changed(self, checked):
        data = utils.unwrap_QVariant(self.sender().data())
        if "ch" in data:
            tr = self._scp.channels[data["ch"]].trigger
        elif "trin" in data:
            tr = self._scp.trigger_inputs[data["trin"]]

        tr.enabled = checked

        if checked:
            self._trigger_source = tr
            self._update_trigger_source()

    def _trigger_kind_changed(self, checked):
        if checked:
            self._trigger_source.kind = utils.unwrap_QVariant(self.sender().data())
            self._update_trigger_levels_hystereses_condition_times()

    def _trigger_level_changed(self, checked):
        if checked:
            data = utils.unwrap_QVariant(self.sender().data())
            self._trigger_source.levels[data["index"]] = data["value"]

    def _trigger_hysteresis_changed(self, checked):
        if checked:
            data = utils.unwrap_QVariant(self.sender().data())
            self._trigger_source.hystereses[data["index"]] = data["value"]

    def _trigger_condition_changed(self, checked):
        if checked:
            self._trigger_source.condition = utils.unwrap_QVariant(self.sender().data())
            self._update_trigger_times()

    def _trigger_time_changed(self, checked):
        if checked:
            data = utils.unwrap_QVariant(self.sender().data())
            self._trigger_source.times[data["index"]] = data["value"]

    def _update_sample_frequency(self):
        sample_frequency = self._scp.sample_frequency
        menu = self._menu_sample_frequency
        menu.clear()
        for value in reversed(utils.sequence_125(SAMPLE_FREQUENCY_MIN, self._scp.verify_sample_frequency(1e100))):
            action = menu.addAction(utils.val_to_str(value, 3, 0) + "Hz")
            action.setCheckable(True)
            action.setChecked(sample_frequency == value)
            action.setData(value)
            action.toggled.connect(self._sample_frequency_changed)
            self._menu_sample_frequency_act_group.addAction(action)

    def _update_record_length(self):
        record_length = self._scp.record_length
        menu = self._menu_record_length
        menu.clear()
        for value in reversed(utils.sequence_125(self._scp.verify_record_length(RECORD_LENGTH_MIN), self._scp.verify_record_length(RECORD_LENGTH_MAX))):
            action = menu.addAction(utils.val_to_str(value, 3, 0) + "Samples")
            action.setCheckable(True)
            action.setChecked(record_length == value)
            action.setData(int(value))
            action.toggled.connect(self._record_length_changed)
            self._menu_record_length_act_group.addAction(action)

    def _update_channel_range(self, index):
        ch = self._scp.channels[index]
        menu_ch = self._menu_channels[index]
        items = menu_ch["menu"].children()
        if len(items) > MENU_CHANNEL_RANGE_INDEX:
            menu = items[MENU_CHANNEL_RANGE_INDEX]

            menu.clear()

            action = menu.addAction("Auto")
            action.setCheckable(True)
            action.setChecked(ch.auto_ranging)
            action.setData({"ch": index, "range": None})
            action.toggled.connect(self._channel_range_changed)
            menu_ch["range_action_group"].addAction(action)

            ck = self._scp.channels[index].coupling
            if ck & libtiepie.CKM_V != 0:
                unit = "V"
            elif ck & libtiepie.CKM_A != 0:
                unit = "A"
            elif ck & libtiepie.CKM_OHM != 0:
                unit = "Ohm"

            for value in reversed(self._scp.channels[index].ranges):
                action = menu.addAction(utils.val_to_str(value, 3, 0) + unit)
                action.setCheckable(True)
                action.setChecked(not ch.auto_ranging and ch.range == value)
                action.setData({"ch": index, "range": value})
                action.toggled.connect(self._channel_range_changed)
                menu_ch["range_action_group"].addAction(action)

    def _update_trigger_source(self):
        self._update_trigger_kind()
        self._update_trigger_levels_hystereses_condition_times()

    def _update_trigger_kind(self):
        tr = self._trigger_source
        self._menu_trigger_kind.menuAction().setVisible(tr.kinds != libtiepie.TKM_NONE)
        if self._menu_trigger_kind.menuAction().isVisible():
            self._menu_trigger_kind.clear()
            for tk in TRIGGER_KINDS:
                if tr.kinds & tk["value"] != 0:
                    action = self._menu_trigger_kind.addAction(tk["name"])
                    action.setCheckable(True)
                    action.setChecked(tr.kind == tk["value"])
                    action.setData(tk["value"])
                    action.toggled.connect(self._trigger_kind_changed)
                    self._menu_trigger_kind_act_group.addAction(action)

    def _update_trigger_levels_hystereses_condition_times(self):
        tr = self._trigger_source
        level_count = len(tr.levels) if hasattr(tr, 'levels') else 0
        for i in range(len(self._menu_trigger_levels)):
            menu = self._menu_trigger_levels[i]
            menu.menuAction().setVisible(level_count > i)
            if menu.menuAction().isVisible():
                value = tr.levels[i]
                for action in menu.actions():
                    action.setChecked(utils.unwrap_QVariant(action.data())["value"] == value)

        hysteresis_count = len(tr.hystereses) if hasattr(tr, 'hystereses') else 0
        for i in range(len(self._menu_trigger_hystereses)):
            menu = self._menu_trigger_hystereses[i]
            menu.menuAction().setVisible(hysteresis_count > i)
            if menu.menuAction().isVisible():
                value = tr.hystereses[i]
                for action in menu.actions():
                    action.setChecked(utils.unwrap_QVariant(action.data())["value"] == value)

        self._menu_trigger_condition.menuAction().setVisible(hasattr(tr, 'conditions') and tr.conditions != libtiepie.TCM_NONE)
        if self._menu_trigger_condition.menuAction().isVisible():
            self._menu_trigger_condition.clear()
            for tc in TRIGGER_CONDITIONS:
                if tr.conditions & tc["value"] != 0:
                    action = self._menu_trigger_condition.addAction(tc["name"])
                    action.setCheckable(True)
                    action.setChecked(tr.condition == tc["value"])
                    action.setData(tc["value"])
                    action.toggled.connect(self._trigger_condition_changed)
                    self._menu_trigger_kind_act_group.addAction(action)

        self._update_trigger_times()

    def _update_trigger_times(self):
        tr = self._trigger_source
        time_count = len(tr.times) if hasattr(tr, 'times') else 0
        for i in range(len(self._menu_trigger_times)):
            menu = self._menu_trigger_times[i]
            menu.menuAction().setVisible(time_count > i)
            if menu.menuAction().isVisible():
                menu.clear()
                for value in utils.sequence_125(tr.times.verify(i, 1e-100), 1):
                    action = menu.addAction(utils.val_to_str(value, 3, 0) + "s")
                    action.setCheckable(True)
                    action.setChecked(tr.times[i] == value)
                    action.setData({"index": i, "value": value})
                    action.toggled.connect(self._trigger_time_changed)
                    self._menu_trigger_times_act_group[i].addAction(action)

    def _start(self, checked):
        self._continuous = True
        self._scp.start()

    def _oneshot(self, checked):
        self._continuous = False
        self._scp.start()

    def _stop(self, checked):
        self._continuous = False
        try:
            self._scp.stop()
        except libtiepie.exceptions.UnsuccessfulError:
            pass

    def _event_dataready(self, fd):
        utils.eventfd_clear(fd)

        scp = self._scp
        channel_count = len(scp.channels)

        start = 0
        length = scp._record_length - start

        # Get data
        pointers = libtiepie.api.HlpPointerArrayNew(channel_count)
        data = [None for i in range(channel_count)]

        try:
            for i in range(channel_count):
                if scp._active_channels[i]:
                    data[i] = np.empty(length, dtype=np.float32)
                    libtiepie.api.HlpPointerArraySet(pointers, i, data[i].ctypes.data)

            libtiepie.api.ScpGetData(scp._handle, pointers, channel_count, start, length)
        finally:
            libtiepie.api.HlpPointerArrayDelete(pointers)

        # Plot data
        glw = self.centralWidget()

        i = 0
        for chnum, chdata in zip(range(len(self._scp.channels)), data):
            if chdata is not None:
                plot = glw.getItem(i, 0)
                if plot:
                    plot.clear()
                else:
                    plot = glw.addPlot(i, 0)
                ch = self._scp.channels[chnum]
                plot.plot(y=chdata, pen=LINE_COLORS[chnum % len(LINE_COLORS)])
                plot.setYRange(ch.data_value_min, ch.data_value_max)
                i += 1

        # Remove unused plots:
        plot = glw.getItem(i, 0)
        while plot is not None:
            glw.removeItem(plot)
            plot = glw.getItem(i, 0)

        if self._continuous:
            self._scp.start()


if __name__ == '__main__':
    import sys

    libtiepie.device_list.update()

    try:
        dev = utils.try_open_device(sys.argv, libtiepie.DEVICETYPE_OSCILLOSCOPE)

        app = QApplication(sys.argv)

        frm = OscilloscopeUI(dev)
        frm.show()

        sys.exit(app.exec_())
    except Exception, e:
        print(e.message, file=sys.stderr)
        sys.exit(1)
