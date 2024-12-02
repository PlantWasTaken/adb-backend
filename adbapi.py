import os
import subprocess
from PIL import Image
import pytesseract
import re

class Device:
    def __init__(self, port, _devices, emulator, _name) -> None:
        current_dir = os.getcwd()
        adb_path = self.find_executable('adb.exe', current_dir)
        if not adb_path:
            raise FileNotFoundError("adb.exe not found in the current directory or subdirectories.")
        
        self.name = _name #only used if emulator = 1
        self.emulator = emulator #using emulator 1 - yes, 0 - no
        self.adb = adb_path
        self.port = port  # Port of emulator to run code on, default #5554
        self.devices = _devices  # Number of devices, default 1, only tested for 3..., 0 - checks for devices

        subprocess.call(['taskkill', '/F', '/IM', 'adb.exe'])
        if(self.emulator == 1): #else establish connection to phonep
            self.connect_emulators()

        if(self.emulator == 0):
            subprocess.run(f'"{self.adb}" devices', shell=True)
            subprocess.run(f'"{self.adb}" -s {self.name} shell wm size', check=True)
        
        subprocess.run(f'"{self.adb}" start-server', shell=True)

    def find_executable(self, filename, search_path):
        """Search for an executable file in the given directory and subdirectories."""
        for root, dirs, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def screenshot(self) -> Image:
        screenshot_path = os.path.join(os.getcwd(), f'emu-{self.port}.png')
        screenshot_path_phone = os.path.join(os.getcwd(), f'phn-{self.name}.png')
        print(screenshot_path_phone)
        temp_screenshot_path = '/data/local/tmp/image.png'

        if(self.emulator == 1):
            subprocess.call(f'"{self.adb}" -s emulator-{self.port} shell screencap -p {temp_screenshot_path}', shell=True)
            subprocess.run(f'"{self.adb}" -s emulator-{self.port} pull {temp_screenshot_path} "{screenshot_path}"', shell=True)
            screenshot = Image.open(screenshot_path)

        if(self.emulator == 0):
            subprocess.call(f'"{self.adb}" -s {self.name} shell screencap -p {temp_screenshot_path}', shell=True)
            subprocess.run(f'"{self.adb}" -s {self.name} pull {temp_screenshot_path} "{screenshot_path_phone}"', shell=True)
            
            screenshot = Image.open(screenshot_path_phone)

        return screenshot

    def screenInput(self, x, y) -> None:
        # Sending a touch input command to the emulator
        
        if(self.emulator == 1):
            print(f'Input emulator-{self.port} at: {x}, {y}')
            subprocess.Popen(f'"{self.adb}" -s emulator-{self.port} shell input tap {x} {y}', shell=True)
        if(self.emulator == 0):
            print(f'Input {self.name} at: {x}, {y}')
            subprocess.Popen(f'"{self.adb}" -s {self.name} shell input tap {x} {y}', shell=True)

    def screenSwipe(self,x1,y1,x2,y2) -> None:
        print(f'Swiping from: {x1}, {y1} -> {x2}, {y2}')
        if(self.emulator == 1):
            subprocess.Popen(f'"{self.adb}" -s emulator-{self.port} shell input touchscreen swipe {x1} {y1} {x2} {y2}', shell=True)
        if(self.emulator == 0):
            subprocess.Popen(f'"{self.adb}" -s {self.name} shell input touchscreen swipe {x1} {y1} {x2} {y2}', shell=True)

    @staticmethod
    def generate_ports(self) -> list: #emulator
        if self.devices == 0:
            print(f'Finding devices..')
            devices_output = subprocess.run(f'"{self.adb}" devices', shell=True, capture_output=True, text=True)
            emulator_ports = re.findall(r'emulator-(\d+)', devices_output.stdout)
            ports = [int(port) for port in emulator_ports]

            if(len(ports) == 0):
                print(f'No adb device detected')
                raise SystemError
            else:
                self.devices = len(ports)
                print(f'Found {len(ports)} devices')
                print(f'Ports: {ports}')

        if self.devices == -1: #if you know the device id
            return [self.port]
        
        if self.devices == 1:
            return [5554]  # Default port
        if self.devices == 2:
            return [5554, 5558]
        if self.devices > 2:
            return [(5554 + 2 * i) for i in range(self.devices)]

    def connect_emulators(self) -> None:
        # Connects to all emulators using the generated ports
        _ports = Device.generate_ports(self)
        print(f'Ports: {_ports}')
        for port in _ports:
            subprocess.run(f'"{self.adb}" connect 127.0.0.1:{port}', check=True)
            subprocess.run(f'"{self.adb}" -s emulator-{port} shell wm size', check=True)

class ImageOcr:
    def __init__(self,im) -> None:
        # Search for tesseract.exe in the current directory or subdirectories
        current_dir = os.getcwd()
        tesseract_path = self.find_executable('tesseract.exe', current_dir)
        if not tesseract_path:
            raise FileNotFoundError("tesseract.exe not found in the current directory or subdirectories.")
        
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.im = im 

    def find_executable(self, filename, search_path):
        for root, dirs, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def get_text(self) -> str:
        # Extracting text from the image using pytesseract
        text = pytesseract.image_to_string(self.im).split()
        print(text)
        return text

# Example usage:
# a = Device(0, 2)
# im1 = a.screenshot()

# my_text = ImageOcr(im1)
# print(my_text.get_text())

# a.screenInput(100, 200)
