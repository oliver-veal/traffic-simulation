export class SocketClient {
    constructor(dataFrameHandler, dfhandleContext, mapDataHandler, maphandleContext, sim) {
        let socket = io("http://localhost:8080");
        this.socket = socket;

        this.dataFrameHandler = dataFrameHandler;
        this.dfhandleContext = dfhandleContext;

        this.mapDataHandler = mapDataHandler;
        this.maphandleContext = maphandleContext;

        this.handshake = false;
        this.complete = false;

        socket.on('start-sim', data => {
            this.handshake = true;
            this.mapDataHandler.call(this.maphandleContext, data)
        });

        socket.on('data-frame', data => {
            this.dataFrameHandler.call(this.dfhandleContext, data)
        });

        socket.on('sim-complete', msg => {
            this.complete = true;
            console.log("Sim Complete!");
        });

        socket.on('error', data => {
            sim.error = true;
            console.log("Simulation error!");
        });
    }

    RequestNextDataFrame() {
        this.socket.emit("next-tick");
    }
}