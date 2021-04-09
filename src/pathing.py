import utils
from utils import Vector
import math

class Path:
    def __init__(self, id, sections, trafficLightId):
        self.id = id
        self.sections = sections
        self.trafficLightId = trafficLightId

        self.vehicleOrder = []

        self.length = 0
        self.distanceUntilAfterTurn = -1

        for section in sections:
            self.length += section.length
            if isinstance(section, CircleSection):
                self.distanceUntilAfterTurn = self.length

    def getNextVehicleInQueue(self, vehicleId):
        vehicleIndex = self.vehicleOrder.index(vehicleId)
        if vehicleIndex < 0:
            raise Exception(f"VehicleID {vehicleId} not in queue.")

        if vehicleIndex == 0:
            return None

        return self.vehicleOrder[vehicleIndex - 1]

    def debug_getPoints(self):
        points = []

        for section in self.sections:
            points.extend(section.points)
            points.pop()

        points.append(self.sections[-1].points[-1])

        return points

    def interpolate(self, distance):
        pathDistance = 0
        sectionIndex = 0

        while pathDistance <= distance:
            if sectionIndex > len(self.sections) - 1:
                return pathDistance, 0
            if distance - pathDistance > self.sections[sectionIndex].length:
                pathDistance += self.sections[sectionIndex].length
                sectionIndex += 1
            else:
                return self.sections[sectionIndex].interpolate(distance - pathDistance)

class PathSection:
    def __init__(self):
        self.points = []
        self.length = 0

    def interpolate(self, distance):
        return 0, 0

class StraightSection(PathSection):
    def __init__(self, start, end):
        super().__init__()
        self.start = start
        self.end = end

        self.points.extend([start, end])

        self.pathVector = self.end - self.start
        self.orientation = self.pathVector.argument()
        self.unitVector = self.pathVector.normalize()
        self.length = self.pathVector.norm()

    def interpolate(self, distance):
        if distance < 0:
            raise ValueError(f"Distance {distance} is less than 0.")
        if distance > self.length:
            raise ValueError(f"Distance {distance} is greater than the length of the path {self.length}.")
        
        return self.start + (self.unitVector * distance), self.orientation

def generateTurnSection(start, startOrientation, end, endOrientation, clockwise, bikeLane):
    turnRadius = 4 if bikeLane else (9.5 if clockwise else 6)

    v1 = Vector(1, 0).rotate(startOrientation) + start
    v2 = Vector(1, 0).rotate(endOrientation) + end #.rotate(180)

    intersect = utils.intersectLines(start, v1, end, v2)

    if not intersect:
        raise Exception("CurvedSection: No intersection point between lines")

    # Normal to v1 pointing in direction of 2nd point
    # If left turn, rotate -90, if right turn, rotate +90
    normalTurn = 90 if clockwise else -90
    v1Normal = Vector(1, 0).rotate(startOrientation + normalTurn) * turnRadius
    v2Normal = Vector(1, 0).rotate(endOrientation + normalTurn) * turnRadius

    v1NormalInv = v1Normal * -1
    v2NormalInv = v2Normal * -1

    v1inner = v1 + v1Normal
    v2inner = v2 + v2Normal

    circleCenter = utils.intersectLines(start + v1Normal, v1inner, end + v2Normal, v2inner)

    if not circleCenter:
        raise Exception("TurnSection: No intersection point between lines")

    entryStop = circleCenter - v1Normal
    exitStart = circleCenter - v2Normal

    delta = v1NormalInv.angleBetween(v2NormalInv)

    if clockwise:
        delta *= -1

    return [
        StraightSection(start, entryStop),
        CircleSection(circleCenter, turnRadius, v1NormalInv, delta),
        StraightSection(exitStart, end)
    ]

class CircleSection(PathSection):
    def __init__(self, center, radius, startVector, maxDelta):
        super().__init__()
        self.center = center
        self.radius = radius
        self.startVector = startVector
        self.maxDelta = maxDelta

        self.length = abs(math.pi * 2 * radius * (maxDelta / (2 * math.pi)))

        POINTS = 20
        self.points = [self.startVector.rotate(-math.degrees(self.maxDelta * (i / POINTS))) + self.center for i in range(POINTS + 2)]

    def interpolate(self, distance):
        if distance < 0:
            raise ValueError(f"Distance {distance} is less than 0.")
        if distance > self.length:
            raise ValueError(f"Distance {distance} is greater than the length of the path {self.length}.")
        
        delta = self.maxDelta * (distance / self.length) * -1

        position = self.startVector.rotate(math.degrees(delta)) + self.center
        normalTurn = 90 if self.maxDelta > 0 else -90
        return position, self.startVector.argument() + delta + math.radians(normalTurn + 180)