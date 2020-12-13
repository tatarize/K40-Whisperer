from nano_library import K40_CLASS as K40_LIBUSB
from ctypes import *

# Code donated to public domain.


class K40_CLASS(K40_LIBUSB):
    def initialize_device(self, USB_Location=-1, verbose=False):
        try:
            self.dev = WindllDevice(USB_Location)
        except:
            raise Exception("Could not load CH341 Windll")
        self.USB_Location = self.dev.driver_index
        return self.USB_Location

    def release_usb(self):  # Override to avoid usb.util command.
        self.dev.close()
        self.dev = None
        self.USB_Location = None


class WindllDevice:
    def __init__(self, index=-1):
        try:
            self.driver = windll.LoadLibrary("CH341DLL.dll")
        except (NameError, OSError):
            raise ConnectionRefusedError
        self.driver_index = index
        if self.driver_index == -1:  # -1 means any device.
            for i in range(16):  # Try up to 16 devices.
                self.driver_value = self.driver.CH341OpenDevice(i)
                if self.driver_value != -1:
                    self.driver_index = i  # device found.
                    break
        else:
            self.driver_value = self.driver.CH341OpenDevice(index)  # Specific device.
        if self.driver_value == -1:  # No device was found.
            raise ConnectionRefusedError
        self.driver.CH341InitParallel(self.driver_index, 1)  # Control Transfer 0x40, 177, 0x8800, 0, 0

    def close(self):
        self.driver_value = -1  # Close
        self.driver.CH341CloseDevice(self.driver_index)

    reset = close  # Driver manages resources. Just close it on reset.

    def read(self, address, length, timeout):
        if self.driver_value == -1:  # Driver was never correctly initialized.
            raise ConnectionRefusedError
        obuf = (c_byte * 6)()
        self.driver.CH341GetStatus(self.driver_index, obuf)  # Does Write 160 and Read.
        return [int(q & 0xff) for q in obuf]

    def write(self, address, line, timeout):
        if self.driver_index == -1:  # Driver was not correctly initialized.
            raise ConnectionError
        if len(line) == 1:
            return  # Just the 160 Hello. This will cover in read.
        line = line[1:]  # Removing A0 = EppWrite.
        length = len(line)
        obuf = (c_byte * length)()
        for i in range(length):
            obuf[i] = line[i]
        length = (c_byte * 1)()
        length[0] = 32
        self.driver.CH341EppWriteData(self.driver_index, obuf, length)
