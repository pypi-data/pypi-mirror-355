import numpy as np
import matplotlib.pyplot as plt



def complexCoordinates(testCurve, op = ["", 0], passValue = False,xlim=(-16, 16), ylim=(-16, 16),
                       lowerLimit=-20j, upperLimit=20j, steps=20):
    realCoords = []
    imagCoords = []


    t = np.linspace(lowerLimit, upperLimit, num = steps)
    function = testCurve + t

    if(op[0] == "*"):
        function = function*op[1]

    if(op[0] == "+"):
        function = function + op[1]

    for i in range(-steps + 1, steps - 1):
        realCoords.append(([function.real[i], function.real[i + 1]]))
        imagCoords.append(([function.imag[i], function.imag[i + 1]]))

    return realCoords, imagCoords


def additionWithComplexPoints(testCurve, numAdd, rad = None,steps=20,xlim=(-16, 16), ylim=(-16, 16),
                              lowerLimit=-20j, upperLimit=20j):
    if(rad == None):
        realCoords, imagCoords = complexCoordinates(testCurve, ["+",numAdd])
        for i in range(-steps + 1, steps - 1):
            newRealValue = (realCoords[i][0] + numAdd.real, realCoords[i][1] + numAdd.real)
            realCoords[i] = newRealValue

            newImagValue = (imagCoords[i][0] + numAdd.imag, imagCoords[i][1] + numAdd.imag)
            imagCoords[i] = newImagValue

    else:
        realCoords, imagCoords = complexPolarCoordinates(testCurve, rad, ["+",numAdd])
        for i in range(-steps + 1, steps - 1):
            newRealValue = (realCoords[i][0], realCoords[i][1] )
            realCoords[i] = newRealValue

            newImagValue = (imagCoords[i][0], imagCoords[i][1] )
            imagCoords[i] = newImagValue

    return realCoords, imagCoords

def multiplyWithComplexPoints(testCurve, numMult,rad = None,steps=20,xlim=(-16, 16), ylim=(-16, 16),
                              lowerLimit=-20j, upperLimit=20j):

    if(rad == None):
        realCoords, imagCoords = complexCoordinates(testCurve,["*",numMult])

    else:
        realCoords, imagCoords = complexPolarCoordinates(testCurve,rad,["*",numMult])
        for i in range(-steps + 1, steps - 1):
            newRealValue = (realCoords[i][0] , realCoords[i][1])
            realCoords[i] = newRealValue

            newImagValue = (imagCoords[i][0] , imagCoords[i][1])
            imagCoords[i] = newImagValue

    return realCoords, imagCoords

def inverseWithComplexPoints(testCurve, rad = None,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20):
    realCoords = []
    imagCoords = []

    if(rad ==None):
        t = np.linspace(lowerLimit, upperLimit, num=steps)
        function = (testCurve + t)**-1

        for i in range(-steps + 1, steps - 1):
            realCoords.append(([function.real[i], function.real[i + 1]]))
            imagCoords.append(([function.imag[i], function.imag[i + 1]]))
    else:
        t = np.linspace(0,2*np.pi)
        function = (testCurve + np.e ** (rad * 1j * t))**-1

        for i in range(len(t)-1):
            realCoords.append(([function.real[i], function.real[i + 1]]))
            imagCoords.append(([function.imag[i], function.imag[i + 1]]))

    return realCoords, imagCoords

def graphLineWithTwoPoints(pointOne,pointTwo, range = np.array(range(-10,10)), lineColor = 'black', pointOneColor = "lightseagreen",pointTwoColor = "violet"):
    function = (pointOne+range*(pointTwo-pointOne))
    plt.plot(function.real, function.imag, color=lineColor)

    plt.plot(pointOne.real, pointOne.imag, color=pointOneColor, marker='o')
    plt.plot(pointTwo.real, pointTwo.imag, color=pointTwoColor, marker='o')

def plotOperationsOnComplexCoords(testCurve, function,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):
    plt.subplots()
    TestRealCoords, TestImagCoords = complexCoordinates(testCurve)
    plt.plot(TestRealCoords, TestImagCoords, color=lineColor)

    plt.subplots()
    AddRealCoords, AddImagCoords = additionWithComplexPoints(testCurve, function)
    plt.plot(AddRealCoords, AddImagCoords, color=lineColor)

    plt.subplots()
    MultRealCoords, MultImagCoords = multiplyWithComplexPoints(testCurve, function)
    plt.plot(MultRealCoords, MultImagCoords, color=lineColor)

    plt.subplots()
    InvertRealCoords, InvertImagCoords = inverseWithComplexPoints(testCurve)
    plt.plot(InvertRealCoords, InvertImagCoords, color=lineColor)

def plotTestCurve(testCurve,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):
    plt.subplots()
    TestRealCoords, TestImagCoords = complexCoordinates(testCurve)
    plt.plot(TestRealCoords, TestImagCoords, color=lineColor)

def plotAddCurve(testCurve, function,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):
    plt.subplots()
    AddRealCoords, AddImagCoords = additionWithComplexPoints(testCurve, function)
    plt.plot(AddRealCoords, AddImagCoords, color=lineColor)

def plotMultCurve(testCurve, function,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):
    plt.subplots()
    MultRealCoords, MultImagCoords = multiplyWithComplexPoints(testCurve, function)
    plt.plot(MultRealCoords, MultImagCoords, color=lineColor)

def plotInvertCurve(testCurve,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):
    plt.subplots()
    InvertRealCoords, InvertImagCoords = inverseWithComplexPoints(testCurve)
    plt.plot(InvertRealCoords, InvertImagCoords, color=lineColor)

def complexPolarCoordinates(testCurve, radius,op = ["", 0],xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=0, upperLimit=np.pi*2, steps=20):
    realCoords = []
    imagCoords = []

    t = np.linspace(lowerLimit, upperLimit)
    function = (testCurve+ np.e**(1j*t*radius))

    if (op[0] == "*"):
        function = function * op[1]

    if(op[0] == "+"):
        function = function + op[1]

    for i in range(len(t)-1):
        realCoords.append(([function.real[i], function.real[i + 1]]))
        imagCoords.append(([function.imag[i], function.imag[i + 1]]))

    return realCoords, imagCoords

def plotOperationsOnComplexPolar(center, radious,function,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):
    t = np.linspace(lowerLimit, upperLimit)

    plt.subplots()
    TestRealCoords, TestImagCoords = complexPolarCoordinates(center,radious)
    plt.plot(TestRealCoords, TestImagCoords, color=lineColor)

    plt.subplots()
    AddRealCoords, AddImagCoords = additionWithComplexPoints(center, function, radious,len(t))
    plt.plot(AddRealCoords, AddImagCoords, color=lineColor)

    plt.subplots()
    MultRealCoords, MultImagCoords = multiplyWithComplexPoints(center, function,radious,len(t))
    plt.plot(MultRealCoords, MultImagCoords, color=lineColor)

    plt.subplots()
    InvertRealCoords, InvertImagCoords = inverseWithComplexPoints(center,radious)
    plt.plot(InvertRealCoords, InvertImagCoords, color=lineColor)

def polarPlotTestCurve(center, radious,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):
    t = np.linspace(lowerLimit, upperLimit)
    plt.subplots()
    TestRealCoords, TestImagCoords = complexPolarCoordinates(center, radious)
    plt.plot(TestRealCoords, TestImagCoords, color=lineColor)

def polarPlotAdd(center, radious,function,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):

    t = np.linspace(lowerLimit, upperLimit)
    plt.subplots()
    AddRealCoords, AddImagCoords = additionWithComplexPoints(center, function, radious, len(t))
    plt.plot(AddRealCoords, AddImagCoords, color=lineColor)

def polarPlotMult(center, radious,function,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):
    t = np.linspace(lowerLimit, upperLimit)
    plt.subplots()
    MultRealCoords, MultImagCoords = multiplyWithComplexPoints(center, function,radious,len(t))
    plt.plot(MultRealCoords, MultImagCoords, color=lineColor)

def polarPlotInvert(center, radious,xlim=(-16, 16), ylim=(-16, 16),
                             lowerLimit=-20j, upperLimit=20j, steps=20, lineColor = 'black'):

    plt.subplots()
    InvertRealCoords, InvertImagCoords = inverseWithComplexPoints(center,radious)
    plt.plot(InvertRealCoords, InvertImagCoords, color=lineColor)
