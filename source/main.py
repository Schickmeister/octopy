import pygame
from PIL import Image
import os
import sys
import random
import Analysis
import OctopusGenerator
import ImageOpener
import copy
import math
import time

###################################
##             Classes           ##
###################################

class Button(object):
    def __init__(self, x, y, width, height, function, color, text, data, 
                 autocolor=False, active=True):
        self.x = round(x - (width / 2))
        self.y = round(y - (height / 2))
        self.width = width
        self.height = height
        self.function = function
        self.data = data
        self.color = color
        self.text = text
        self.rect = (self.x, self.y, self.width, self.height)
        self.drawnOnce = False
        self.autocolor = autocolor
        self.active = active

    def draw(self):
        if not self.active: return

        if self.autocolor and not self.drawnOnce:
            self.color = self.getColor()
            self.drawnOnce = True

        pygame.draw.rect(self.data.screen, self.color, self.rect)

        textX = round(self.x + (self.width / 2))
        textY = round(self.y + (self.height / 2))

        draw_bordered_text("Helvetica", 45, (0,0,0), 
                           (255,255,255), self.text, textX, textY, 
                           self.data, True)

    def checkClick(self, position):
        if not self.active: return

        clickX = position[0]
        clickY = position[1]

        if ((clickX > self.x) and (clickX < (self.x + self.width)) and 
            (clickY > self.y) and (clickY < (self.y + self.height))):
                self.function(self.data)
                return True
        else:
            return False

    def getColor(self):
        image = self.data.PILImage
        box = (self.x, self.y, self.x + self.width, self.y + self.height)
        selectionImg = image.crop(box)
        hist = Analysis.Histogram(selectionImg, 5, 6)
        hist.getPeaks()
        return hist.peaks[-1][0]

class imageThumbnail(object):
    def __init__(self, imagePath, row, col, default, active, data):
        self.data = data
        self.imagePath = imagePath

        self.xOffset = (self.data.imageBoxRect[2] / 20)
        self.yOffset = (self.data.imageBoxRect[2] / 20)
        self.width = (self.data.imageBoxRect[2] - (4 * self.xOffset)) / 3
        self.height = (self.data.imageBoxRect[3] - (3 * self.yOffset)) / 2

        self.x = ((self.xOffset) * (col+1)) + (self.width * col)
        self.y = ((self.yOffset) * (row+1)) + (self.height * row)
        self.x += self.data.imageBoxRect[0]
        self.y += self.data.imageBoxRect[1]

        self.drawingY = self.y

        self.selected = False
        self.default = default
        self.active = active

        self.setImage()
    def setImage(self):
        self.pilImage = Image.open(self.imagePath)
        self.pilImage = self.pilImage.resize((round(self.width), 
                                              round(self.height)))
        if not self.active:
            self.pilImage = self.pilImage.convert('L')

        self.image = PILtoPygame(self.pilImage, self.imagePath)

        maxRows = (len(self.data.totalImagePaths)-1) // 3
        self.data.maxScrollOffset = ((self.height + self.yOffset) * 
                                      max(0,(maxRows-1)))

    def draw(self):
        self.drawingY = (self.y - self.data.imageBoxScrollOffset)
        self.data.screen.blit(self.image, (self.x, self.drawingY))

        if self.selected:
            rect = (self.x, self.drawingY, self.width, self.height)
            pygame.draw.rect(self.data.screen, (20,20,20), rect, 3)

    def setButtons(self):
        if self.active:
            self.data.imagesUseButton.active = False
            self.data.imagesDontUseButton.active = True
        else:
            self.data.imagesUseButton.active = True
            self.data.imagesDontUseButton.active = False
        if self.default:
            self.data.imagesDeleteButton.active = False
        else:
            self.data.imagesDeleteButton.active = True

    def checkClick(self, position):
        clickX = position[0]
        clickY = position[1]

        if ((clickX > self.x) and (clickX < (self.x + self.width)) and 
            (clickY > self.drawingY) and 
            (clickY < (self.drawingY + self.height)) and
            inImageBoxBounds(clickX, clickY, self.data)):

            for thumbnail in self.data.imageThumbnails:
                thumbnail.selected = False

            self.selected = True
            self.setButtons()

###################################
##  High level helper functions  ##
###################################

def make3dList(rows, cols, stacks):
    a=[]
    for row in range(rows): a += [[None]*cols]
    for row in range(rows):
        for col in range(cols):
            a[row][col] = [0]*stacks
    return a

def attemptDeletion(path):
    try:
        os.remove(path)
    except:
        pass

###################################
##  Game logic helper functions  ##
###################################

def add_octopus(data, x, y):
    image = data.PILImage

    size = data.octopusSize

    box = (x, y, x+size, y+size)
    selectionImg = image.crop(box)

    OctopusGenerator.Generate(selectionImg, data.octopusPath)
    data.octopi.append((pygame.image.load(data.octopusPath).convert_alpha(), 
                       (x, y)))

    #for testing
    #data.octopi.append((pygame.image.load
    #                   ("./Images/octopus_mask.jpg").convert_alpha(), (x, y)))

def set_level(data):
    data.octopi = []

    size = data.octopusSize

    positions = []
    for x in range(data.width - size):
        for y in range(data.height - size):
            positions.append((x,y))

    for i in range(data.octopiPerLevel):
        x,y = random.choice(positions)

        newPos = []
        for p in positions:
            if not ((abs(p[0] - x) < size) and (abs(p[1] - y) < size)):
                newPos.append(p)

        positions = newPos
        add_octopus(data, x, y)

def checkOctopusClick(data, position):
    updatedOctopi = []
    x = position[0]
    y = position[1]

    for i in range(len(data.octopi)):
        octopus = data.octopi[i]

        octX = octopus[1][0]
        octY = octopus[1][1]
        if not ((x > octX) and (x < (octX + data.octopusSize)) and 
            (y > octY) and (y < (octY + data.octopusSize))):

            updatedOctopi.append(octopus)

    if len(updatedOctopi) < len(data.octopi):
        pygame.mixer.Sound("./sounds/pop.wav").play()
    data.octopi = updatedOctopi

def backToTitleScreen(data):
    initGameVariables(data)
    data.imageIndex = 0
    data.currentImagePath = data.titlePath
    set_background_image(data)
    data.gameMode = data.TITLE
    data.timerSeconds = data.maxTimerSeconds

###################################
##     Image helper functions    ##
###################################

def PILtoPygame(image, path):
    file, extension = os.path.splitext(path)
    newPath = file + "_temp" + extension
    image.save(newPath)
    pygameImage = pygame.image.load(newPath)
    attemptDeletion(newPath)    

    return pygameImage

def fit_image(data):
    file, extension = os.path.splitext(data.currentImagePath)
    newPath = file + "_temp" + extension

    image = Image.open(data.currentImagePath)
    tempImage = image.resize(data.screenSize)
    tempImage.save(newPath)
    return pygame.image.load(newPath), newPath, tempImage

def analyze_selection(data):
    image = data.PILImage

    bleft = min(data.selection[0][0], data.selection[1][0])
    bright = max(data.selection[0][0], data.selection[1][0])
    blower = max(data.selection[0][1], data.selection[1][1])
    bupper = min(data.selection[0][1], data.selection[1][1])

    box = (bleft, bupper, bright, blower)
    selectionImg = image.crop(box)

    OctopusGenerator.Generate(selectionImg, data.octopusPath, True)
    data.octopi.append((pygame.image.load(data.octopusPath).convert_alpha(), 
                       (data.selection[0][0], data.selection[0][1])))

###################################
##         Input functions       ##
###################################

def mouse_down(data, event):
    if data.gameMode == data.PLAY:
        if data.generation_mode == True:
            data.octopusImage = None
            data.drawingSelection = True
            data.selection[0] = pygame.mouse.get_pos()
            data.selection[1] = data.selection[0]
    elif data.gameMode == data.IMAGES:
        scrollSpeed = 5

        mouseX, mouseY = pygame.mouse.get_pos()
        if not inImageBoxBounds(mouseX, mouseY, data):
            return

        if event.button == 4:
            data.imageBoxScrollOffset -= scrollSpeed
        if event.button == 5:
            data.imageBoxScrollOffset += scrollSpeed

        data.imageBoxScrollOffset = max(0, data.imageBoxScrollOffset)
        data.imageBoxScrollOffset = min(data.imageBoxScrollOffset, 
                                        data.maxScrollOffset)

def imagesMouseUp(data, event):
    buttonClicked = False

    for button in data.imagesScreenButtons:
        if button.checkClick(pygame.mouse.get_pos()):
            buttonClicked = True

    data.imagesUseButton.active = False
    data.imagesDontUseButton.active = False
    data.imagesDeleteButton.active = False
    data.imagesAddButton.active = True

    if not buttonClicked:
        for thumbnail in data.imageThumbnails:
            thumbnail.selected = False
            thumbnail.checkClick(pygame.mouse.get_pos())

    for thumbnail in data.imageThumbnails:
        if thumbnail.selected:
            data.imagesAddButton.active = False
            thumbnail.setButtons()

def mouse_up(data, event):
    if event.button == 4 or event.button == 5: return

    if data.gameMode == data.PLAY:
        if data.generation_mode == True:
            data.drawingSelection = False
            data.selection[1] = pygame.mouse.get_pos()
            analyze_selection(data)
        else:
            checkOctopusClick(data, pygame.mouse.get_pos())
    elif data.gameMode == data.TITLE:
        for button in data.titleScreenButtons:
            button.checkClick(pygame.mouse.get_pos())
    elif data.gameMode == data.WIN:
        for button in data.winScreenButtons:
            button.checkClick(pygame.mouse.get_pos())
    elif data.gameMode == data.LOSE:
        for button in data.loseScreenButtons:
            button.checkClick(pygame.mouse.get_pos())
    elif data.gameMode == data.IMAGES:
        imagesMouseUp(data, event)

def mouse_moved(data):
    if data.gameMode == data.PLAY:
        if data.drawingSelection == True:
            data.selection[1] = pygame.mouse.get_pos()

def key_press(data, key):
    if data.gameMode == data.PLAY:
        if key == pygame.K_ESCAPE:
            backToTitleScreen(data)
    if data.gameMode == data.IMAGES:
        os.system("python3 getFiles.py")
        initImagesScreen(data)
        initGameVariables(data)
        data.gameMode = data.IMAGES

###################################
##       Drawing functions       ##
###################################

def inImageBoxBounds(x,y,data):
    return ((x > data.imageBoxRect[0]) and 
            (x < data.imageBoxRect[0] + data.imageBoxRect[2]) and 
            (y > data.imageBoxRect[1]) and
            (y < data.imageBoxRect[1] + data.imageBoxRect[3]))

def set_background_image(data):
    data.image, data.imageTempPath, data.PILImage = fit_image(data)

def draw_selection_bounds(data):
    if (data.selection[0] == None 
        or data.selection[1] == None): return

    rectX = data.selection[0][0]
    rectY = data.selection[0][1]
    rectW = data.selection[1][0] - data.selection[0][0]
    rectH = data.selection[1][1] - data.selection[0][1]
    rect = (rectX, rectY, rectW, rectH)

    linewidth = 2
    color = (0, 0, 0)

    pygame.draw.rect(data.screen, color, rect, linewidth)

def draw_octopi(data, outlines = False):
    if not data.octopi == []:
        for oImg in data.octopi:
            data.screen.blit(oImg[0], oImg[1])
            if outlines == True:
                x,y = oImg[1]
                width,height = oImg[0].get_rect().size
                rect = (x,y,width,height)
                pygame.draw.rect(data.screen, (255,0,0), rect, 2)

def draw_bordered_text(fontName, fontSize, bgColor, fgColor, text, x, y, data,
                       centered = False):

    font = pygame.font.SysFont(fontName, fontSize)

    if centered:
        textSize = font.size(text)
        x = (x - (textSize[0] / 2))
        y = (y - (textSize[1] / 2))

    textOutlineSurface = font.render(text, False, bgColor)
    data.screen.blit(textOutlineSurface, (x-1, y-1))
    data.screen.blit(textOutlineSurface, (x+1, y+1))
    data.screen.blit(textOutlineSurface, (x-1, y+1))
    data.screen.blit(textOutlineSurface, (x+1, y-1))

    textSurface = font.render(text, False, fgColor)
    data.screen.blit(textSurface, (x,y))

def draw_timer(data):
    timerOffset = 15

    minutes = data.timerSeconds // 60
    seconds = int(data.timerSeconds % 60)

    timerString = "%d:%02d" % (minutes, seconds)

    x = timerOffset
    y = timerOffset

    fgColor = (255,255,255)
    if data.timerSeconds <= 10:
        fgColor = (255,0,0)

    draw_bordered_text("Arial", 34, (0,0,0), fgColor, timerString,
                       x, y, data)

def drawTitleScreen(data):
    x = (data.width/2)
    y = (data.height/5)

    draw_bordered_text("Helvetica", 100, (0,0,0), (255,255,255), "OCTO.PY",
                       x, y, data, True)

    for button in data.titleScreenButtons:
        button.draw()

def drawWinScreen(data):
    scoreStr = "Score: %0.2f Octopi Per Second" % (data.score)
    draw_bordered_text("Helvetica", 70, (0,0,0), (255,255,255), "You won!",
                       data.width*(10/20), data.height*(3/20), data, True)
    draw_bordered_text("Helvetica", 50, (0,0,0), (255,255,255), scoreStr,
               data.width*(10/20), data.height*(8/20), data, True)

    if not data.newHighScore:
        highScoreStr = "High Score: %0.2f Octopi Per Second" % (data.highScore)
        draw_bordered_text("Helvetica", 50, (0,0,0), (255,255,255), 
            highScoreStr, data.width*(10/20), data.height*(11/20), data, True)
    else:
        highScoreStr = "New High Score!"
        draw_bordered_text("Helvetica", 50, (0,0,0), (255,255,255), 
            highScoreStr, data.width*(10/20), data.height*(11/20), data, True)

    for button in data.winScreenButtons:
        button.draw()

def drawLoseScreen(data):
    draw_bordered_text("Helvetica", 70, (0,0,0), (255,255,255), "You Lost",
                       data.width*(10/20), data.height*(6/20), data, True)
    for button in data.loseScreenButtons:
        button.draw()

def setImageBoxRect(data):
    imageBoxX = (data.width * (1/20))
    imageBoxY = imageBoxX
    imageBoxHeight = (data.height * (13/20))
    imageBoxWidth = (data.width - (2*imageBoxX))
    imageBoxRect = (imageBoxX, imageBoxY, imageBoxWidth, imageBoxHeight)
    data.imageBoxRect = imageBoxRect

def drawImagesScreen(data):
    pygame.draw.rect(data.screen, (255,255,255), data.imageBoxRect)

    buttonsToDraw = []
    for thumbnail in data.imageThumbnails:
        thumbnail.draw()

    data.screen.blit(data.cutoutTitleImage, (0,0))

    for button in data.imagesScreenButtons:
        button.draw()

def redraw_all(data):
    data.screen.blit(data.image, (0,0)) #draw background image

    if data.gameMode == data.TITLE:
        drawTitleScreen(data)
    elif data.gameMode == data.PLAY:
        draw_octopi(data)
        if data.drawingSelection: draw_selection_bounds(data) #draw selection
        draw_timer(data)
    elif data.gameMode == data.WIN:
        drawWinScreen(data)
    elif data.gameMode == data.LOSE:
        drawLoseScreen(data)
    elif data.gameMode == data.IMAGES:
        drawImagesScreen(data)
    pygame.display.flip() #actually display everything

###################################
##       General  Functions      ##
###################################

def win(data):
    for button in data.winScreenButtons:
        button.drawnOnce = False

    totalOctopi = (data.octopiPerLevel * len(data.activeImagePaths))
    totalSeconds = (data.maxTimerSeconds - data.timerSeconds)

    data.score = (totalOctopi / totalSeconds)
    data.newHighScore = False

    highscoreFile = open("./data/highscore.txt", "r")
    data.highScore = float(highscoreFile.read())
    highscoreFile.close()

    if data.score > data.highScore:
        highscoreFile = open("./data/highscore.txt", "w")
        highscoreFile.write(str(data.score))
        highscoreFile.close()
        data.newHighScore = True
        data.highScore = data.score

    data.gameMode = data.WIN
    os.system("say 'you won'")

def lose(data):
    for button in data.loseScreenButtons:
        button.drawnOnce = False

    data.gameMode = data.LOSE
    os.system("say 'you lose'")
    draw_octopi(data, True)
    pygame.display.flip()
    time.sleep(6)

def playLoop(data):
    if data.octopi == []:
        data.imageIndex += 1

        if data.imageIndex == len(data.activeImagePaths):
            win(data)
            return

        data.currentImagePath = data.activeImagePaths[data.imageIndex]
        set_background_image(data)
        set_level(data)

    pygame.time.delay(10)
    data.timerSeconds -= .01

    if data.timerSeconds <= 0:
        lose(data)
        return

def game_loop(data):
    redraw_all(data)
    check_events(data)
    if data.gameMode == data.PLAY:
        playLoop(data)

def check_events(data):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            data.running = False
            pygame.quit()
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down(data, event)
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_up(data, event)
        if event.type == pygame.MOUSEMOTION:
            mouse_moved(data)
        if event.type == pygame.KEYDOWN:
            key_press(data, event.key)

###################################
##           Init & Run          ##
###################################

def initBaseVariables(data):
    data.running = True
    data.screenSize = (800, 500)
    data.width = data.screenSize[0]
    data.height = data.screenSize[1]
    data.screen = pygame.display.set_mode(data.screenSize)
    data.clock = pygame.time.Clock()

def initGameMode(data):
    data.TITLE = 0
    data.PLAY = 1
    data.WIN = 2
    data.LOSE = 3
    data.IMAGES = 4

    data.gameMode = data.TITLE

def getPathLines(data):
    pathsFile = open("./data/images.txt")
    pathsText = pathsFile.read()
    pathsFile.close()

    return pathsText.splitlines()

def getAllImagePaths(data):
    paths = []
    pathsLines = getPathLines(data)

    for pathLine in pathsLines:
        paths.append(pathLine.split(":")[0])

    return paths

def getActiveImagePaths(data):
    paths = []
    pathsLines = getPathLines(data)

    for pathLine in pathsLines:
        path, default, active = pathLine.split(":")
        if active == "1":
            paths.append(path)

    return paths

def initGameVariables(data):
    data.totalImagePaths = getAllImagePaths(data)
    data.activeImagePaths = getActiveImagePaths(data)

    data.imageIndex = 0

    data.octopusPath = "./images/octopus.png"
    data.octopi = []
    data.octopiPerLevel = 5
    data.octopusSize = 60

    data.titlePath = "./images/title.jpg"

    initGameMode(data)

    data.currentImagePath = data.titlePath

    data.secondsPerOctopus = 3
    data.maxTimerSeconds = (data.secondsPerOctopus * data.octopiPerLevel *
                            len(data.activeImagePaths))
    data.timerSeconds = data.maxTimerSeconds

def initGenerationMode(data):
    data.generation_mode = False
    data.drawingSelection = False
    data.selection = [None, None]

    ###################################
    ##          Title Screen         ##
    ###################################

def playButtonFunction(data):
    if len(data.activeImagePaths) < 1:
        pygame.mixer.Sound("./sounds/error.wav").play()
        return

    data.gameMode = data.PLAY
    data.activeImagePaths = getActiveImagePaths(data)
    data.imageIndex = 0
    data.timerSeconds = data.maxTimerSeconds
    data.currentImagePath = data.activeImagePaths[data.imageIndex]
    set_background_image(data)
    set_level(data)

def initPlayButton(data, again = False):
    buttonWidth = round(data.width * (5/20))
    buttonHeight = round(data.height * (4/20))

    pButtonX = round(data.width * (5/20))
    pButtonY = round(data.height * (11/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  playButtonFunction, (0,100,170), "PLAY", data)

def imagesButtonFunction(data):
    data.gameMode = data.IMAGES

def initImagesButton(data):
    buttonWidth = round(data.width * (5/20))
    buttonHeight = round(data.height * (4/20))

    pButtonX = round(data.width * (15/20))
    pButtonY = round(data.height * (11/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  imagesButtonFunction, (0,100,170), "IMAGES", data)

def quitButtonFunction(data):
    data.running = False

def initQuitButton(data):
    buttonWidth = round(data.width * (5/20))
    buttonHeight = round(data.height * (4/20))

    #pButtonX = round(data.width * (15/20))
    pButtonX = round(data.width * (10/20))
    pButtonY = round(data.height * (17/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  quitButtonFunction, (0,100,170), "QUIT", data)

def initTitleScreen(data):
    playButton = initPlayButton(data)
    imagesButton = initImagesButton(data)
    quitButton = initQuitButton(data)

    data.titleScreenButtons = [playButton, imagesButton, quitButton]

    ###################################
    ##         \ Title Screen        ##
    ###################################

def initWinHomeButton(data):
    buttonWidth = round(data.width * (7/20))
    buttonHeight = round(data.height * (4/20))

    pButtonX = round(data.width * (5/20))
    pButtonY = round(data.height * (16/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  backToTitleScreen, (0,100,170), "HOME", data, True)

def initWinPlayAgainButton(data):
    buttonWidth = round(data.width * (7/20))
    buttonHeight = round(data.height * (4/20))

    pButtonX = round(data.width * (15/20))
    pButtonY = round(data.height * (16/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  playButtonFunction, (0,100,170), "PLAY AGAIN", data, True)

def initWinScreen(data):
    homeButton = initWinHomeButton(data)
    playAgain = initWinPlayAgainButton(data)

    data.winScreenButtons = [homeButton, playAgain]

def initLoseScreen(data):
    homeButton = initWinHomeButton(data)
    playAgain = initWinPlayAgainButton(data)

    data.loseScreenButtons = [homeButton, playAgain]

def setCutoutTitleImage(data):
    pilTitleImage = Image.open(data.titlePath)
    pilTitleImage = pilTitleImage.resize(data.screenSize)
    cutoutTitleImage = Image.new("RGBA", data.screenSize)

    for x in range(data.width):
        for y in range(data.height):
            if inImageBoxBounds(x,y,data):
                cutoutTitleImage.putpixel((x,y), (0,0,0,0))
            else:
                cutoutTitleImage.putpixel((x,y), OctopusGenerator.addAlpha(
                                 pilTitleImage.getpixel((x,y)), 255))

    path = "./images/cutoutTitleImage.png"

    cutoutTitleImage.save(path, "PNG")
    data.cutoutTitleImage = pygame.image.load(path)

def initImagesBackButton(data):
    buttonWidth = round(data.width * (5/20))
    buttonHeight = round(data.height * (4/20))

    pButtonX = round(data.width * (1/20)) + (buttonWidth / 2)
    pButtonY = round(data.height * (17/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  backToTitleScreen, (0,100,170), "DONE", data)

def useButtonFunction(data):
    pathToChange = ""

    for thumbnail in data.imageThumbnails:
        if thumbnail.selected == True:
            pathToChange = thumbnail.imagePath
            thumbnail.active = True
            thumbnail.setImage()

    strOut = ""
    pathsLines = getPathLines(data)

    for line in pathsLines:
        path, default, active = line.split(":")
        if path == pathToChange:
            active = "1"
        strOut += (":".join((path,default,active)) + "\n")

    pathsFile = open("./data/images.txt", "w")
    pathsFile.write(strOut)
    pathsFile.close()

def initImagesUseButton(data):
    buttonWidth = round(data.width * (5/20))
    buttonHeight = round(data.height * (4/20))

    pButtonX = round(data.width * (10/20))
    pButtonY = round(data.height * (17/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  useButtonFunction, (0,100,170), "ENABLE", data, active=False)
def deleteButtonFunction(data):
    pathToChange = ""

    for thumbnail in data.imageThumbnails:
        if thumbnail.selected == True:
            pathToChange = thumbnail.imagePath

    strOut = ""
    pathsLines = getPathLines(data)

    for line in pathsLines:
        path, default, active = line.split(":")
        if not path == pathToChange:
           strOut += (":".join((path,default,active)) + "\n")

    pathsFile = open("./data/images.txt", "w")
    pathsFile.write(strOut)
    pathsFile.close()

    initGameVariables(data)
    initImagesScreen(data)
    data.gameMode = data.IMAGES

def initImagesDeleteButton(data):
    buttonWidth = round(data.width * (5/20))
    buttonHeight = round(data.height * (4/20))

    pButtonX = round(data.width * (19/20)) - (buttonWidth / 2)
    pButtonY = round(data.height * (17/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  deleteButtonFunction, (0,100,170), "DELETE", 
                  data, active=False)

def addButtonFunction(data):
    os.system("python3 getFiles.py")
    initGameVariables(data)
    initImagesScreen(data)
    data.gameMode = data.IMAGES

def initImagesAddButton(data):
    buttonWidth = round(data.width * (5/20))
    buttonHeight = round(data.height * (4/20))

    pButtonX = round(data.width * (10/20))
    pButtonY = round(data.height * (17/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  addButtonFunction, (0,100,170), "ADD", data, active=True)

def dontUseButtonFunction(data):
    pathToChange = ""

    for thumbnail in data.imageThumbnails:
        if thumbnail.selected == True:
            pathToChange = thumbnail.imagePath
            thumbnail.active = False
            thumbnail.setImage()

    strOut = ""
    pathsLines = getPathLines(data)

    for line in pathsLines:
        path, default, active = line.split(":")
        if path == pathToChange:
            active = "0"
        strOut += (":".join((path,default,active)) + "\n")

    pathsFile = open("./data/images.txt", "w")
    pathsFile.write(strOut)
    pathsFile.close()

def initImagesDontUseButton(data):
    buttonWidth = round(data.width * (5/20))
    buttonHeight = round(data.height * (4/20))

    pButtonX = round(data.width * (10/20))
    pButtonY = round(data.height * (17/20))

    return Button(pButtonX, pButtonY, buttonWidth, buttonHeight, 
                  dontUseButtonFunction, (0,100,170), 
                  "DISABLE", data, active=False)

def populateImageThumbnails(data):
    thumbnails = []
    pathsLines = getPathLines(data)

    for i in range(len(pathsLines)):
        pathLine = pathsLines[i]
        path, default, active = pathLine.split(":")

        if active == "1": active = True
        else: active = False
        if default == "1": default = True
        else: default = False

        thumbnails.append(imageThumbnail(path, i//3, i%3, 
                                         default, active, data))

    return thumbnails

def initImagesScreen(data):
    data.imageThumbnails = []
    setImageBoxRect(data)
    data.imageBoxScrollOffset = 0

    setCutoutTitleImage(data)

    data.imageThumbnails = populateImageThumbnails(data)

    data.imagesBackButton = initImagesBackButton(data)
    data.imagesUseButton = initImagesUseButton(data)
    data.imagesDontUseButton = initImagesDontUseButton(data)
    data.imagesDeleteButton = initImagesDeleteButton(data)
    data.imagesAddButton = initImagesAddButton(data)

    data.imagesScreenButtons = [data.imagesBackButton, data.imagesUseButton, 
                                data.imagesDontUseButton, 
                                data.imagesDeleteButton, data.imagesAddButton]

def initScreens(data):
    initTitleScreen(data)
    initImagesScreen(data)
    initWinScreen(data)
    initLoseScreen(data)

def cleanup(data):
    attemptDeletion(data.imageTempPath)
    attemptDeletion(data.octopusPath)
    pygame.quit()

def run():
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()

    pygame.display.set_caption("octo.py")
    pygame.mixer.Sound("./sounds/background.wav").play(-1)

    class Struct(object): pass
    data = Struct()

    initBaseVariables(data)
    initGameVariables(data)
    initGenerationMode(data)
    initScreens(data)

    set_background_image(data)

    while data.running:
        game_loop(data)
    cleanup(data)

run()
print("bye!")