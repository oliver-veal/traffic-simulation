Author: Oliver Veal

Working on python version 3.8.5
Python required packages:

    For debug server:
    - aiohttp
    - python-socketio

    For running optimisation methods:
    - numpy
    - sklearn
    - scipy
    - cython
    - SMT (https://smt.readthedocs.io/en/latest/_src_docs/getting_started.html)

Main file: main.py

3 variables to change behaviour of program (lines 30-32 main.py):
    - MULTITHREAD (Deprecated)
    - DEBUG: Run the debug server over socketio. Enters debug mode.
    - USE_EGO: Switch between EGO and DE optimisers

Performance:
    - EGO runs in ~20 mins using 12 threads on an i7 8700k @ 5.0Ghz

Debug mode (Very cool, worth playing with!):
    - Set DEBUG to True in main.py
    - This will launch a web server on port 8080 of localhost
    - To view the debugger, open index.html in a web server
        (I use live-server for development, or http-server, both work. Easy to get and use with NPM)
        (https://www.npmjs.com/package/live-server)
    - If the python backend is running (make sure they don't run on the same port), the debug client will connect
      and start rendering the junction layout
    - Press SPACE to play/pause the simulation.
    - Press R when paused to move forward frame by frame.
    - If you want a video demo of this instead, or have any questions at all feel free to email me at any time 
      at oliver.veal18@imperial.ac.uk