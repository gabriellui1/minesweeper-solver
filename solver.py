import math
import mss
import cv2 as cv
import numpy as np
import pyautogui
from PIL import Image
import time


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def fastcopy(d):
    output = d.copy()
    output = {tile: value for (tile, value) in output.items()}
    return output


def distance(a, b):
    x1, y1 = a
    x2, y2 = b
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def findNeighbours(pos, allTiles):
    neighbours = {neigh for neigh in getNeighbours[pos] if neigh in allTiles}
    return neighbours


def findTiles(tiles, world, race):

    # 0 = no number but safe
    # -1 = unknown
    # 9 = bomb
    # 10 = safe click now

    group = {pos for pos in tiles if world[pos] in race}
    return group


def checkLegal(world):
    bombs = findTiles(world, world, [9])
    numbers = findTiles(world, world, [1, 2, 3, 4, 5])
    unknowns = findTiles(world, world, [-1])
    for tile in numbers:
        neighBombs = findNeighbours(tile, bombs)
        neighUnknowns = findNeighbours(tile, unknowns)
        value = world[tile]
        value -= len(neighBombs)
        if value < 0:
            return False
        if value - len(neighUnknowns) > 0:
            return False
    return True


def fillTiles(world):
    bombs = findTiles(world, world, [9])
    numbers = findTiles(world, world, [1, 2, 3, 4, 5])
    unknownTiles = findTiles(world, world, [-1])

    for tile in numbers:
        neighBombs = findNeighbours(tile, bombs)
        value = world[tile]
        value -= len(neighBombs)

        if value <= 0:
            neighbours = findNeighbours(tile, unknownTiles)
            for neigh in neighbours:
                if neigh != tile:
                    world[neigh] = 10

    return world


def fillBombs(world):
    numbers = findTiles(world, world, [1, 2, 3, 4, 5])
    unknowns = findTiles(world, world, [-1, 9])

    for tile in numbers:
        neigh = findNeighbours(tile, unknowns)
        value = world[tile]
        value -= len(neigh)

        if value >= 0:
            for bomb in neigh:
                world[bomb] = 9

    return world


def completeEasy(world):
    return fillTiles(fillBombs(world))


def completeHard(world):
    oldWorld = fastcopy(world)
    world = completeEasy(world)

    changes = 0
    for pos in world:
        if world[pos] != oldWorld[pos]:
            changes += 1

    # if changes > 10:
    #     return world

    allBlocks = findTiles(world, world, [1, 2, 3, 4, 5])
    unknownTiles = findTiles(world, world, [-1])

    blockNeighbours = set()

    for tile in allBlocks:
        blockNeighbours |= findNeighbours(tile, unknownTiles)

    if len(unknownTiles) < 20:
        blockNeighbours |= unknownTiles

    count = 0

    for tile in blockNeighbours:
        testWorld = fastcopy(world)
        testWorld[tile] = 9
        testWorld = fillTiles(fillBombs(testWorld))

        if not checkLegal(testWorld):
            world[tile] = 10
            continue

        testWorld = fastcopy(world)
        testWorld[tile] = 10
        testWorld = fillTiles(fillBombs(testWorld))

        if not checkLegal(testWorld):
            world[tile] = 9

        count += 1

    world = completeEasy(world)

    return world


def aroundColour(G, V, r=15):
    v1, v2, v3 = V
    g1, g2, g3 = G
    check = 0
    if abs(g1 - v1) < r:
        check += 1
    if abs(g2 - v2) < r:
        check += 1
    if abs(g3 - v3) < r:
        check += 1

    if check == 3:
        return True
    return False


def locateAllImages(mainScreen, template, threshold=0.8):
    result = cv.matchTemplate(mainScreen, template, cv.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    found = []

    for pt in zip(*loc[::-1]):
        found.append(pt)

    return found


def getWorldPos(position):
    x, y = position

    x /= blockWidth
    y /= blockWidth
    x = math.floor(x)
    y = math.floor(y)
    return (x, y)


def getScreenPos(position, offsetX=0, offsetY=0):
    x, y = position

    x *= blockWidth
    y *= blockWidth

    if offsetX != 0 or offsetY != 0:
        x += offsetX
        y += offsetY

    return (round(x), round(y))


def printWorld():
    for i in range(20):
        print("+---" * 24 + "+")
        message = ""
        for j in range(24):
            c = str(world[(j, i)])

            if c == "-1":
                c = " "
            if c == "10":
                c = f"{bcolors.OKGREEN}#{bcolors.ENDC}"
            if c == "9":
                c = f"{bcolors.WARNING}!{bcolors.ENDC}"
            if c in map(str, [1, 2, 3, 4, 5, 6]):
                c = f"{bcolors.OKCYAN}{c}{bcolors.ENDC}"

            message += "| " + c + " "

        message += "|"

        print(message)


knownTiles = set()
alreadyClicked = set()
noMovesTime = -1
turns = 0

sct = mss.mss()

world = {}
for x in range(24):
    for y in range(20):
        world[(x, y)] = -1

getNeighbours = {}
for x in range(24):
    for y in range(20):
        neighs = []

        neighs.append((x - 1, y))
        neighs.append((x + 1, y))
        neighs.append((x, y - 1))
        neighs.append((x, y + 1))

        neighs.append((x + 1, y + 1))
        neighs.append((x - 1, y + 1))
        neighs.append((x + 1, y - 1))
        neighs.append((x - 1, y - 1))

        neighs = [pos for pos in neighs if pos in world]

        getNeighbours[(x, y)] = neighs

# pyautogui.PAUSE = 0
pyautogui.PAUSE = 0
homedir = "/home/bigmac/"

lMine1 = cv.imread(f"{homedir}projects/minesweeper/pics/l_mine1.png", 0)
lMine2 = cv.imread(f"{homedir}projects/minesweeper/pics/l_mine2.png", 0)
lMine3 = cv.imread(f"{homedir}projects/minesweeper/pics/l_mine3.png", 0)
lMine4 = cv.imread(f"{homedir}projects/minesweeper/pics/l_mine4.png", 0)
lMine5 = cv.imread(f"{homedir}projects/minesweeper/pics/l_mine5.png", 0)

dMine1 = cv.imread(f"{homedir}projects/minesweeper/pics/d_mine1.png", 0)
dMine2 = cv.imread(f"{homedir}projects/minesweeper/pics/d_mine2.png", 0)
dMine3 = cv.imread(f"{homedir}projects/minesweeper/pics/d_mine3.png", 0)
dMine4 = cv.imread(f"{homedir}projects/minesweeper/pics/d_mine4.png", 0)
dMine5 = cv.imread(f"{homedir}projects/minesweeper/pics/d_mine5.png", 0)

grey = [(215, 184, 153), (229, 194, 159)]

time.sleep(3)

boardImg = f"{homedir}projects/minesweeper/pics/board.png"
board = pyautogui.locateOnScreen(boardImg, confidence=0.9)

if board:
    TOP = board.top
    LEFT = board.left
    WIDTH = board.width
    HEIGHT = board.height
    pyautogui.click(LEFT+WIDTH/2, TOP+HEIGHT/2)
else:
    LEFT = 650
    TOP = 510
    RIGHT = 1590
    BOTTOM = 1290
    WIDTH = RIGHT - LEFT
    HEIGHT = BOTTOM - TOP

blockWidth = int(WIDTH / 24)
blockMiddle = int(blockWidth / 2)

firstStartTime = time.time()
while True:
    start_time = time.time()

    monitor = {"top": TOP, "left": LEFT, "width": WIDTH, "height": HEIGHT}
    scr = sct.grab(monitor)
    RGBscreen = Image.frombytes("RGB", scr.size, scr.bgra, "raw", "BGRX")

    screen = np.array(scr)
    greyScreen = cv.cvtColor(screen, cv.COLOR_BGR2GRAY)

    dMine1Points = locateAllImages(greyScreen, dMine1, 0.95)
    dMine2Points = locateAllImages(greyScreen, dMine2, 0.95)
    dMine3Points = locateAllImages(greyScreen, dMine3, 0.95)
    dMine4Points = locateAllImages(greyScreen, dMine4, 0.95)
    dMine5Points = locateAllImages(greyScreen, dMine5, 0.95)

    lMine1Points = locateAllImages(greyScreen, lMine1, 0.95)
    lMine2Points = locateAllImages(greyScreen, lMine2, 0.95)
    lMine3Points = locateAllImages(greyScreen, lMine3, 0.95)
    lMine4Points = locateAllImages(greyScreen, lMine4, 0.95)
    lMine5Points = locateAllImages(greyScreen, lMine5, 0.95)

    mines = [
            dMine1Points+lMine1Points,
            dMine2Points+lMine2Points,
            dMine3Points+lMine3Points,
            dMine4Points+lMine4Points,
            dMine5Points+lMine5Points,
    ]

    level = 1
    for levels in mines:
        for position in levels:
            gridPos = getWorldPos(position)
            world[gridPos] = level
        level += 1

    for gridPixel in world:
        pixelPos = getScreenPos(gridPixel, blockMiddle, blockMiddle)
        if world[gridPixel] == -1:
            pixelPos = getScreenPos(gridPixel, blockMiddle, blockMiddle)
            pixelColour = RGBscreen.getpixel(pixelPos)

            for sColour in grey:
                if aroundColour(sColour, pixelColour):
                    world[gridPixel] = 0

    print(f"picture {time.time()-start_time}")

    world = completeHard(world)

    # print(printWorld())
    print(f"calculate {time.time()-start_time}")

    unknowns = 0
    newClicks = 0
    knowns = []
    for tile in world:
        worldPos = getScreenPos(tile, blockMiddle, blockMiddle)

        if world[tile] == -1:
            unknowns += 1
        else:
            knowns.append(world[tile])

        if tile in alreadyClicked:
            continue

        if world[tile] == 10:
            mx, my = (worldPos[0] + LEFT, worldPos[1] + TOP)
            pyautogui.click(mx, my, button="left")
            alreadyClicked.add(tile)
            world[tile] = -1
            newClicks += 1
        elif world[tile] == 9:  # don't flag
            mx, my = (worldPos[0] + LEFT, worldPos[1] + TOP)
            pyautogui.click(mx, my, button="right")
            alreadyClicked.add(tile)

    print(f"click {time.time()-start_time}")

    if unknowns == 0 and time.time() - firstStartTime > 2:
        print("I win")
        break
