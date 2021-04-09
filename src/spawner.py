import random
import utils
import math
from vehicle import Vehicle

class Spawner:
    def __init__(self, sim):
        self.sim = sim
        ticksPerHour = math.floor((1000 / sim.delta) * 3600)
        self.rate = math.floor(ticksPerHour / sim.simVars.spawnRate)
        self.lastVehicleId = 0
        self.lastVehicleSpawnedFrame = 0


    def spawnVehicles(self):
        shuffledLanes = list(self.sim.map.entryLanes.keys()).copy()
        random.shuffle(shuffledLanes)

        if self.sim.tick % self.rate == 0 and self.sim.tick > 0:
            for laneId in shuffledLanes:
                lane = self.sim.map.entryLanes[laneId]

                path = random.choice(list(lane.paths.values()))
                vehicle = Vehicle(self.getVehicleId(), self.sim, path.id, laneId, name=lane.vehicleType, initialSpeed=self.sim.simVars.speedLimit) #Set initial speed to the speed of the vehicle in front (if it is within the car's stopping distance (to avoid funny spawning collisions))
                self.sim.addVehicle(vehicle)

                nvid = path.getNextVehicleInQueue(vehicle.id)
                if nvid is not None:
                    nv = self.sim.map.vehicles[nvid]
                    # if nv.distance - vehicle.distance - (vehicle.config.length + 1) < utils.getStoppingDistance(utils.mphToMs(30), vehicle.config.maxBraking):
                        # print(f"setting speed to {nv.speed}")
                    vehicle.speed = nv.speed

                collisions = self.sim.physics.doesVehicleCollide(vehicle)
                if len(collisions) > 0:
                    self.lastVehicleId -= 1
                    self.sim.removeVehicle(vehicle)
                else:
                    return

    def getVehicleId(self):
        self.lastVehicleId += 1
        return self.lastVehicleId

