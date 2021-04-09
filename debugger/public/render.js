import { World } from "./world.js"
import { SocketClient } from "./socket-client.js"
import { RenderContext } from "./render-context.js"
import { KeyboardEvents } from "./keyboard-events.js"

let sim = {
    play: false,
    error: false,
    tick: 0,
    frameTime: 50,
    timeSinceLastFrame: 0
}

let keyboardEvents = new KeyboardEvents();

/*
  Render Context
    - Contains two.js instance
    - Handles ZUI
*/

let renderContext = new RenderContext(document.body);

/*
  World
    - Stores list of current vehicles
    - Stores and renders current map
*/

let world = new World(renderContext.two, sim);

/*
  Socket Client
    - Listens for incoming data packets
    - Can request the next data frame
*/

let socketClient = new SocketClient(world.DataFrameHandler, world, world.MapDataHandler, world, sim);

/*
  Vehicle
    - Stores ID, position, type
    - Has functions for rendering the vehicle to a passed Render Context
*/

//TODO

renderContext.two.bind("update", (frameCount, dt) => {
    if (socketClient.handshake && !socketClient.complete && sim.play && !sim.error) {
        sim.timeSinceLastFrame += dt;

        if (sim.timeSinceLastFrame >= sim.frameTime) {
            socketClient.RequestNextDataFrame();
            sim.timeSinceLastFrame = 0;
        } else { //Interpolate based on position and velocity (eventually angular velocity)
            // world.InterpolateVehicles(dt/1000);
        }
    }
}).play();

keyboardEvents.AddHandler(" ", up => {
    if (!up)
        sim.play = !sim.play;
});

keyboardEvents.AddHandler("r", up => {
    if (!up && socketClient.handshake && !socketClient.complete && !sim.play && !sim.error)
        socketClient.RequestNextDataFrame();
});