from adbapi import Emulator,Phone
import time as t
phn = Phone('R5CRC0WAGML') 
print(phn.resolution())
phn.screenshot()
#phn.get_info()

#emu = Emulator(5554,-1)
#print(emu.resolution())
#emu.get_info()
