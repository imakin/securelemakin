BOARD = esp32:esp32:lolin_s2_mini
SKETCH = $(notdir $(CURDIR))
DEVICE_PATTERN = /dev/cu.usbmodem*

# Find device file matching the pattern /dev/cu.usb*
DEVICE := $(shell ls $(DEVICE_PATTERN) 2>/dev/null | head -n 1)

ifeq ($(strip $(DEVICE)),)
	DEVICE := /dev/ttyACM0
endif


compile:
	arduino-cli --verbose compile --fqbn $(BOARD) ../$(SKETCH)

upload:
	arduino-cli upload -p $(DEVICE) --fqbn $(BOARD) ../$(SKETCH)

terminal:
	nodemcu-uploader --port $(DEVICE) terminal
