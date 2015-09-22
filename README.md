# libtiepie-ui

Simple GUI for [TiePie engineering](http://www.tiepie.com) oscilloscopes and generators.

libtiepie-ui is a simple Python application using the Qt4 framework for
controlling TiePie engineering oscilloscopes and
function generators.

The oscilloscope GUI support basic measurering and one active trigger source.

The generator GUI can control all supported signal types except arbitrary and it
can only operate in continuous mode.

## Dependencies

- PyQt4
- pyqtgraph
- numpy
- libtiepie and its Python bindings, see http://www.tiepie.com/libtiepie

## Usage

Use both GUI's:
- `./libtiepieui.py`

Use only the oscilloscope GUI:
- `./oscilloscopeui.py` - open first discovered oscilloscope.
- `./oscilloscopeui.py <pid>` - open oscilloscope by product id, valid values: `HP3`, `HS4`, `HS4D`, `HS5` or `Combi`.
- `./oscilloscopeui.py <sn>` - open oscilloscope by serial number, e.g. `27917`

Use only the generator GUI:
- `./generatorui.py` - open first discovered generator.
- `./generatorui.py <pid>` - open generator by product id, valid values: `HS5`.
- `./generatorui.py <sn>` - open generator by serial number, e.g. `22110`
