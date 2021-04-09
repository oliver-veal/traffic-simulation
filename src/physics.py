import math

class Physics():
    def __init__(self):
        self.boundingBoxIds = {}
        self.chunks = {}
        self.CHUNK_SIZE = 4

    def addCollisionBox(self, box):
        self.boundingBoxIds[box.id] = box
        box.chunks = self.calcSpanningChunks(box.corners)
        
        for chunk in box.chunks:
            if chunk[0] not in self.chunks:
                self.chunks[chunk[0]] = {}
            if chunk[1] not in self.chunks[chunk[0]]:
                self.chunks[chunk[0]][chunk[1]] = []

            self.chunks[chunk[0]][chunk[1]].append(box.id)
        
        # print(box.chunks)

    def updateCollisionBox(self, vehicle):
        #TODO Compare list of chunks now vs in previous position.
        #     If different, get list of chunks added and removed and add/remove them.
        vehicle.boundingBox.update(vehicle.position, vehicle.rotation)
        chunks = self.calcSpanningChunks(vehicle.boundingBox.corners)

        currentChunks = set(chunks)
        previousChunks = set(vehicle.boundingBox.chunks)

        addedChunks = currentChunks - previousChunks
        removedChunks = previousChunks - currentChunks

        for chunk in addedChunks:
            # print(f"Added chunk: {chunk}")
            if chunk[0] not in self.chunks:
                self.chunks[chunk[0]] = {}
            if chunk[1] not in self.chunks[chunk[0]]:
                self.chunks[chunk[0]][chunk[1]] = []

            self.chunks[chunk[0]][chunk[1]].append(vehicle.boundingBox.id)

        for chunk in removedChunks:
            # print(f"Removed chunk: {chunk}")
            self.chunks[chunk[0]][chunk[1]].remove(vehicle.boundingBox.id)

        vehicle.boundingBox.chunks = chunks

    def removeCollisionBox(self, box):
        self.boundingBoxIds[box.id] = None

        for chunk in box.chunks:
            self.chunks[chunk[0]][chunk[1]].remove(box.id)

    def doesVehicleCollide(self, v):
        #Get all vehicles not including v in v's chunks
        #Test for collions between all of those vehicles and v
        #If collision found, return ID of vehicle colliding with
        #TODO Return list of all vehicles colliding with (in case of multiple collision happening in the same tick?)
        vehicleIds = set() # Also, only check for collisions with vehicles on the same path, or defined colliding paths. Vehicles will never collide with vehicles not on colliding (intersecting) paths

        for chunk in v.boundingBox.chunks:
            for v1 in self.chunks[chunk[0]][chunk[1]]:
                vehicleIds.add(v1)

        vehicleIds.remove(v.id)
        collisions = set()
        collides = False

        for v1id in vehicleIds:
            bb = self.boundingBoxIds[v1id]
            if bb.intersects(v.boundingBox): # Expensive: minimise calls to this function by culling vehicleId list
                collisions.add(v.simulation.map.vehicles[bb.id])
                collides = True
        if collides:
            collisions.add(v)
        return collisions
    
    def calcSpanningChunks(self, corners):
        """
        Returns a list of tuples of chunk coordinates that are spanned by the chunk-aligned AABB of the rectangle
        """
        chunks = []

        minX = maxX = minY = maxY = None

        for corner in corners:
            chunkX = corner.x / self.CHUNK_SIZE
            chunkY = corner.y / self.CHUNK_SIZE

            chunkMinX = math.floor(chunkX)
            minX = chunkMinX if minX == None or chunkMinX < minX  else minX
            chunkMaxX = math.ceil(chunkX)
            maxX = chunkMaxX if maxX == None or chunkMaxX > maxX else maxX
            chunkMinY = math.floor(chunkY)
            minY = chunkMinY if minY == None or chunkMinY < minY else minY
            chunkMaxY = math.ceil(chunkY)
            maxY = chunkMaxY if maxY == None or chunkMaxY > maxY else maxY

        # print(f"minX: {minX}, maxX: {maxX}, minY: {minY}, maxY: {maxY}")

        for x in range(minX, maxX):
            for y in range(minY, maxY):
                chunks.append((x, y))

        return chunks
        #TODO Remove reference to all chunks BB is contained in