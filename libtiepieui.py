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


if __name__ == '__main__':
    import sys

    try:
        libtiepie.device_list.update()

        dev_count = len(libtiepie.device_list)

        if dev_count == 0:
            raise Exception("No devices found")
        elif dev_count == 1:
            item = libtiepie.device_list[0]

            app = QApplication(sys.argv)

            scp = item.open_oscilloscope() if (item.types & libtiepie.DEVICETYPE_OSCILLOSCOPE) != 0 else None
            if scp:
                from oscilloscopeui import OscilloscopeUI
                scpui = OscilloscopeUI(scp)
                scpui.show()

            gen = item.open_generator() if (item.types & libtiepie.DEVICETYPE_GENERATOR) != 0 else None
            if gen:
                from generatorui import GeneratorUI
                genui = GeneratorUI(gen)
                genui.show()

            sys.exit(app.exec_())
        else:
            raise Exception("TODO: show dialog to choose instrument.")
    except Exception, e:
        print(e.message, file=sys.stderr)
        sys.exit(1)
