import { Vehicle } from "./vehicle.js";
import { TrafficLight, Lane, Connection } from "./map-objects.js"

export class World {
    constructor(two, sim) {
        this.two = two;
        this.sim = sim;

        //Vehicles
        this.vehicles = [];
        this.activeVehicleIds = [];

        //Map
        this.lanes = {}
        this.trafficLights = {}
        this.connections = []
        this.DrawMap();
    }

    DrawMap() {
        this.DrawGrid()

        //TODO Render all map objects
    }

    MapDataHandler(data) {
        /*
            Static Map Data
        */

        //Add Lanes
        data.lanes.forEach(l => {
            let lane = new Lane(l, this.two);
            this.lanes[lane.id] = lane
            lane.AddToScene();
        });

        //Add Traffic Lights
        data.trafficLights.forEach(tl => {
            let light = new TrafficLight(tl, this.two);
            this.trafficLights[light.id] = light
            light.AddToScene();
        });

        //Add Connections
        data.connections.forEach(con => {
            let connection = new Connection(con, this.two);
            this.connections.push(connection)
            connection.AddToScene();
        });
    }

    DrawGrid() {
        let size = 10000;
        for (let i = -size; i <= size; i += 100) {
            // for (let j = -size; j <= size; j += 100) {
            let x = new Two.Line(-size, i, size, i);
            let y = new Two.Line(i, -size, i, size);
            
            x.stroke = y.stroke = "#6dcff6";

            if (i % 400 === 0) {
                x.stroke = y.stroke = "#6dcff6";
                x.linewidth = y.linewidth = 4;
            } else if (i % 200 === 0) {
                x.stroke = y.stroke = "#6dcff6";
                x.linewidth = y.linewidth = 2;
            }

            if (i !== 0) {
                this.two.add(x);
                this.two.add(y);
            }
        }

        let x = this.two.makeLine(-size, 0, size, 0);
        let y = this.two.makeLine(0, -size, 0, size);
        x.stroke = y.stroke = "#F08080";
        x.linewidth = y.linewidth = 4;
    }

    /*
      Update
        - Add new vehicles to render context
        - Remove vehicles not in latest frame
        - Update position and rotation of existing vehicles

        -TODO render debug information
    */

    DataFrameHandler(data) {
        this.sim.tick = data.tick;

        let activeVehicleIds = []
        
        //TODO Process list of vehicles (and if first frame, map info)
        data.vehicles.forEach(vehicle => {
            activeVehicleIds.push(vehicle.id);
        });

        let newVehicleIds = activeVehicleIds.filter(x => !this.activeVehicleIds.includes(x));

        newVehicleIds.forEach(id => {
            let vehicle = data.vehicles.find(v => v.id === id);
            this.AddVehicle(vehicle);
        });

        let removedVehicles = this.activeVehicleIds.filter(x => !activeVehicleIds.includes(x));

        removedVehicles.forEach(id => {
            let vehicle = this.vehicles.find(v => v.id === id);
            this.RemoveVehicle(vehicle);
        });

        
        let existingVehicleIds = activeVehicleIds.filter(x => this.activeVehicleIds.includes(x));

        existingVehicleIds.forEach(id => {
            let vehicle = this.vehicles.find(v => v.id === id);
            let vehicleData = data.vehicles.find(v => v.id === id);
            vehicle.Update(vehicleData);
        });

        let mapData = data.map;
        mapData.mapUpdates.forEach(update => {
            if (update.type === "trafficLight") {
                let light = this.trafficLights[update.data.id];
                light.Update(update.data.color);
            }
        });
    }

    InterpolateVehicles(dt) {
        this.vehicles.forEach(v => { 
            v.Interpolate(dt);
        });
    }

    AddMapObject(data) {

    }

    AddVehicle(vehicleData) {
        this.activeVehicleIds.push(vehicleData.id);
        let vehicle = new Vehicle(vehicleData, this.two);
        this.vehicles.push(vehicle)

        vehicle.AddToScene();

        // console.log("Adding vehicle ID: " + vehicleData.id);
    }

    RemoveVehicle(vehicle) {
        this.vehicles = this.vehicles.filter(v => v !== vehicle)
        this.activeVehicleIds = this.activeVehicleIds.filter(vid => vid !== vehicle.id)

        vehicle.RemoveFromScene();
    }
}