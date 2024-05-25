## Prerequisites
- Python 3.11
- Virtualenv

## Using Virtualenv
```bash
# 1. Create and activate virtualenv
$ python -m venv virtualenv
$ source ./virtualenv/bin/activate (Linux)
$ virtualenv\Scripts\activate (Windows)

# 2. Install dependencies
$ pip install -r requirements.txt

# 3. Run Application
$ python main.py

# 4. Interact with Application
- Click the "Open OSM File" button to open an OSM file 
which is a map data file for a specific region in folder "data"

- Click 2 points on the left-hand side chart that 
indicates to the start point and the target point
you want to travel. The map on the right will mark
those 2 points as anchors for better imagination of
the way you may go through.

- Choose your desired algorithm to find the shortest
path from the start point to the target point on the map.
For Yen algorithm, it will find the top 3 shortest paths.

- Click the "Find Routes" button. The map on the right will
show you the shortest path(s) with respective shortest
distance(s).

- You can compare the result with an online map by clicking
"Find Routes with Online Map" button. A dialog will be shown
with an integrated map that shows the shortest path between
2 selected locations. Please select the "Bicycle" search mode
if the result traveses oneway street. If the result traveses
only two-way streets, please choose the "Foot" search mode.
