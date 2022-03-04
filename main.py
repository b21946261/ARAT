import time

import cv2 as cv
import numpy as np
from pynput.keyboard import Key, Controller
import pyautogui
import PIL

ellipseCount = 1


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

"""Verdiğin butona verdiğin süre basılı tutar sonra bırakır"""
def pressAndRelease(key, seconds):
    keyboard.press(key)
    time.sleep(seconds)
    keyboard.release(key)

"""Screenshot alır ve cv.imread() ile okur"""
def ssAl():
    myScreenshot = pyautogui.screenshot()
    myScreenshot.save("Images/ss.png")
    img = cv.imread("Images/ss.png")

    try:
        circles = findCircles(img)
        return (circles, img)
    except Exception:  # hiç circle bulamazsa
        pressAndRelease(goForward, 1)
        ssAl()


"""
HoughCircle kullanılarak çember tespiti yapılır ve çember array'i return edilir.
"""
def findCircles(img):
    imgHSV = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    imgGray = cv.cvtColor(imgHSV, cv.COLOR_BGR2GRAY)
    imgBlur = cv.GaussianBlur(imgGray, (7, 7), cv.BORDER_DEFAULT)

    """
    4. parametre çerber merkezleri arasındaki min uzaklığı belirtir. 
    param1 canny edge detection higher olan,param1 in yarısı da lower olan. 
    param2 küçüldükçe false circle bulma ihtimali artar.
    """

    circles = cv.HoughCircles(imgBlur, cv.HOUGH_GRADIENT, 0.9, 200, param1=40, param2=25, minRadius=0, maxRadius=5000)
    circlesRounded = np.uint16(np.around(circles))

    return circlesRounded


"""
Çemberin merkezinin verilen hata payı dahil olmak üzere ekranı ortalayıp ortalamadığını
kontrol eder.
"""
def centered(center):
    centerX = center[0]
    centerY = center[1]

    if abs(screenCenter[0] - centerX) < (screenCenter[0] * 0.1) and\
        abs(screenCenter[1] - centerY) < (screenCenter[1] * 0.05):
        return True

    else:
        return False


"""
Çemberin merkezinin koordinatlarını ekran merkezinin koordinatlarıyla karşılaştırır ve 
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


"""
Çemberin cihaza göre konumuna bağlı olarak çemberi karşısına alacak şekilde hareket eder.
"""
def centeringByLocationEllipse(mode, FTCList):
    center = FTCList[0]
    isEllipse = FTCList[1]
    radius = FTCList[2]


    releaseDelay = 0.3
    """Verilen moda göre sağa ya da sola hareket eder"""
    def modeMovement(mode):
        if mode < 0:  # Sol için mode = -1 girilir
            pressAndRelease(goLeft, releaseDelay)
            pressAndRelease(turnRight, releaseDelay)
        else:         # Sağ için mode = 1 girilir
            pressAndRelease(goRight, releaseDelay)
            pressAndRelease(turnLeft, releaseDelay)

    while isEllipse:
        modeMovement(mode)
        circles = ssAl()[0]
        img = ssAl()[1]
        FTCList = findTargetCircle(img, circles)
        isEllipse = FTCList[1]



"""
Elips bulduğu zaman, çember görene kadar doğru yönde hareket etmeyi sağlar.
Fonksiyonun amacı ekranda çemberi ortalayıp cihazın artık çember görmesini sağlmakatır.
"""
def solveEllipse(cir1, cir2):
    oldRadius = cir2[2]

    # Sola giderken sağa döner.
    keyboard.press(goLeft)
    keyboard.press(turnRight)
    time.sleep(0.5)
    keyboard.release(goLeft)
    time.sleep(0.25)
    keyboard.release(turnRight)

    circles = ssAl()[0]
    img = ssAl()[1]
    FTCList = findTargetCircle(img, circles)
    center = FTCList[0]
    isEllipse = FTCList[1]
    newRadius = float(FTCList[2])

    """
    Önce sola gider.
    if ->   sola gittiğinde elips bulduysa ve dıştaki çemberin yayı küçüldüyse doğru yöndeyiz demektir:
                kendini merkeze göre düzeltip, çember bulana kadar hareket eder.
    elif -> sola gittiğinde bir çember bulduysa ve çemberin yarıçapı elipsin yarıçapından büyükse doğru yöndeyiz demektir,
                çemberin içinden geçme görevini diğer fonksiyonlar halleder.
    
    else -> sol yanlış yön demektir, sağa git:
                sağa gittiğimizde elips bulduysa ve dıştaki çemberin yayı küçüldüyse:
                    kendini merkeze göre düzeltip, çember bulana kadar hareket eder.
                sağa gidince bir çember bulduysa ve çemberin yarıçapı elipsin yarıçapından büyükse,
                    çemberin içinden geçme görevini diğer fonksiyonlar halleder.
    """
    if isEllipse and newRadius < oldRadius:
        centeringByLocationEllipse(-1, FTCList)
        pressAndRelease(goLeft, 0.2)

    elif not isEllipse and (newRadius < oldRadius and abs(float(center[1]) - float(cir2[1])) < float(cir2[1]) * 0.05):
        pressAndRelease(goLeft, 0.2)
        return None
    else:
        keyboard.press(goRight)
        keyboard.press(turnLeft)
        time.sleep(1)
        keyboard.release(goRight)
        time.sleep(0.5)
        keyboard.release(turnLeft)

        try:
            circles = ssAl()[0]
        except TypeError:
            print("hata")
            pressAndRelease(turnRight, 0.5)
            return None

        try:
            img = ssAl()[1]
        except TypeError:
            print("hata")
            pressAndRelease(turnRight, 0.5)
            return None


        FTCList = findTargetCircle(img, circles)
        center = FTCList[0]
        isEllipse = FTCList[1]
        newRadius = FTCList[2]


        if isEllipse and newRadius < oldRadius:
            centeringByLocationEllipse(1, FTCList)
            pressAndRelease(goRight, 0.2)
        elif not isEllipse and (newRadius < oldRadius and abs(float(center[1]) - float(cir2[1])) < float(cir2[1]) * 0.05):
            pressAndRelease(goRight, 0.2)
            return None


    return None


"""
Çemberin merkezini ortalamak için çemberin koordinat sistemindeki konumuna uygun olarak hareket eder.
1. bölge -> Sağ üste gider.
2. bölge -> Sol üste gider.
3. bölge -> Sol alta gider.
4. bölge -> Sağ alta gider.
"""
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


"""
Çemberin merkezi ekranın merkezine belli bir mesafeden uzaksa, çembere düz girebilmek için
cihazın merkeze doğru çevirir.
"""
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




"""
HoughCircle'ın return ettiği circle array'ini yarıçaplarına göre sıralar. Hedef çemberi seçer.
Hedef çemberin merkezinin koordinatlarını, yarıçapını, elips olup olmadığını ve elips ise elipsi oluşturan
iki çemberin çember özelliklerini return eder.

Hedef Çember Nasıl Seçilir?
Hedef çember yarıçapı en büyük olan çember olmalıdır. Bu sebeple return edilen array çemberlerin yarıçapına
göre sıralanır. En büyük iki çemberin boyutları birbirine yakın ise elips görülmüş demektir.
Elips görüldüyse elipsi oluşturan 2 çember solveEllipse() fonksiyona return edilir, işlem orada artık çember
görülene kadar devam eder.
Elips görülmediyse basitçe en büyük çember hedef çember olarak seçilir.
"""
def findTargetCircle(img_orig, circlesRounded):
    # circle array bakıcak ekranın merkezine en yakın ve alanı en büyük olanı hedef belirlemeli

    cir1 = (0, 0)
    cir2 = (0, 0)
    centerArr = []
    cirDict = {}

    if len(circlesRounded[0]) >= 2:
        for i in circlesRounded[0, :]:
            centerArr.append(int(i[2]))
            cirDict[i[2]] = (i[0], i[1], i[2])
        centerArr.sort(reverse=True)
        if abs(centerArr[0] - centerArr[1]) < (centerArr[0] * 0.15):
            cir1 = cirDict[centerArr[0]]
            cir2 = cirDict[centerArr[1]]

            x = (cir1[0] + cir2[0]) * 0.5
            y = (cir1[1] + cir2[1]) * 0.5

            # cv.circle(img_orig, (int(x), int(y)), 2, (255, 55, 55), 4)

            center = (int(x), int(y))
            isEllipse = True
            return [center, isEllipse, centerArr[0], [cir1, cir2]]

        else:
            circle = cirDict[centerArr[0]]
            center = (circle[0], circle[1])
            isEllipse = False
            return [center, isEllipse, centerArr[0]]


    elif len(circlesRounded) == 1:
        center = (int(circlesRounded[0][0][0]), int(circlesRounded[0][0][1]))
        isEllipse = False
        return [center, isEllipse, circlesRounded[0][0][2]]


"""
Bazı ayarlamalar yaptıktan sonra çemberin içinden geçer.
"""
def goThroughCircle(FTCList):
    center = FTCList[0]
    isEllipse = FTCList[1]
    radius = FTCList[2]

    if isEllipse:
        cir1 = FTCList[3][0]
        cir2 = FTCList[3][1]
        solveEllipse(cir1, cir2)
        # print("I saw an ellipse")
        return None

    location = locateCenter(center)
    if radius > 220:
        turning(center)
        centeringByLocation(location, 0.09)
        if centered(center):
            pressAndRelease(goForward, 3)

    else:  # hiç yeterince büyük circle bulamazsa:
        pressAndRelease(goForward, 1)

def scan():
    pass

"""
Bir while döngüsü içinde ss alarak gereken fonksiyonları çağırır.
"""
def runSim():
    time.sleep(3)
    while True:
        try:
            circles = ssAl()[0]
        except TypeError:
            print("hata")
            pressAndRelease(turnRight, 0.5)
            continue

        try:
            img = ssAl()[1]
        except TypeError:
            print("hata")
            pressAndRelease(turnRight, 0.5)
            continue

        FTCList = findTargetCircle(img, circles)

        if FTCList is not None:
            goThroughCircle(FTCList)
        else:
            scan()


def main():
    runSim()


if __name__ == "__main__":
    main()
    cv.waitKey(0)
    exit(0)
