import os
import subprocess
from PIL import Image
import re
import pytesseract

def find_all_elements_with_text(target_list, text):
    """
    Returns a list of all elements in the target_list that contain the specified text.
    """
    return [item for item in target_list if text in item]

class BaseDevice:
    def __init__(self, adb_path=None) -> None:
        self.BASE_RESOLUTION_EMU = [1920,1080] #scale 16:9 aspect ratio
        self.BASE_RESOLUTION_PHN = [2400,1080] #scale, device samsung galaxy s21, 9:20 aspect ratio
        self.LANDSCAPE = True #default True

        self.res_scalar_x = 1 #default 1
        self.res_scalar_y = 1 #default 1
        
        current_dir = os.getcwd()
        self.adb = adb_path or self.find_executable('adb.exe', current_dir)
        if not self.adb:
            raise FileNotFoundError("adb.exe not found in the current directory or subdirectories.")
        
        subprocess.call(['taskkill', '/F', '/IM', 'adb.exe'])
        server = subprocess.run(f'"{self.adb}" start-server', shell=True,capture_output=True,text=True)
        self.check_connection(server)
        print(server.stderr)

        #resolution scalar
        subprocess.run(f'"{self.adb}" devices', shell=True)

    def check_connection(self,CompletedProcess):
        if(CompletedProcess.returncode == 0): #good connection
            return True
        else:                                  #bad connection
            raise ConnectionError
        
    def get_info(self, device_identifier) -> None:
        print(f'\nInfo for device: {device_identifier}')
        #subprocess.run(f'"{self.adb}" -s {device_identifier} shell dumpsys battery', shell=True)
        subprocess.run(f'"{self.adb}" -s {device_identifier} shell wm size', check=True, shell=True)
        print(f'{device_identifier} Landscape: {self.LANDSCAPE}')
        print(f'{device_identifier} Resolution scalar X: {self.res_scalar_x}')
        print(f'{device_identifier} Resolution scalar Y: {self.res_scalar_y}')
        subprocess.run(f'"{self.adb}" -s {device_identifier} get-serialno', shell=True)

    def find_executable(self, filename, search_path) -> None:
        """Search for an executable file in the given directory and subdirectories."""
        for root, dirs, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def screenshot(self, device_identifier) -> Image:
        screenshot_path = os.path.join(os.getcwd(), f'{device_identifier}.png')
        temp_screenshot_path = '/data/local/tmp/image.png'
        
        take_screenshot = subprocess.run(f'"{self.adb}" -s {device_identifier} shell screencap -p {temp_screenshot_path}', shell=True, text=True)
        fetch_screenshot = subprocess.run(f'"{self.adb}" -s {device_identifier} pull {temp_screenshot_path} "{screenshot_path}"', shell=True, text=True)
        
        self.check_connection(take_screenshot)
        self.check_connection(fetch_screenshot)

        return Image.open(screenshot_path)

    def resolution(self, device_identifier) -> list:
        #orientation = subprocess.run(f'"{self.adb}" -s {device_identifier} shell dumpsys input',shell=True, text=True,capture_output=True)
        #dump_info = orientation.stdout.splitlines()
        #_orientation = find_all_elements_with_text(dump_info,text='Orientation:') #search dump for Transoform (ROT)

        res = subprocess.run(f'"{self.adb}" -s {device_identifier} shell wm size', shell=True, text=True, capture_output=True)
        self.check_connection(res) 
        #self.check_connection(orientation) #uncomment

        res = res.stdout.split()[-1] #formattex in mxn, type=str
        res_list = res.replace('x', ' ').split()
        res_list_int = list(map(int, res_list))
        res_list_int.sort(reverse=True) #sort x,y

        return res_list_int #in the format, x is biggest, y smallest

    def screenInput(self, device_identifier, x, y) -> None:
        print(f'Input {device_identifier} at: {x}, {y}')
        subprocess.Popen(f'"{self.adb}" -s {device_identifier} shell input tap {x} {y}', shell=True, text=True)

    def screenSwipe(self, device_identifier, x1, y1, x2, y2) -> None:
        print(f'Swiping from: {x1}, {y1} -> {x2}, {y2}')
        subprocess.Popen(f'"{self.adb}" -s {device_identifier} shell input touchscreen swipe {x1} {y1} {x2} {y2}', shell=True)


class Phone(BaseDevice):
    def __init__(self, name, force_pc_resolution=True, vertical=True,adb_path=None) -> None:
        super().__init__(adb_path)
        self.name = name #device name
        
        subprocess.run(f'"{self.adb}" devices', shell=True)
        if(self.name == None): #unknown device name
            self.name = self.find_device()

            for i in self.name: #if multiple devices
                print(f'Found device with name: {i}')
            
            self.name = self.name[0] #unit 0, is the default unit
            print(f'Connecting to default unit: {self.name}')
            print(f'Recomended to change device name to: {self.name}\nTo avoid errors.')

        phone_resolution = self.resolution() #[x,y]
        if force_pc_resolution: #forces scaling to landscape 1920x1080, default
            self.LANDSCAPE = True
            self.res_scalar_x = phone_resolution[0]/self.BASE_RESOLUTION_EMU[0]
            self.res_scalar_y = phone_resolution[1]/self.BASE_RESOLUTION_EMU[1]

        if not force_pc_resolution: #phone to phone scaling
            self.LANDSCAPE = False
            self.res_scalar_x = phone_resolution[1]/self.BASE_RESOLUTION_PHN[0]
            self.res_scalar_y = phone_resolution[0]/self.BASE_RESOLUTION_PHN[1]
        
        self.get_info() #post info about system
        #subprocess.run(f'"{self.adb}" -s {self.name} shell wm size', check=True)

    def find_device(self) -> str: 
        print(f'Finding device..')
        devices_output = subprocess.run(f'"{self.adb}" devices', shell=True, capture_output=True, text=True)
        super().check_connection(devices_output)

        phones = devices_output.stdout.split() #list
        phones = phones[4:] #formatting
        device_name = [i for i in phones if i != 'device']
        phone_name = [name for name in device_name if 'emulator' not in name]

        if(phone_name == []): #no phone
            raise ConnectionError
        
        return phone_name

    def get_info(self) -> None:
        super().get_info(self.name)
    
    def screenshot(self) -> Image:
        return super().screenshot(self.name)

    def screenInput(self, x, y) -> None: #scaled
        x_scaled = x*self.res_scalar_x #scaling values for normalization
        y_scaled = y*self.res_scalar_y

        super().screenInput(self.name, x_scaled, y_scaled)


    def screenSwipe(self, x1, y1, x2, y2) -> None:
        x1_scaled = x1*self.res_scalar_x #scaling values for normalization
        y1_scaled = y1*self.res_scalar_y
        x2_scaled = x2*self.res_scalar_x 
        y2_scaled = y2*self.res_scalar_y

        super().screenSwipe(self.name, x1_scaled, y1_scaled, x2_scaled, y2_scaled)


    def resolution(self) -> list:
        res = super().resolution(self.name)
        return res

class Emulator(BaseDevice):
    def __init__(self, port, devices, emulator=True,name=None, adb_path=None) -> None:
        super().__init__(adb_path)
        self.port = port
        self.devices = devices
        self.emulator = emulator
        self.name = name

        if self.emulator:
            self.connect_emulators()
        else:
            raise SystemError

        emulator_resolution = self.resolution() #[x,y]
        self.res_scalar_x = emulator_resolution[0]/self.BASE_RESOLUTION_EMU[0]
        self.res_scalar_y = emulator_resolution[1]/self.BASE_RESOLUTION_EMU[1]

        self.get_info() #post info about system

    def generate_ports(self) -> list:
        if self.devices == 0:
            print(f'Finding devices..')
            devices_output = subprocess.run(f'"{self.adb}" devices', shell=True, capture_output=True, text=True)
            super().check_connection(devices_output)

            emulator_ports = re.findall(r'emulator-(\d+)', devices_output.stdout)
            ports = [int(port) for port in emulator_ports]

            if not ports:
                print(f'No adb device detected')
                raise SystemError
            else:
                self.devices = len(ports)
                print(f'Found {len(ports)} devices')
                print(f'Ports: {ports}')

        if self.devices == -1: #manual port
            return [self.port]

        if self.devices == 1: #default port
            return [5554]
        
        if self.devices == 2:
            return[5554,5558]
        
        if self.devices > 2:
            return [(5554 + 2 * i) for i in range(self.devices)]

    def connect_emulators(self) -> None:
        ports = self.generate_ports()
        print(f'Ports: {ports}')
        for port in ports:
            subprocess.run(f'"{self.adb}" connect 127.0.0.1:{port}', check=True)
            subprocess.run(f'"{self.adb}" -s emulator-{port} shell wm size', check=True)

    def get_info(self):
        identifier = f"emulator-{self.port}" if self.emulator else self.name
        return super().get_info(identifier)
    
    def screenshot(self) -> Image:
        identifier = f"emulator-{self.port}" if self.emulator else self.name
        return super().screenshot(identifier)

    def screenInput(self, x, y) -> None: 
        identifier = f"emulator-{self.port}" if self.emulator else self.name
        x_scaled = x*self.res_scalar_x #scaling values for normalization
        y_scaled = y*self.res_scalar_y

        super().screenInput(identifier, x_scaled, y_scaled)

    def screenSwipe(self, x1, y1, x2, y2) -> None:
        identifier = f"emulator-{self.port}" if self.emulator else self.name
        x1_scaled = x1*self.res_scalar_x #scaling values for normalization
        y1_scaled = y1*self.res_scalar_y
        x2_scaled = x2*self.res_scalar_x 
        y2_scaled = y2*self.res_scalar_y

        super().screenSwipe(identifier, x1_scaled, y1_scaled, x2_scaled, y2_scaled)
    
    def resolution(self):
        identifier = f"emulator-{self.port}" if self.emulator else self.name
        return super().resolution(identifier)

class ImageOcr:
    def __init__(self,im,res_scalar_x,res_scalar_y) -> None:
        # Search for tesseract.exe in the current directory or subdirectories
        current_dir = os.getcwd()
        tesseract_path = self.find_executable('tesseract.exe', current_dir)
        if not tesseract_path:
            raise FileNotFoundError("tesseract.exe not found in the current directory or subdirectories.")
        
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        self.res_scalar_x = res_scalar_x
        self.res_scalar_y = res_scalar_y
        self.im = im 

    def find_executable(self, filename, search_path) -> None:
        for root, dirs, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def crop_image(self,x1,y1,x2,y2) -> Image:
        x1_scaled = x1*self.res_scalar_x #scaling values for normalization
        y1_scaled = y1*self.res_scalar_y
        x2_scaled = x2*self.res_scalar_x 
        y2_scaled = y2*self.res_scalar_y

        _im = self.im.crop((x1_scaled, y1_scaled, x2_scaled, y2_scaled))
        return _im
    
    def get_text(self) -> str:
        # Extracting text from the image using pytesseract
        text = pytesseract.image_to_string(self.im).split()
        print(text)
        return text
