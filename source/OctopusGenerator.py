from PIL import Image, ImageDraw
import Analysis
import Perlin
import math

def displayColorMap(colorMap):
    barWidth = 4

    height = 40
    width = 255 * barWidth

    bgColor = (255, 255, 255, 0)

    mapImage = Image.new("RGBA", (width, height), bgColor)
    drawing = ImageDraw.Draw(mapImage)

    #draw grey
    for i in range(256):
        x0 = i * barWidth
        y0 = 0
        x1 = ((i+1) * barWidth)-1
        y1 = 20

        box = [x0, y0, x1, y1]

        drawing.rectangle(box, fill=(i,i,i))

    for i in range(256):
        x0 = i * barWidth
        y0 = 21
        x1 = ((i+1) * barWidth)-1
        y1 = 40

        box = [x0, y0, x1, y1]

        drawing.rectangle(box, fill=colorMap[i])

    mapImage.show()

def fade(x):
    #This fade function is taken from the Perlin Noise page
    return (6*x**5 - 15*x**4 + 10*x**3)

def interpolate(v0, v1, t):
    #This exact function is on the Wikipedia page for interpolation
    return v0 + (t*(v1 - v0))

def makeColorMap(hist):
    colorMap = dict()

    slideSpace = 80

    if len(hist.peaks) == 1:
        slideSpace = 0
        slideDistance = 0
    else:
        slideDistance = math.floor(slideSpace / (len(hist.peaks)-1))

    stretchSpace = 255 - slideSpace

    totalPeakHeight = 0
    for peak in hist.peaks:
        totalPeakHeight += peak[1]

    mapIndex = 0
    for peakNum in range(len(hist.peaks)):
        peak = hist.peaks[peakNum]
        stretch = math.floor(stretchSpace*(peak[1] / totalPeakHeight))

        for i in range(stretch):
            colorMap[mapIndex] = peak[0]
            mapIndex += 1

        if ((peakNum + 1) < len(hist.peaks)):
            nextPeak = hist.peaks[peakNum + 1]
            for i in range(slideDistance):
                t = i/slideDistance

                r = math.floor(interpolate(peak[0][0], nextPeak[0][0], t))
                g = math.floor(interpolate(peak[0][1], nextPeak[0][1], t))
                b = math.floor(interpolate(peak[0][2], nextPeak[0][2], t))

                colorMap[mapIndex] = (r,g,b)
                mapIndex += 1
        else:
            for i in range(256):
                if not i in colorMap:
                    colorMap[i] = peak[0]

    return colorMap

def printIntermediate(hist, colorMap, noise):
    hist.seePeaks()
    noise.show()
    displayColorMap(colorMap)

def addAlpha(color, alpha):
    colorList = list(color)
    colorList.append(alpha)
    return tuple(colorList)

def Generate(inputImg, outPath, debug = False):
    outSize = min(inputImg.size)

    hist = Analysis.Histogram(inputImg, 5, 6)
    noise = Perlin.Generate(outSize, outSize, len(hist.peaks), 0.9)
    colorMap = makeColorMap(hist)

    mask = Image.open("./Images/octopus_mask.jpg")
    mask = mask.resize((outSize, outSize))

    colorNoise = Image.new("RGBA", (outSize, outSize))

    for x in range(outSize):
        for y in range(outSize):
            noiseValue, _, _ = noise.getpixel((x, y))
            maskValue, _, _ = mask.getpixel((x, y))

            threshold = 255 // 2

            if maskValue > threshold:
                colorNoise.putpixel((x,y), addAlpha(colorMap[noiseValue], 255))
            else:
                colorNoise.putpixel((x,y), (0,0,0,0))

    if debug: printIntermediate(hist, colorMap, noise)
    colorNoise.save(outPath, "PNG")
    colorNoise.close
