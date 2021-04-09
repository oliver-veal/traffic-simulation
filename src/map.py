import json
import random
import math
from enum import Enum
from utils import Vector
import pathing
from pathing import Path, StraightSection

class MapConfig:
    def __init__(self, name = "default"):
        self.name = name

        # Parse the json file in /maps with the name name.json
        # Store results in some data structure

        with open("./maps/" + name + ".json") as cfg:
            self.data = json.load(cfg)

class SpawnPoint:
    def __init__(self, position, orientation):
        self.position = position
        self.orientation = orientation

class Lane:
    def __init__(self, id, vehicleType, width, length, position, orientation, type):
        self.id = id
        self.vehicleType = vehicleType
        self.width = width
        self.length = length
        self.position = position
        self.orientation = orientation
        self.type = type

        self.connectsTo = None
        self.leftTurn = None
        self.rightTurn = None

        self.paths = {}
        self.vehicleOrder = []

        entryPoint = Vector(-length / 2, 0)
        self.entryPoint = entryPoint.rotate(orientation) + position
        exitPoint = Vector(length / 2, 0)
        self.exitPoint = exitPoint.rotate(orientation) + position

        self.trafficLight = None

    def getNextVehicleInQueue(self, vehicleId):
        try:
            vehicleIndex = self.vehicleOrder.index(vehicleId)

            if vehicleIndex == 0:
                return None

            return self.vehicleOrder[vehicleIndex - 1]
        except ValueError:
            return None
            # raise ValueError(f"VehicleID {vehicleId} not in lane.")


class LightState:
    green = 1
    amber = 2
    red = 3

class SimpleLightCycle:
    def __init__(self, majors, minors, params=None):
        params = {} if params == None else params
        self.MAJOR_GREEN = 15 if "MAJOR_GREEN" not in params else params["MAJOR_GREEN"]
        self.MINOR_GREEN = 8 if "MINOR_GREEN" not in params else params["MINOR_GREEN"]
        self.AMBER_CLEARANCE = 3 if "AMBER_CLEARANCE" not in params else params["AMBER_CLEARANCE"]
        self.RED_CLEARANCE = 2 if "RED_CLEARANCE" not in params else params["RED_CLEARANCE"]
        self.SIM_DELTA = (50 / 1000) if "SIM_DELTA" not in params else (params["SIM_DELTA"] / 1000)

        self.majors = majors
        self.numMajors = len(majors)
        self.minors = minors
        self.numMinors = len(minors)

        self.timingIndex = 0
        self.lastUpdateTick = 0 #So the first state change is always sent on tick 1

        # Pregenerate list of light timings? (Assume all are red by default)

        self.timingArray = []
        #     ([("majorGroup1Ids", "green")], 15),
        #     ([("majorGroup1Ids", "amber")], 3),
        #     ([("majorGroup1Ids", "red")], 2),

        #     ([("minorGroup1Ids", "green")], 8),
        #     ([("minorGroup1Ids", "amber")], 3),
        #     ([("minorGroup1Ids", "red")], 3),

        #     ([("minorGroup2Ids", "green")], 8),
        #     ([("minorGroup2Ids", "amber")], 3),
        #     ([("minorGroup2Ids", "red")], 3),
        # ]

        # Run all major groups, then all minor groups
        self.timingArray.append((([], LightState.green), -1))
        for groupId in sorted(majors.keys()):
            self.timingArray.append(((majors[groupId], LightState.green), self.MAJOR_GREEN))
            self.timingArray.append(((majors[groupId], LightState.amber), self.AMBER_CLEARANCE))
            self.timingArray.append(((majors[groupId], LightState.red), self.RED_CLEARANCE))

        for groupId in sorted(minors.keys()):
            self.timingArray.append(((minors[groupId], LightState.green), self.MINOR_GREEN))
            self.timingArray.append(((minors[groupId], LightState.amber), self.AMBER_CLEARANCE))
            self.timingArray.append(((minors[groupId], LightState.red), self.RED_CLEARANCE))

    def getLightUpdates(self, map, tick):
        stateUpdates = []
        currentStageTime = self.timingArray[self.timingIndex][1]
        if (tick - self.lastUpdateTick) * self.SIM_DELTA > currentStageTime:
            self.lastUpdateTick = tick
            self.timingIndex = (self.timingIndex + 1) % len(self.timingArray)
            
            state = self.timingArray[self.timingIndex][0]
            
            for lightId in state[0]:
                map.entryLanes[lightId].trafficLight.color = state[1]
                stateUpdates.append({
                    "type": "trafficLight",
                    "data": {
                        "id": lightId,
                        "color": state[1]
                    }
                })

        return stateUpdates

class TrafficLight:
    def __init__(self, id, position, orientation, width):
        #Static
        self.id = id
        self.position = position
        self.orientation = orientation
        self.width = width

        #Dynamic
        self.color = LightState.red

class Map:
    def __init__(self, simVars):
        self.config = MapConfig()
        self.vehicles = {}

        self.frameStateUpdates = []

        self.entryLanes = {}
        self.exitLanes = {}
        self.latestPathId = 0

        self.majorSignalGroups = {}
        self.minorSignalGroups = {}

        self.lightUpdateSubscriptions = {}

        for l in self.config.data["lanes"]:
            id = l["id"]
            vehicleType = l["vehicle"]
            # width = l["width"]
            width = l["width"] * simVars.laneWidth
            length = l["length"]
            # position = Vector(l["position"]["x"], l["position"]["y"])
            orientation = l["orientation"]
            laneType = l["type"]

            if orientation == 90 or orientation == -90:
                spacing = simVars.junctionSpacing / 2 if l["position"]["y"] > 0 else -(simVars.junctionSpacing / 2)
                if vehicleType == "bicycle":
                    addWidth = l["numLanesFromCenter"] * width * 3 + (width / 2)
                else:
                    addWidth = l["numLanesFromCenter"] * width + (width / 2)
                if l["position"]["x"] < 0:
                    addWidth *= -1
                position = Vector(addWidth, spacing + l["position"]["y"])
            else:
                spacing = simVars.junctionSpacing / 2  + simVars.laneWidth if l["position"]["x"] > 0 else -(simVars.junctionSpacing / 2  + simVars.laneWidth)
                if vehicleType == "bicycle":
                    addWidth = l["numLanesFromCenter"] * width * 3 + (width / 2)
                else:
                    addWidth = l["numLanesFromCenter"] * width + (width / 2)
                if l["position"]["y"] < 0:
                    addWidth *= -1
                position = Vector(spacing + l["position"]["x"], addWidth)
            

            lane = Lane(id, vehicleType, width, length, position, orientation, laneType)

            if laneType == "ENTRY":
                #Generate traffic light
                light = TrafficLight(lane.id, lane.exitPoint, lane.orientation, lane.width)
                lane.trafficLight = light

                if "majorSignalGroup" in l:
                    groupId = l["majorSignalGroup"]
                    if groupId not in self.majorSignalGroups:
                        self.majorSignalGroups[groupId] = []
                    self.majorSignalGroups[groupId].append(light.id)
                if "minorSignalGroup" in l:
                    groupId = l["minorSignalGroup"]
                    if groupId not in self.minorSignalGroups:
                        self.minorSignalGroups[groupId] = []
                    self.minorSignalGroups[groupId].append(light.id)
                
                if "connectsTo" in l:
                    lane.connectsTo = l["connectsTo"]
                if "leftTurn" in l:
                    lane.leftTurn = l["leftTurn"]
                if "rightTurn" in l:
                    lane.rightTurn = l["rightTurn"]

                self.entryLanes[id] = lane
            elif laneType == "EXIT":
                self.exitLanes[id] = lane

        # customParams = {
        #     "MAJOR_GREEN": 1,
        #     "MINOR_GREEN": 1,
        #     "AMBER_CLEARANCE": 1,
        #     "RED_CLEARANCE": 1
        # }

        self.lightController = SimpleLightCycle(self.majorSignalGroups, self.minorSignalGroups, params={"RED_CLEARANCE": simVars.clearTime})

        # Now that we know all lanes and connections, precompute paths
        for lane in self.entryLanes.values():
            bikeLane = lane.vehicleType == "bicycle"
            if lane.connectsTo is not None:
                lane.paths["connectsTo"] = self.computePath(lane, self.exitLanes[lane.connectsTo], bikeLane=bikeLane)
            if lane.leftTurn is not None:
                lane.paths["left"] = self.computePath(lane, self.exitLanes[lane.leftTurn], False, bikeLane=bikeLane)
            if lane.rightTurn is not None:
                lane.paths["right"] = self.computePath(lane, self.exitLanes[lane.rightTurn], True, bikeLane=bikeLane)

    def getPath(self, pathId):
        for lane in self.entryLanes.values():
            for path in lane.paths.values():
                if path.id == pathId:
                    return path
    
    def computePath(self, entryLane, exitLane, clockwise=None, bikeLane=False):
        sections = []

        sections.append(StraightSection(entryLane.entryPoint, entryLane.exitPoint))

        if clockwise is None:
            sections.append(StraightSection(entryLane.exitPoint, exitLane.entryPoint))
        else:
            sections.extend(pathing.generateTurnSection(entryLane.exitPoint, entryLane.orientation, exitLane.entryPoint, exitLane.orientation, clockwise, bikeLane))

        sections.append(StraightSection(exitLane.entryPoint, exitLane.exitPoint))

        return Path(self.genPathId(), sections, entryLane.id)

    def genPathId(self):
        self.latestPathId += 1
        return self.latestPathId
    
    def clearFrameStateUpdates(self):
        self.frameStateUpdates = []
    
    def update(self, tick): #Update traffic light colors
        lightUpdates = self.lightController.getLightUpdates(self, tick)
        for update in lightUpdates:
            lightId = update["data"]["id"]
            if lightId in self.lightUpdateSubscriptions:
                for vehicleId in self.lightUpdateSubscriptions[lightId]:
                    vehicle = self.vehicles[vehicleId]
                    vehicle.trafficLightState = update["data"]["color"]
                    vehicle.trafficLightUpdatedTick = tick
        self.frameStateUpdates.extend(lightUpdates)

    def subscribeToTrafficLightUpdate(self, vehicle):
        lightId = self.getPath(vehicle.pathId).trafficLightId
        if lightId not in self.lightUpdateSubscriptions:
            self.lightUpdateSubscriptions[lightId] = []

        self.lightUpdateSubscriptions[lightId].append(vehicle.id)
        vehicle.trafficLightStateObserved = self.entryLanes[lightId].trafficLight.color
        vehicle.trafficLightState = self.entryLanes[lightId].trafficLight.color
        vehicle.trafficLightUpdatedTick = 0

    def unsubscribeFromLightUpdate(self, vehicle):
        self.lightUpdateSubscriptions[self.getPath(vehicle.pathId).trafficLightId].remove(vehicle.id)

    def updateVehicleLightState(self, vehicle, color, tick):
        vehicle.trafficLightState = color
        vehicle.trafficLightUpdatedTick = tick

    def serialiseStatic(self): #Return a JSON object of map objects
        staticData = self.config.data

        lanes = []
        lanes.extend(self.entryLanes.values())
        lanes.extend(self.exitLanes.values())

        staticData["lanes"] = [{
            "id": lane.id,
            "position": {
                "x": lane.position.x,
                "y": lane.position.y
            },
            "orientation": lane.orientation,
            "type": lane.type,
            "width": lane.width,
            "length": lane.length,
        } for lane in lanes]

        staticData["trafficLights"] = [{
            "id": lane.trafficLight.id,
            "position": {
                "x": lane.trafficLight.position.x,
                "y": lane.trafficLight.position.y
            },
            "orientation": lane.orientation + 90,
            "color": lane.trafficLight.color,
            "width": lane.width
        } for (laneid, lane) in self.entryLanes.items()]

        staticData["connections"] = []

        for lane in self.entryLanes.values():
            for path in lane.paths.values():
                staticData["connections"].append({
                    "points": [{
                        "x": point.x,
                        "y": point.y
                    } for point in path.debug_getPoints()],
                    "width": lane.width
                })

        return self.config.data

    def serialiseDynamic(self):
        return {
            "mapUpdates": [{
                "type": update["type"],
                "data": update["data"]
            } for update in self.frameStateUpdates]
        }