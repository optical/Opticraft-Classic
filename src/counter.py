import os
Files = os.listdir('')
Lines = 0
for File in Files:
    if len(File) < 3:
        continue
    if File[-3:] != '.py':
        continue
    Lines += len(open(File).readlines())
    
raw_input("Total lines %s" %Lines)