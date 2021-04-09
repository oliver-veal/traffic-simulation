from simulation import Simulation, SimVars

import concurrent.futures
import itertools
import time
import traceback
import random

import socketio
import asyncio
import threading
from aiohttp import web

import numpy as np
from smt.applications import EGO
from smt.applications.ego import EGO, Evaluator
from smt.sampling_methods import FullFactorial
from smt.sampling_methods import LHS

from scipy.optimize import differential_evolution, dual_annealing

import sklearn
import matplotlib.pyplot as plt
from matplotlib import colors
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import norm
from smt.surrogate_models import KRG
from smt.sampling_methods import LHS

MULTITHREAD = False
DEBUG = True
USE_EGO = False

def runSimulationFrame(sim):
    num_crashes = 0
    num_complete = 0

    sim.map.clearFrameStateUpdates()
    sim.map.update(sim.tick)
    sim.spawner.spawnVehicles()

    vehicleRemoveList = set()

    for vehicle in sim.map.vehicles.values():
        vehicle.update()
        if (vehicle.outOfBounds()):
            num_complete += 1
            vehicleRemoveList.add(vehicle)
        else:
            sim.physics.updateCollisionBox(vehicle)

    for vehicle in sim.map.vehicles.values():
        if vehicle not in vehicleRemoveList:
            collisions = sim.physics.doesVehicleCollide(vehicle)
            if len(collisions) > 0:
                num_crashes += 1
            for vehicle in collisions:
                vehicleRemoveList.add(vehicle)

    for vehicle in vehicleRemoveList:
        sim.removeVehicle(vehicle)

    return num_crashes, num_complete

def runSimulation(X):
    y = []
    for i in range(len(X[:, 0])):
        spawnRate = X[i, 0]
        speedLimit = X[i, 1]
        laneWidth = X[i, 2]
        clearTime = X[i, 3]

        sim = Simulation(SimVars(spawnRate, speedLimit, laneWidth, clearTime))

        num_crashes = 0
        num_complete = 0

        while sim.tick < TICK_LIMIT:
            frame_num_crashes, frame_num_complete = runSimulationFrame(sim)
            num_crashes += frame_num_crashes
            num_complete += frame_num_complete
            sim.tick += 1

        result = 10 * num_crashes - num_complete
        print(result)
        y.append(result)

    return np.array(y)

def runSimulation1D(X):
    spawnRate = X[0]
    speedLimit = X[1]
    laneWidth = X[2]
    clearTime = X[3]

    sim = Simulation(SimVars(spawnRate, speedLimit, laneWidth, clearTime))

    num_crashes = 0
    num_complete = 0

    while sim.tick < TICK_LIMIT:
        frame_num_crashes, frame_num_complete = runSimulationFrame(sim)
        num_crashes += frame_num_crashes
        num_complete += frame_num_complete
        sim.tick += 1

    result = 10 * num_crashes - num_complete
    print(num_crashes, num_complete)

    return result

class ParallelEvaluator(Evaluator):
    def run(self, fun, x):
        import numpy as np
        from sys import version_info
        import concurrent.futures

        if version_info.major == 2:
            return fun(x)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            print(len(x))
            futures = [
                executor.submit(runSimulation, np.atleast_2d(x[i]))
                for i in range(len(x))
            ]

            return np.array([
                fut.result()[0]
                for fut in concurrent.futures.as_completed(futures)
            ]).reshape(len(x), 1)

TICK_LIMIT = 12000 #10 Minutes

if __name__ == "__main__":
    if DEBUG:
        sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
        app = web.Application()
        sio.attach(app)

        @sio.event
        async def connect(sid, environ):
            sim = Simulation(SimVars(6000, 13.6, 3.5, 2), tick=0)
            await sio.save_session(sid, {"sim": sim})
            await sio.emit('start-sim', sim.map.serialiseStatic())

        @sio.on("next-tick")
        async def nextTick(sid):
            try:
                session = await sio.get_session(sid)
                sim = session["sim"]
                runSimulationFrame(sim)
                sim.tick += 1
                if sim.tick > TICK_LIMIT:
                    await sio.emit('sim-complete', {})
                else:
                    await sio.emit('data-frame', sim.getSerialisedFrame())
            except:
                traceback.print_exc()
                await sio.emit('error', {})

        sio.on("next-tick", nextTick)

        web.run_app(app)

    else:
        start = time.perf_counter()
        print("Starting simulation(s)...")

        # if MULTITHREAD:
        #     # simsToRunList = [Simulation(SimVars(0, 0, 0, 0, 0), tick=0)]# for i in range(100)]
        #     # simsToRun = iter(simsToRunList)
        #     with concurrent.futures.ProcessPoolExecutor() as executor:

        #         # Schedule the first N futures.  We don't want to schedule them all
        #         # at once, to avoid consuming excessive amounts of memory.
        #         futures = {
        #             executor.submit(runSimulationFrame, frame): frame
        #             for frame in itertools.islice(simsToRun, 12)
        #         }

        #         while futures:
        #             # Wait for the next future to complete.
        #             done, _ = concurrent.futures.wait(
        #                 futures, return_when=concurrent.futures.FIRST_COMPLETED
        #             )

        #             for fut in done:
        #                 original_task = futures.pop(fut)

        #                 if original_task.tick < TICK_LIMIT:
        #                     original_task.tick += 1
        #                     simsToRun = itertools.chain(iter([original_task]), simsToRun)

        #                 # print(f"The outcome of {original_task.tick} is {fut.result()}")

        #             # Schedule the next set of futures.  We don't want more than N futures
        #             # in the pool at a time, to keep memory consumption down.

        #             for frame in itertools.islice(simsToRun, len(done)):
        #                 fut = executor.submit(runSimulationFrame, frame)
        #                 futures[fut] = frame

        # else:
        if USE_EGO:
            n_iter = 10
            n_parallel = 10
            xlimits = np.array(
                [[500, 6000], [6.7, 17.8], [2.5, 3.5], [0, 5]]
            )
            criterion = "EI"  #'EI' or 'SBO' or 'UCB'
            qEI = "KB"
            sm = KRG(print_global=False)

            n_doe = 10
            sampling = LHS(xlimits=xlimits)
            xdoe = sampling(n_doe)

            ego = EGO(
                n_iter=n_iter,
                criterion=criterion,
                xdoe=xdoe,
                xlimits=xlimits,
                surrogate=sm,
                n_parallel=n_parallel,
                evaluator=ParallelEvaluator(),
                qEI=qEI,
                random_state=42,
            )

            x_opt, y_opt, _, _, y_data = ego.optimize(fun=runSimulation)
            print("Minimum in x={} with f(x)={:.1f}".format(x_opt, float(y_opt)))

            min_ref = -15
            mini = np.zeros(n_iter)
            for k in range(n_iter):
                mini[k] = np.log(np.abs(np.min(y_data[0 : k + n_doe - 1]) - min_ref))
            x_plot = np.linspace(1, n_iter + 0.5, n_iter)
            u = max(np.floor(max(mini)) + 1, -100)
            l = max(np.floor(min(mini)) - 0.2, -10)
            fig = plt.figure()
            axes = fig.add_axes([0.1, 0.1, 0.8, 0.8])
            axes.plot(x_plot, mini, color="r")
            axes.set_ylim([l, u])
            plt.title("minimum convergence plot", loc="center")
            plt.xlabel("number of iterations")
            plt.ylabel("log of the difference w.r.t the best")
            plt.show()
        else:
            bounds = [(500, 6000), (6.7, 17.8), (2.5, 3.5), (0, 5)]
            ret = differential_evolution(runSimulation1D, bounds, updating='deferred', workers=12)
            # ret = dual_annealing(runSimulation1D, bounds)
            print(ret)
            print(ret.x, ret.fun)


        end = time.perf_counter()
        print(f"Finished in {round(end - start, 2)} seconds.")
