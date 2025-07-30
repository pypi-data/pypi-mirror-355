# Binance trading gateway for VeighNa

<p align="center">
  <img src ="https://github.com/veighna-global/vnpy_evo/blob/dev/logo.png" width="300" height="300"/>
</p>

<p align="center">
    <img src ="https://img.shields.io/badge/version-2025.06.17-blueviolet.svg"/>
    <img src ="https://img.shields.io/badge/platform-windows|linux|macos-yellow.svg"/>
    <img src ="https://img.shields.io/badge/python-3.10|3.11|3.12-blue.svg"/>
    <img src ="https://img.shields.io/github/license/veighna-global/vnpy_binance.svg?color=orange"/>
</p>


## Introduction

This gateway is developed based on Binance's REST and Websocket API, and supports spot, linear contract and inverse contract trading.

**For derivatives contract trading, please notice:**

1. Only supports cross margin mode.
2. Only supports one-way position mode.

## Install

Users can easily install ``vnpy_binance`` by pip according to the following command.

```
pip install vnpy_binance
```

Also, users can install ``vnpy_binance`` using the source code. Clone the repository and install as follows:

```
git clone https://github.com/veighna-global/vnpy_binance.git && cd vnpy_binance

python setup.py install
```

## A Simple Example

Save this as run.py.

```
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_binance import (
    BinanceLinearGateway,
)


def main() -> None:
    """main entry"""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(BinanceLinearGateway)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
```
