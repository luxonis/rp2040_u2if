# luxonis-u2if

Python package for controlling Luxonis u2if based devices and library for low level commnucation.

## Install

```bash
pip install .
```

## Usage

```python
from luxonis_u2if import RP2040_u2if

rp = RP2040_u2if()
rp.open()  # use default VID/PID
rp.gpio_init_pin(0, rp.GPIO_OUT, rp.GPIO_PULL_NONE)
rp.gpio_set_pin(0, 1)
rp.close()

```python
from luxonis_u2if import RP2040_u2if

box = ControllerBox()
box.relay_init()
box.relay_set(1)
box.close()
```

