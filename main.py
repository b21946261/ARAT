import time

import cv2 as cv
import numpy as np
from pynput.keyboard import Key, Controller
import pyautogui
import PIL

keyboard = Controller()

imgWidth = 1920
imgHeight = 1080

screenCenter = (imgWidth/2, imgHeight/2)

turnLeft = Key.left
turnRight = Key.right
goUp = Key.up
goDown = Key.down

goForward = 'w'
goLeft = 'a'
goRight = 'd'
goBackward = 's'


def pressAndRelease(key, seconds):
    keyboard.press(key)
    time.sleep(seconds)
    keyboard.release(key)

def ssAl():
    myScreenshot = pyautogui.screenshot()
    myScreenshot.save("Images/ss.png")


"""
Çemberin merkezinin verilen hata payı dahil olmak üzere ekranı ortalayıp ortalamadığını
kontrol eder.
"""
def centered(center):
    centerX = center[0]
    centerY = center[1]

    if abs(screenCenter[0] - centerX) < (screenCenter[0] * 0.05) and\
        abs(screenCenter[1] - centerY) < (screenCenter[1] * 0.05):
        return True

    else:
        return False


"""
Çemberin merkezinin koordinatlarını merkezin koordinatlarıyla karşılaştırır ve 
kartezyen koordinat sisteminde hangi bölgede bulunduğunu return eder.
"""
def locateCenter(center):
    isLeft = False
    isBelow = False

    if center[0] < screenCenter[0]:
        isLeft = True

    if center[1] > screenCenter[1]:
        isBelow = True

    if not isLeft and not isBelow:
        return 1
    elif isLeft and not isBelow:
        return 2
    elif isLeft and isBelow:
        return 3
    elif not isLeft and isBelow:
        return 4

def solveEllipse(center):
    return None

def centeringByLocation(location, releaseDelay):
    if location == 1:
        pressAndRelease(goRight, releaseDelay)
        pressAndRelease(goUp, releaseDelay)
        pressAndRelease(goForward, releaseDelay)

    elif location == 2:
        pressAndRelease(goLeft, releaseDelay)
        pressAndRelease(goUp, releaseDelay)
        pressAndRelease(goForward, releaseDelay)

    elif location == 3:
        pressAndRelease(goLeft, releaseDelay)
        pressAndRelease(goDown, releaseDelay)
        pressAndRelease(goForward, releaseDelay)

    elif location == 4:
        pressAndRelease(goRight, releaseDelay)
        pressAndRelease(goDown, releaseDelay)
        pressAndRelease(goForward, releaseDelay)

def turning(center):
    isLeft = False
    if center[0] < screenCenter[0]:
        isLeft = True

    distance = abs(center[0] - screenCenter[0])

    if distance < screenCenter[0] * 0.2:
        pass
    else:
        releaseDelay = distance / screenCenter[0]

        if isLeft:
            pressAndRelease(turnLeft, releaseDelay)
            #pressAndRelease(goRight, releaseDelay)

        else:
            pressAndRelease(turnRight, releaseDelay)
            #pressAndRelease(goLeft, releaseDelay)


def runSim():
    time.sleep(3)
    while True:
        ssAl()
        img = cv.imread("Images/ss.png")

        try:
            circles = findCircles(img)
        except Exception:
            pressAndRelease(goForward, 1)
            continue

        FTCList = findTargetCircle(img, circles)
        print(FTCList)
        center = FTCList[0]
        isEllipse = FTCList[1]
        radius = FTCList[2]

        if isEllipse:
            solveEllipse(center)
            print("anan")
            time.sleep(1000)


        location = locateCenter(center)
        if radius > 220:
            turning(center)
            centeringByLocation(location, 0.09)
            if centered(center):
                pressAndRelease(goForward, 3)

        else:
            pressAndRelease(goForward, 1)




def findCircles(img):
    imgHSV = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    imgGray = cv.cvtColor(imgHSV, cv.COLOR_BGR2GRAY)
    imgBlur = cv.GaussianBlur(imgGray, (7, 7), cv.BORDER_DEFAULT)

    """
    4. parametre çmerber merkezleri arasındaki min uzaklığı belirtir. 
    param1 canny edge detection higher olan,param1 in yarısı da lower olan. 
    param2 küçüldükçe false circle bulma ihtimali artar.
    """

    circles = cv.HoughCircles(imgBlur, cv.HOUGH_GRADIENT, 0.9, 200, param1=40, param2=25, minRadius=0, maxRadius=5000)
    circlesRounded = np.uint16(np.around(circles))

    return circlesRounded

def findTargetCircle(img_orig, circlesRounded):
    # circle array bakıcak ekranın merkezine en yakın ve alanı en büyük olanı hedef belirlemeli

    cir1 = (0, 0)
    cir2 = (0, 0)
    centerArr = []
    cirDict = {}

    if len(circlesRounded[0]) >= 2:
        for i in circlesRounded[0, :]:
            centerArr.append(int(i[2]))
            cirDict[i[2]] = (i[0], i[1])
        centerArr.sort(reverse=True)
        if abs(centerArr[0] - centerArr[1]) < (centerArr[0] * 0.1):
            cir1 = cirDict[centerArr[0]]
            cir2 = cirDict[centerArr[1]]

            x = (cir1[0] + cir2[0]) * 0.5
            y = (cir1[1] + cir2[1]) * 0.5

            # cv.circle(img_orig, (int(x), int(y)), 2, (255, 55, 55), 4)

            center = (int(x), int(y))
            return [center, True, centerArr[0]]

        else:
            circle = cirDict[centerArr[0]]
            center = (circle[0], circle[1])
            return [center, False, centerArr[0]]


    elif len(circlesRounded) == 1:
        center = (int(circlesRounded[0][0][0]), int(circlesRounded[0][0][1]))
        return [center, False, circlesRounded[0][0][2]]



def main():
    runSim()


if __name__ == "__main__":
    main()
    cv.waitKey(0)
    exit(0)
