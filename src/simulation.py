from map import Map
from spawner import Spawner
from physics import Physics

import json

class SimVars:
    def __init__(self, spawnRate, speedLimit, laneWidth, clearTime):
        self.spawnRate = spawnRate #500 - 6000
        self.speedLimit = speedLimit #6.7 - 17.8 DONE
        self.laneWidth = laneWidth #2.5 - 3.5
        self.junctionSpacing = 8 * laneWidth#15 - 25
        self.clearTime = clearTime #0 - 5

class Simulation:
    def __init__(self, simVars, delta = 50, tick = 0):
        self.delta = delta
        self.simVars = simVars
        self.map = Map(simVars)
        self.spawner = Spawner(self)
        self.tick = tick

        self.physics = Physics()

    def addVehicle(self, vehicle):
        self.map.vehicles[vehicle.id] = vehicle
        self.physics.addCollisionBox(vehicle.boundingBox)

    def removeVehicle(self, vehicle): # Be careful not to remove before loop finishes (will cause errors for other vehicles)
        del self.map.vehicles[vehicle.id]
        self.map.unsubscribeFromLightUpdate(vehicle)
        self.physics.removeCollisionBox(vehicle.boundingBox)
        self.map.getPath(vehicle.pathId).vehicleOrder.remove(vehicle.id)
        try:
            self.map.entryLanes[vehicle.laneId].vehicleOrder.remove(vehicle.id)
        except ValueError:
            pass

    def getSerialisedFrame(self): #Take current state of simulation and return an object describing the state
        return {
            "tick": self.tick,
            "vehicles": [{
                "id": v.id,
                "type": v.type,
                "position": {
                    "x": v.position.x,
                    "y": v.position.y
                },
                "velocity": {
                    "x": v.velocity.x,
                    "y": v.velocity.y
                },
                "length": v.config.length,
                "width": v.config.width,
                "wheelBase": v.config.wheelBase,
                "rotation": v.rotation,
                "angularVelocity": 0,#v.angularVelocity,
                "corners": [{"x": c.x, "y": c.y} for c in v.boundingBox.corners]
            } for v in self.map.vehicles.values()],
            "map": self.map.serialiseDynamic()
        }