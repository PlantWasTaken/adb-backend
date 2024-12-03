import os
import subprocess
from PIL import Image
import re

class BaseDevice:
    def __init__(self, adb_path=None):
        current_dir = os.getcwd()
        self.adb = adb_path or self.find_executable('adb.exe', current_dir)
        if not self.adb:
            raise FileNotFoundError("adb.exe not found in the current directory or subdirectories.")
        
        subprocess.call(['taskkill', '/F', '/IM', 'adb.exe'])
        subprocess.run(f'"{self.adb}" start-server', shell=True)

    def find_executable(self, filename, search_path):
        """Search for an executable file in the given directory and subdirectories."""
        for root, dirs, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def screenshot(self, device_identifier):
        screenshot_path = os.path.join(os.getcwd(), f'{device_identifier}.png')
        temp_screenshot_path = '/data/local/tmp/image.png'
        
        subprocess.call(f'"{self.adb}" -s {device_identifier} shell screencap -p {temp_screenshot_path}', shell=True)
        subprocess.run(f'"{self.adb}" -s {device_identifier} pull {temp_screenshot_path} "{screenshot_path}"', shell=True)
        
        return Image.open(screenshot_path)

    def screenInput(self, device_identifier, x, y):
        print(f'Input {device_identifier} at: {x}, {y}')
        subprocess.Popen(f'"{self.adb}" -s {device_identifier} shell input tap {x} {y}', shell=True)

    def screenSwipe(self, device_identifier, x1, y1, x2, y2):
        print(f'Swiping from: {x1}, {y1} -> {x2}, {y2}')
        subprocess.Popen(f'"{self.adb}" -s {device_identifier} shell input touchscreen swipe {x1} {y1} {x2} {y2}', shell=True)


class Phone(BaseDevice):
    def __init__(self, name, adb_path=None):
        super().__init__(adb_path)
        self.name = name
        
        subprocess.run(f'"{self.adb}" devices', shell=True)
        subprocess.run(f'"{self.adb}" -s {self.name} shell wm size', check=True)

    def screenshot(self):
        return super().screenshot(self.name)

    def screenInput(self, x, y):
        super().screenInput(self.name, x, y)

    def screenSwipe(self, x1, y1, x2, y2):
        super().screenSwipe(self.name, x1, y1, x2, y2)


class Device(BaseDevice):
    def __init__(self, port, devices, emulator,name=None, adb_path=None):
        super().__init__(adb_path)
        self.port = port
        self.devices = devices
        self.emulator = emulator
        self.name = name


        if self.emulator:
            self.connect_emulators()
        else:
            subprocess.run(f'"{self.adb}" devices', shell=True)
            if self.name:
                subprocess.run(f'"{self.adb}" -s {self.name} shell wm size', check=True)


    def generate_ports(self):
        if self.devices == 0:
            print(f'Finding devices..')
            devices_output = subprocess.run(f'"{self.adb}" devices', shell=True, capture_output=True, text=True)
            emulator_ports = re.findall(r'emulator-(\d+)', devices_output.stdout)
            ports = [int(port) for port in emulator_ports]

            if not ports:
                print(f'No adb device detected')
                raise SystemError
            else:
                self.devices = len(ports)
                print(f'Found {len(ports)} devices')
                print(f'Ports: {ports}')

        if self.devices == -1:
            return [self.port]

        return [(5554 + 2 * i) for i in range(self.devices)]

    def connect_emulators(self):
        ports = self.generate_ports()
        print(f'Ports: {ports}')
        for port in ports:
            subprocess.run(f'"{self.adb}" connect 127.0.0.1:{port}', check=True)
            subprocess.run(f'"{self.adb}" -s emulator-{port} shell wm size', check=True)

    def screenshot(self):
        identifier = f"emulator-{self.port}" if self.emulator else self.name
        return super().screenshot(identifier)

    def screenInput(self, x, y):
        identifier = f"emulator-{self.port}" if self.emulator else self.name
        super().screenInput(identifier, x, y)

    def screenSwipe(self, x1, y1, x2, y2):
        identifier = f"emulator-{self.port}" if self.emulator else self.name
        super().screenSwipe(identifier, x1, y1, x2, y2)
