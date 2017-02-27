from PIL import Image, ImageDraw
import math

#Adapted from make2dList in the course notes
def make3dList(rows, cols, stacks):
    a=[]
    for row in range(rows): a += [[None]*cols]
    for row in range(rows):
        for col in range(cols):
            a[row][col] = [0]*stacks
    return a

#Similar to code I came across researching the PIL getdata() function, but
#I rewrote it myself
def get2dPixelList(image):
    width, height = image.size
    imageData = list(image.getdata())
    pixels = []

    for row in range(height):
        pixels += [imageData[row * width: (row + 1) * width]]

    return pixels

class Histogram(object):
    def __init__(self, image, bucketsPerColor = 4, peakThreshold = 4):
        self.image = image
        self.bucketsPerColor = bucketsPerColor
        self.peakThreshold = peakThreshold
        self.bucketSize = math.ceil(255 / bucketsPerColor)
        self.buckets = make3dList(bucketsPerColor, bucketsPerColor, bucketsPerColor)

        self.bucketColorR = make3dList(bucketsPerColor, bucketsPerColor, bucketsPerColor)
        self.bucketColorG = make3dList(bucketsPerColor, bucketsPerColor, bucketsPerColor)
        self.bucketColorB = make3dList(bucketsPerColor, bucketsPerColor, bucketsPerColor)

        self.imagePixels = get2dPixelList(self.image)
        self.peaks = []

        self.populate()
        self.getPeaks()

    def populate(self):
        pixelRows, pixelCols = len(self.imagePixels), len(self.imagePixels[0])

        for row in range(pixelRows):
            for col in range(pixelCols):
                pixel = self.imagePixels[row][col]

                rBucket = pixel[0] // self.bucketSize
                gBucket = pixel[1] // self.bucketSize
                bBucket = pixel[2] // self.bucketSize

                rBucket = min(rBucket, self.bucketsPerColor - 1)
                gBucket = min(gBucket, self.bucketsPerColor - 1)
                bBucket = min(bBucket, self.bucketsPerColor - 1)

                self.buckets[rBucket][gBucket][bBucket] += 1
                self.bucketColorR[rBucket][gBucket][bBucket] += pixel[0]
                self.bucketColorG[rBucket][gBucket][bBucket] += pixel[1]
                self.bucketColorB[rBucket][gBucket][bBucket] += pixel[2]

    def averageBucketColor(self, rBucket, gBucket, bBucket):
        bucketSize = self.buckets[rBucket][gBucket][bBucket]

        averageR = math.floor(self.bucketColorR[rBucket][gBucket][bBucket] / bucketSize)
        averageG = math.floor(self.bucketColorG[rBucket][gBucket][bBucket] / bucketSize)
        averageB = math.floor(self.bucketColorB[rBucket][gBucket][bBucket] / bucketSize)

        return (averageR, averageG, averageB)

    def colorDistance(self, color1,color2):
        r1 = color1[0]
        r2 = color2[0]
        g1 = color1[1]
        g2 = color2[1]
        b1 = color1[2]
        b2 = color2[2]

        return math.sqrt(((r2-r1)**2) + ((g2-g1)**2) + ((b2-b1)**2))

    #Adapted from the notes
    def peakQuicksort(self, L):
        if (len(L) < 2):
            return L
        else:
            first = L[0]  # pivot
            rest = L[1:]
            lo = [x for x in rest if x[2] < first[2]]
            hi = [x for x in rest if x[2] >= first[2]]
            return self.peakQuicksort(lo) + [first] + self.peakQuicksort(hi)

    def getPeaks(self):
        self.peaks = []

        numPixels = (len(self.imagePixels) * len(self.imagePixels[0]))
        averageBucketValue = numPixels / (self.bucketsPerColor ** 3)

        for rBucket in range(self.bucketsPerColor):
             for gBucket in range(self.bucketsPerColor):
                 for bBucket in range(self.bucketsPerColor):
                    bucketValue = self.buckets[rBucket][gBucket][bBucket]
                    if bucketValue > (averageBucketValue * self.peakThreshold):
                        averageRGB = self.averageBucketColor(rBucket, gBucket, bBucket)
                        orderNumber = self.colorDistance(averageRGB, (0,0,0))

                        self.peaks.append((averageRGB, bucketValue, orderNumber))

        self.peaks = self.peakQuicksort(self.peaks)

    def getLargestPeak(self):
        largestPeak = None
        largestValue = None
        for peak in self.peaks:
            if largestValue == None or peak[1] > largestValue:
                largestValue = peak[1]
                largestPeak = peak

        return largestPeak

    def seePeaks(self):
        height = 300
        width = 500

        hScale = height / self.getLargestPeak()[1]
        wScale = width / len(self.peaks)
        bgColor = (255, 255, 255, 0)

        peakImage = Image.new("RGBA", (width, height), bgColor)
        drawing = ImageDraw.Draw(peakImage)

        for peakNum in range(len(self.peaks)):
            x0 = peakNum * wScale
            y0 = height
            x1 = (peakNum + 1) * wScale
            y1 = height - (self.peaks[peakNum][1] * hScale)

            box = [x0, y0, x1-1, y1-1]
            peakColor = self.peaks[peakNum][0] + (255,)

            drawing.rectangle(box, fill=peakColor)

        drawing.rectangle([0, 0, width-1, height-1], outline = (0, 0, 0, 0))
        peakImage.show()
