BOARD = esp32:esp32:lolin_s2_mini
SKETCH = $(notdir $(CURDIR))
DEVICE_PATTERN = /dev/tty.usbmodemHID*

# Find device file matching the pattern /dev/cu.usbserial-*
DEVICE := $(shell ls $(DEVICE_PATTERN) 2>/dev/null | head -n 1)

ifeq ($(strip $(DEVICE)),)
	DEVICE_PATTERN := /dev/ttyACM1
endif

DEVICE := $(shell ls $(DEVICE_PATTERN) 2>/dev/null | head -n 1)

ifeq ($(strip $(DEVICE)),)
        DEVICE := /dev/ttyACM0
endif


compile:
	arduino-cli --verbose compile --fqbn $(BOARD) ../$(SKETCH)

upload:
	arduino-cli --verbose upload -p $(DEVICE) --fqbn $(BOARD) ../$(SKETCH)

terminal:
	screen $(DEVICE) 115200
