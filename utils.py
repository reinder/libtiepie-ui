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

import os
import math
from ctypes import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import libtiepie

PRODUCT_IDS = {
    "Combi": libtiepie.PID_COMBI,
    "HP3": libtiepie.PID_HP3,
    "HS4": libtiepie.PID_HS4,
    "HS4D": libtiepie.PID_HS4D,
    "HS5": libtiepie.PID_HS5,
}

libc = cdll.LoadLibrary("libc.so.6")


def eventfd(init_val=0, flags=0):
    return libc.eventfd(init_val, flags)


def eventfd_clear(fd):
    os.read(fd, 8)


def try_open_device(argv, device_type):
    dev = None

    if len(argv) > 1:
        serial = 0
        try:
            serial = int(argv[1])
        except:
            pid = str_to_pid(argv[1])

        if serial > 0:
            dev = libtiepie.device_list.get_item_by_serial_number(serial).open_device(device_type)
        else:
            dev = libtiepie.device_list.get_item_by_product_id(pid).open_device(device_type)
    else:
        for item in libtiepie.device_list:
            try:
                dev = item.open_device(device_type)
                break
            except:
                pass

    if dev:
        return dev
    else:
        raise Exception("No devices found")


def create_ui(item, parent=None):

    scp = item.open_oscilloscope() if (item.types & libtiepie.DEVICETYPE_OSCILLOSCOPE) != 0 else None
    if scp:
        from oscilloscopeui import OscilloscopeUI
        scpui = OscilloscopeUI(scp, parent)
        scpui.show()

    gen = item.open_generator() if (item.types & libtiepie.DEVICETYPE_GENERATOR) != 0 else None
    if gen:
        from generatorui import GeneratorUI
        genui = GeneratorUI(gen, parent)
        genui.show()


def val_to_str(value, digits=6, decimals=3):
    value_abs = float(abs(value))
    prefix = ''

    if value_abs >= 1e9:
        value /= 1e9
        prefix = 'G'
    elif value_abs >= 1e6:
        value /= 1e6
        prefix = 'M'
    elif value_abs >= 1e3:
        value /= 1e3
        prefix = 'k'
    elif value_abs < 1e-9:
        pass  # almost zero, no prefix
    elif value_abs < 1e-6:
        value *= 1e9
        prefix = 'n'
    elif value_abs < 1e-3:
        value *= 1e6
        prefix = 'u'
    elif value_abs < 1e0:
        value *= 1e3
        prefix = 'm'

    s = "{:" + str(digits - decimals) + "." + str(decimals) + "f} {:s}"
    return s.format(value, prefix)


def ceil_125(value):
    factor = 10 ** math.floor(math.log10(value))
    value /= factor

    if value <= 1:
        value = 1
    elif value <= 2:
        value = 2
    elif value <= 5:
        value = 5
    else:
        value = 10

    return value * factor


def sequence_125(min, max):
    values = []
    value = ceil_125(min)

    while value <= max:
        values.append(value)
        value = ceil_125(value * 2)

    return values


def str_to_pid(value):
    if value in PRODUCT_IDS:
        return PRODUCT_IDS[value]
    else:
        raise Exception("Invalid product ID: " + value)


def unwrap_QVariant(value):
    if(value.type() == QMetaType.Int):
        return value.toInt()[0]
    elif(value.type() == QMetaType.Double):
        return value.toDouble()[0]
    elif(value.type() == QMetaType.QVariantMap):
        return dict((str(k), v) for k, v in value.toPyObject().iteritems())
    elif(value.typeName() == "PyQt_PyObject"):
        return value.toPyObject()
    else:
        raise Exception("Can't unwrap QVariant: " + value.typeName())
