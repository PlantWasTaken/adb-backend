import subprocess
subprocess.call(['taskkill', '/F', '/IM', 'adb.exe'])
subprocess.run(f'{r'E:\adbapp\adbfolder\adb.exe'} start-server', shell=True) #R5CRC0WAGML
text = subprocess.run(f'{r'E:\adbapp\adbfolder\adb.exe'}  -s R5CRC0WAGML shell dumpsys activity top | find "mCurrentConfig"', shell=True,text=True,capture_output=True)
print(text)
#adb.exe -s R5CRC0WAGML shell dumpsys window | findstr "mFrame mUnrestricted"
#n = n[0].split()
#print(n)
#' Presentation: SPOT', '    Pointer Display ID: 0', '    Viewports:', '      DisplayViewport[id=0]', '        Width=1080, Height=2400', '        Transform (ROT_0)'