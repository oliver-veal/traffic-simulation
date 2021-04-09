from utils import Rect, Vector
import utils
import json
import math
import random
from map import LightState
from pathing import CircleSection

class BoundingBox:
    def __init__(self, id, position, rotation, width, length, wheelBase):
        self.id = id
        self.position = position
        self.rotation = rotation
        self.width = width
        self.length = length
        self.wheelBase = wheelBase
        self.calcCorners()

    def update(self, position, rotation):
        self.position = position
        self.rotation = rotation
        self.calcCorners()

    def calcCorners(self):
        corners = []

        xoffset = Vector(self.length / 2 - ((self.length - self.wheelBase) / 2), 0)

        corners.append((Vector(self.length / 2, self.width / 2) + xoffset).rotate(math.degrees(self.rotation)) + self.position)
        corners.append((Vector(-self.length / 2, self.width / 2) + xoffset).rotate(math.degrees(self.rotation)) + self.position)
        corners.append((Vector(-self.length / 2, -self.width / 2) + xoffset).rotate(math.degrees(self.rotation)) + self.position)
        corners.append((Vector(self.length / 2, -self.width / 2) + xoffset).rotate(math.degrees(self.rotation)) + self.position)

        self.corners = corners

    def intersects(self, b):
        #Rectangle collision detection (SAT Separating Axis Theorem)
        for rect in [self, b]:
            for i1 in range(len(rect.corners)):
                i2 = (i1 + 1) % len(rect.corners)
                p1 = rect.corners[i1]
                p2 = rect.corners[i2]

                normal = Vector(p2.y - p1.y, p1.x - p2.x)

                minA = maxA = minB = maxB = None
                
                for p in self.corners:
                    projected = normal.x * p.x + normal.y * p.y
                    if (minA == None or projected < minA):
                        minA = projected
                    if (maxA == None or projected > maxA):
                        maxA = projected

                for p in b.corners:
                    projected = normal.x * p.x + normal.y * p.y
                    if (minB == None or projected < minB):
                        minB = projected
                    if (maxB == None or projected > maxB):
                        maxB = projected

                if (maxA < minB or maxB < minA):
                    return False

        return True

class VehicleConfig:
    def __init__(self, name = "default"):
        self.name = name
        with open("./vehicles/" + name + ".json") as cfg:
            data = json.load(cfg)
            self.width = data["width"]
            self.length = data["length"]
            self.wheelBase = data["wheelBase"]
            self.speedLimit = data["speedLimit"]
            self.maxAcceleration = data["maxAcceleration"]
            self.maxBraking = data["maxBraking"]
            self.minBraking = data["minBraking"]
            self.maxSteeringAngle = data["maxSteeringAngle"]

class Vehicle:
    def __init__(self, id, simulation, pathId, laneId, name="default", initialSpeed=0, idealAcceleration=0.7):
        self.id = id
        self.type = name
        self.simulation = simulation
        self.config = VehicleConfig(name)
        self.distanceToFront = self.config.length - ((self.config.length - self.config.wheelBase) / 2)

        self.pathId = pathId
        path = self.simulation.map.getPath(pathId)
        path.vehicleOrder.append(self.id)
        self.laneId = laneId
        lane = self.simulation.map.entryLanes[self.laneId]
        lane.vehicleOrder.append(self.id)
        self.removedFromLaneOrder = False
        # print(f"Added vehicle {id} to vehicleOrder {path.vehicleOrder} in path id {path.id}")
        self.distance = 0

        # self.steeringAngle = 0

        position, rotation = path.interpolate(self.distance)

        self.acceleration = 0
        self.position = position
        self.rotation = rotation
        self.velocity = Vector(0, 0)
        self.speed = initialSpeed
        # self.angularVelocity = 0

        self.boundingBox = BoundingBox(self.id, self.position, self.rotation, self.config.width, self.config.length, self.config.wheelBase)

        self.trafficLightDistance = path.sections[0].length - self.distanceToFront
        self.trafficLightState = LightState.red
        self.trafficLightStateObserved = LightState.red
        self.trafficLightUpdatedTick = 0
        self.simulation.map.subscribeToTrafficLightUpdate(self)

        speedLimit = min(self.config.speedLimit, simulation.simVars.speedLimit)
        self.speedLimit =  speedLimit + random.randint(-math.floor(speedLimit / 10), math.floor(speedLimit / 5)) #TODO simulation variable + driver variation
        self.turnStartsDistance = -1
        self.turnEndsDistance = -1
        self.turnSpeedLimit = -1
        self.maxG = 0.8 #TODO driver variation (sim var?)
        idealAcceleration = (random.randint(0, 30) / 10) + 0.6
        self.maxAcceleration = self.config.maxAcceleration * idealAcceleration

        distanceTravelled = 0
        for section in path.sections:
            if isinstance(section, CircleSection):
                self.turnStartsDistance = distanceTravelled
                self.turnEndsDistance = distanceTravelled + section.length
                self.turnSpeedLimit = math.sqrt(9.8 * self.maxG * section.radius)
                break
            else:
                distanceTravelled += section.length
                

        self.reactionTime = math.floor(200 / simulation.delta)
        self.MAX_REACTION_TICKS = 20
        self.history = []
    
    #TODO Change initial orientation

    def update(self): # Run vehicle AI and update it's position (or run task like remove from sim after successful journey, detect collision etc)
        # self.steeringAngle = 0#math.radians(self.config.maxSteeringAngle)
        delta = self.simulation.delta / 1000
        tick = self.simulation.tick
        
        trafficLightAcceleration = self.maxAcceleration
        speedLimitAcceleration = self.maxAcceleration
        rearEndAcceleration = self.maxAcceleration

        # --- Traffic lights ---
        #Is the car behind the traffic light?
        behindLight = self.distance < self.trafficLightDistance

        # What state is the light observed as (factoring in reaction time)
        if tick - self.trafficLightUpdatedTick == self.reactionTime:
            self.trafficLightStateObserved = self.trafficLightState

        if behindLight and (self.trafficLightStateObserved == LightState.amber or self.trafficLightStateObserved == LightState.red):
            #Calculate maximum possible acceleration value such that, if accelerating at a constant rate until the light, the vehicle will stop at the light
            s = self.trafficLightDistance - self.distance
            if s < utils.getStoppingDistance(self.speed, self.config.minBraking) or s < 1:
                v2 = 0
                u2 = self.speed * self.speed
                a = (v2 - u2) / (2 * s)
                if a > self.config.maxBraking:
                    trafficLightAcceleration = a

        #Speed limits
        currentSpeedLimit = self.speedLimit

        if self.turnStartsDistance > 0:
            if self.distance > self.turnStartsDistance and self.distance < self.turnEndsDistance:
                currentSpeedLimit = self.turnSpeedLimit
            
            if self.distance < self.turnStartsDistance:
                s = self.turnStartsDistance - self.distance
                if s < utils.getStoppingDistance(self.speed, self.config.minBraking):
                    v2 = self.turnSpeedLimit * self.turnSpeedLimit
                    u2 = self.speed * self.speed
                    a = (v2 - u2) / (2 * s)
                    if a < self.config.maxBraking:
                        a = self.config.maxBraking
                    speedLimitAcceleration = a
        
        #Avoid rear-ends
        path = self.simulation.map.getPath(self.pathId)

        # for path in self.simulation.map.entryLanes[self.laneId]:
            #Get all vehicle ahead of this one by distance, but not after turn if not on same path

        nvids = [self.simulation.map.entryLanes[self.laneId].getNextVehicleInQueue(self.id), path.getNextVehicleInQueue(self.id)]
        rearEndAcceleration = self.config.maxAcceleration
        # nvid = path.getNextVehicleInQueue(self.id)
        for nvid in nvids:
            if nvid is not None:
                nv = self.simulation.map.vehicles[nvid]
                i = len(nv.history) - 1 if len(nv.history) <= self.reactionTime else self.reactionTime
                nvdistance, nvspeed, nvaccel = nv.history[i]

                acceleration = self.config.maxAcceleration

                gap = (nvdistance - self.distance) - (self.config.length + 1 + (0.5 * self.speed))#TODO 2 second rule goes here (lower limit of 1m)
                # gap = (nvdistance - self.distance) - (self.config.length + 1)
                if gap < 0:
                    acceleration = self.config.maxBraking
                else:
                    if nvspeed < self.speed:
                        if nvaccel <= 0:
                            t = 0 if nvaccel == 0 else (-(nvspeed) / nvaccel)
                            s = nvspeed * t + 0.5 * nvaccel * t * t
                            s += gap
                            if s < utils.getStoppingDistance(self.speed, self.config.minBraking):
                                v2 = nvspeed * nvspeed if nvaccel == 0 else 0
                                u2 = self.speed * self.speed
                                acceleration = (v2 - u2) / (2 * s)
                                if acceleration < self.config.maxBraking:
                                    acceleration = self.config.maxBraking
                        elif nvaccel > 0:
                            #Two body pursuit
                            a = nvaccel
                            b = nvspeed + self.speed
                            c = 2 * (gap - nvaccel)

                            d = b**2 - 4 * a * c

                            if d > 0:
                                t = 0
                                if d == 0:
                                    t = (-b+math.sqrt(b**2-4*a*c))/2*a
                                else:
                                    t1 = (-b+math.sqrt((b**2)-(4*(a*c))))/(2*a)
                                    t2 = (-b-math.sqrt((b**2)-(4*(a*c))))/(2*a)
                                    if t1 > 0:
                                        t = t1
                                    if t2 > 0:
                                        t = t2

                                if t != 0:
                                    num = gap + (nvspeed * t) + (0.5 * nvaccel * t**2) -  (self.speed * t)
                                    denom = 0.5 * t**2
                                
                                    acceleration = num / denom
                                    if acceleration < self.config.maxBraking:
                                        acceleration = self.config.maxBraking

                if acceleration < rearEndAcceleration:
                    rearEndAcceleration = acceleration

        self.acceleration = min(trafficLightAcceleration, speedLimitAcceleration, rearEndAcceleration)
        if abs(self.acceleration) < 0.001:
            self.acceleration = 0
        if abs(self.speed) < 0.001:
            self.speed = 0

        self.speed += self.acceleration * delta
        if self.speed < 0:
            self.speed = 0

        #Speed limiter (straight have map speed limit, circle sections have max turning G speed limit)
        if self.speed > currentSpeedLimit:
            self.speed = currentSpeedLimit
            self.acceleration = 0

        # self.angularVelocity = (math.tan(self.steeringAngle) / self.config.wheelBase) * self.speed
        # self.rotation = self.rotation + (self.angularVelocity * delta)

        # self.velocity = Vector(math.cos(self.rotation) * self.speed, math.sin(self.rotation) * self.speed)

        # self.position = self.position + (self.velocity * delta)

        self.distance += self.speed * delta

        if self.distance > path.distanceUntilAfterTurn and path.distanceUntilAfterTurn >= 0 and not self.removedFromLaneOrder:
            self.simulation.map.entryLanes[self.laneId].vehicleOrder.remove(self.id)
            self.removedFromLaneOrder = True

        #Store last 1000ms worth of ticks of a, v and s so other vehicles can use those values for reaction times
        self.history.insert(0, (self.distance, self.speed, self.acceleration))
        if len(self.history) > self.MAX_REACTION_TICKS:
            self.history.pop()
        
        position, rotation = path.interpolate(self.distance)
        self.position = position
        self.rotation = rotation

        # if len(self.history) > 1:
        #     self.velocity = (self.history[1][0] - self.position) / delta

    def outOfBounds(self):
        return self.distance >= self.simulation.map.getPath(self.pathId).length