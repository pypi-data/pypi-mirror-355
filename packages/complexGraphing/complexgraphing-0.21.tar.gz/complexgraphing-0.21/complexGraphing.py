import numpy as np


def complexCoordinates(testCurve, function='-', xlim=(-16, 16), ylim=(-16, 16),
                       lowerLimit=-20j, upperLimit=20j, steps=20):
    realCoords = []
    imagCoords = []

    print(function)
    if (function.any() == '-'):
        t = np.linspace(lowerLimit.imag, upperLimit.imag, steps)
        function = testCurve + t

    for i in range(-steps + 1, steps - 1):
        realCoords.append([function.real[i], function.real[i + 1]])
        imagCoords.append(([function.imag[i], function.imag[i + 1]]))

    return realCoords, imagCoords


def additionWithComplexPoints(testCurve, numAdd, xlim=(-16, 16), ylim=(-16, 16),
                              lowerLimit=-20j, upperLimit=20j, steps=20):
    t = np.linspace(lowerLimit.imag, upperLimit.imag, steps)
    function = testCurve + t + numAdd

    complexCoordinates(testCurve, function, xlim, ylim, lowerLimit, upperLimit, steps)


def multiplyWithComplexPoints(testCurve, numMult, xlim=(-16, 16), ylim=(-16, 16),
                              lowerLimit=-20j, upperLimit=20j, steps=20):
    t = np.linspace(lowerLimit.imag, upperLimit.imag, steps)
    function = (testCurve + t) * numMult

    complexCoordinates(testCurve, function, xlim, ylim, lowerLimit, upperLimit, steps)


def inverseWithComplexPoints(testCurve, function='-', xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20):
    t = np.linspace(lowerLimit.imag, upperLimit.imag, steps)
    function = (testCurve + t) ** -1

    complexCoordinates(testCurve, function, xlim, ylim, lowerLimit, upperLimit, steps)
