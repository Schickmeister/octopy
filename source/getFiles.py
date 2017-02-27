import easygui
from shutil import copyfile
import os

#filePath = easygui.fileopenbox(filetypes = ['*.jpg'], default="../Pictures/")
filePath = easygui.fileopenbox(filetypes = ['*.jpg'], default="../Pictures/")
#for demo purposes

if not filePath == None:
    filename = filePath.split(os.sep)[-1]
    newPath = "./images/" + filename

    copyfile(filePath, newPath)

    pathsFile = open("./images.txt", "r")
    fileText = pathsFile.read()
    fileText += (("%s:0:1\n") % newPath) 
    pathsFile.close()

    pathsFile = open("./images.txt", "w")
    pathsFile.write(fileText)
    pathsFile.close()
