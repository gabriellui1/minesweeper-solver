import math
import mss
import cv2 as cv
import numpy as np
import keyboard
import pyautogui
from PIL import Image
import time


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
    numbers = findTiles(world, world, [1, 2, 3, 4, 5, 6])
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
    numbers = findTiles(world, world, [1, 2, 3, 4, 5, 6])
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
    numbers = findTiles(world, world, [1, 2, 3, 4, 5, 6])
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
    world = completeEasy(world)

    allBlocks = findTiles(world, world, [1, 2, 3, 4, 5, 6])
    unknownTiles = findTiles(world, world, [-1])

    blockNeighbours = set()

    for tile in allBlocks:
        blockNeighbours |= findNeighbours(tile, unknownTiles)

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
                c = "#"
            message += "| " + c + " "

        message += "|"

        print(message)


keyboard.wait("q")

firstStartTime = time.time()


knownTiles = set()

alreadyClicked = set()

noMovesTime = -1

turns = 0

sct = mss.mss()

LEFT = 570
TOP = 375

RIGHT = 1650
BOTTOM = 1320

WIDTH = RIGHT - LEFT  # 1080
HEIGHT = BOTTOM - TOP  # 900

blockWidth = int(WIDTH / 24)  # 45

# width 24
# height 20

# top left 570, 420
# top right 1650, 420
# bottom left 570, 1320
# bottom right 1650, 1320

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

pyautogui.PAUSE = 0
# pyautogui.PAUSE = 0.1

mine1 = cv.imread(r"C:\Users\boneb\well\auto\minesweeper\pics\mine1.png", 0)
mine2 = cv.imread(r"C:\Users\boneb\well\auto\minesweeper\pics\mine2.png", 0)
mine3 = cv.imread(r"C:\Users\boneb\well\auto\minesweeper\pics\mine3.png", 0)
mine4 = cv.imread(r"C:\Users\boneb\well\auto\minesweeper\pics\mine4.png", 0)
mine5 = cv.imread(r"C:\Users\boneb\well\auto\minesweeper\pics\mine5.png", 0)


grey = [(215, 184, 153), (229, 194, 159)]

while True:

    start_time = time.time()

    monitor = {"top": TOP, "left": LEFT, "width": WIDTH, "height": HEIGHT}
    scr = sct.grab(monitor)
    RGBscreen = Image.frombytes("RGB", scr.size, scr.bgra, "raw", "BGRX")

    screen = np.array(scr)
    greyScreen = cv.cvtColor(screen, cv.COLOR_BGR2GRAY)

    mine1Points = locateAllImages(greyScreen, mine1, 0.9)
    mine2Points = locateAllImages(greyScreen, mine2, 0.9)
    mine3Points = locateAllImages(greyScreen, mine3, 0.8)
    mine4Points = locateAllImages(greyScreen, mine4, 0.9)
    mine5Points = locateAllImages(greyScreen, mine5, 0.8)

    mines = [
        mine1Points,
        mine2Points,
        mine3Points,
        mine4Points,
        mine5Points,
    ]

    level = 1
    for levels in mines:
        for position in levels:
            gridPos = getWorldPos(position)
            world[gridPos] = level
        level += 1

    for gridPixel in world:
        pixelPos = getScreenPos(gridPixel, 22, 22)
        if world[gridPixel] == -1:
            pixelPos = getScreenPos(gridPixel, 22, 22)
            pixelColour = RGBscreen.getpixel(pixelPos)

            for sColour in grey:
                if aroundColour(sColour, pixelColour):
                    world[gridPixel] = 0

    world = completeHard(world)

    unknowns = 0
    newClicks = 0
    knowns = []
    for tile in world:
        worldPos = getScreenPos(tile, 22, 22)

        if world[tile] == -1:
            unknowns += 1
        else:
            knowns.append(world[tile])

        if tile in alreadyClicked:
            continue

        if world[tile] == 10:
            mx, my = (worldPos[0] + LEFT, worldPos[1] + TOP)

            pyautogui.click(mx, my, button="left")

            world[tile] = -1
            alreadyClicked.add(tile)
            newClicks += 1

    if unknowns == 0 and time.time() - firstStartTime > 2:
        print("I win")
        break

    print(time.time() - start_time)
