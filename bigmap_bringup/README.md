# bigmap_bringup

**BigMap on a robot, real or simulated.** It launches EasyNav with the BigMap maps manager
(`easynav_bigmap_maps_manager/BigMapMapsManager`, in this repository: a NavMap that is fine around the
robot and coarse far away, made of tiles at levels of detail), the NavMap of the place (outdoors, made
from its DEM), and RViz; and it has the complete parameter files of the use cases. The application knows nothing of Gazebo: the robot, real or
simulated, gives the sensors, the odometry and the TF. To use the plugin on your own robot, without this
package, see the README of `easynav_bigmap_maps_manager`: its parameters, how it works and what it
costs.

**BigMap in any place, in one launch.** `bigmap_geo.launch.py` starts the simulation of a real place
(`easynav_playground_geo`: the Gazebo world of its coordinates, with the Summit XL) and then the
application on that very world:

```bash
ros2 launch bigmap_bringup bigmap_geo.launch.py lat:=46.0207 lon:=7.7491 radius:=300                # terrain (Zermatt)
ros2 launch bigmap_bringup bigmap_geo.launch.py lat:=40.4168 lon:=-3.7038 radius:=250 world:=area   # + buildings, walls, trees
```

See [In any place: `bigmap_geo.launch.py`](#in-any-place-bigmap_geolaunchpy).

**The packages and how they meet.**

| Package | What it is | Talks to the others through |
|---|---|---|
| `easynav_bigmap_maps_manager` ([BigMap](https://github.com/EasyNavigation/BigMap)) | the plugin: a NavMap file cut into tiles at levels of detail, assembled around the robot; the obstacles the sensors see, remembered and forgotten | its parameters `maps_manager_node.bigmap.*`, the NavState (`map.navmap`), topics `/maps_manager_node/bigmap/*` |
| `bigmap_bringup` (this package) | the application: `launch/bigmap.launch.py`, `launch/bigmap_geo.launch.py`, `config/params_*.yaml`, `maps/`, `rviz/`, and the Python module `bigmap_bringup.dem` (how the DEM and the NavMap of a place are made) | runs `navmap_gis_tool` (the DEM generator, package `navmap_tools`) and EasyNav's `system_main` with one parameter file; nothing of the plugin is linked |
| `easynav_playground_geo` ([easynav_playgrounds](https://github.com/EasyNavigation/easynav_playgrounds)) | the simulation of any real place: the Gazebo world of its coordinates (terrain, optionally buildings, walls and trees), with the Summit XL | writes `~/.ros/easynav_geo/last_world.yaml` (the place and the mesh of its world), which the application reads with `sim:=true` |
| `navmap_tools` ([NavMap](https://github.com/EasyNavigation/NavMap)) | outdoors: `navmap_gis_tool --dem-out --navmap-out` makes the DEM and, from it, the NavMap of the place (`dem_generator.navmap_file`), from a place or from the mesh of a simulated world, then exits | the DEM cache file (the UKF's origin) and the NavMap file |

The launch only chooses the parameter file and starts the processes; every behaviour of the plugin is in
that file (see [Parameters](#parameters)).

The indoor simulations of the use cases below (the parking garage, the large warehouse, a world of
your own) and the article's campaigns use `easynav_playground_bigmap`, the earlier simulation package
of the BigMap workspace, which is not published: with `sim:=true` the application also follows it
(`~/.ros/bigmap/sim/sim.yaml`), whichever of the two simulations was launched last.

## Use cases: `config:=`

`config:=<name>` is `config/params_<name>.yaml`; `params_file:=<file>` is any complete parameter file instead.

| `config:=` | Map | Terrain | Localization | Meant for |
|---|---|---|---|---|
| `outdoor` (default) | NavMap | made from the DEM of a place (IGN, or Copernicus elsewhere) at every launch | GPS + odometry + IMU (UKF) | an outdoor ground robot; the Summit in simulation |
| `indoor` | NavMap | your NavMap file (floors over each other, ramps) | external: your own localization gives `map -> odom` | an indoor real robot (a template to fill) |
| `parking_garage` | NavMap | the two-floor garage (`maps/parking_garage.navmap`) | AMCL on its Bonxai map | simulation |
| `large_warehouse` | NavMap | `large_warehouse_world` (700 x 450 m, one floor): the NavMap of the article's runs | AMCL | simulation |
| `two_floors` | NavMap | two floors, one start | AMCL | simulation |

The files have the same sections, names and order (see [Parameters](#parameters)).

## Build (ROS 2 Rolling)

This package is part of the [BigMap](https://github.com/EasyNavigation/BigMap) repository, which also
has the maps manager and the EasyNav plugins it is tested with; `bigmap.repos` brings the rest (EasyNav,
NavMap with `navmap_gis_tool --dem-out --navmap-out` and the tools BigMap is built on, and
`easynav_playgrounds` with `easynav_playground_geo`). One distro per shell, and always a shell where only Rolling is sourced (a
binary built with Rolling does not run under Jazzy: `undefined symbol ... rclcpp ...`):

```bash
mkdir -p <ws>/src && cd <ws>/src
git clone https://github.com/EasyNavigation/BigMap.git && cd ..
vcs import src < src/BigMap/bigmap.repos
source /opt/ros/rolling/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-up-to bigmap_bringup \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PROJECT_navmap_rviz_plugin_INCLUDE=$PWD/src/BigMap/bigmap_bringup/cmake/rolling_rviz_qt.cmake
source install/setup.bash
```

With `--symlink-install` the YAMLs, launch files and `maps/` are links to `src`: edit them without
rebuilding (the module `bigmap_bringup.dem` too). `package.xml` declares what the launch runs
(EasyNav's `system_main`, the plugins the YAMLs name, `easynav_playground_geo`), so `--packages-up-to`
builds them and rosdep brings the system ones.
`rolling_rviz_qt.cmake` is a workaround for the Rolling packages released for Ubuntu 24.04 (no
longer updated): their `rviz_common` is built against Qt5 but exports a bare `Qt5` dependency and
looks for Qt6 first. It only affects `navmap_rviz_plugin` and edits no third-party code; it is not
needed on a consistent Rolling (Ubuntu 26.04). Do not run two stacks on the same `ROS_DOMAIN_ID` /
`GZ_PARTITION`.

`maps/` is 180 MB: the NavMaps and the point clouds of the indoor use cases (AMCL localizes on the
clouds).

## Launch the application

```bash
# a real robot, outdoors: the DEM and the NavMap of its place, then EasyNav with the UKF origin there
ros2 launch bigmap_bringup bigmap.launch.py config:=outdoor lat:=40.4168 lon:=-3.7038 radius:=400
# a real robot, indoors: your NavMap is in the file (bigmap.navmap_path_file)
ros2 launch bigmap_bringup bigmap.launch.py params_file:=<yours.yaml>
# a simulated robot: start a simulation first, then follow it (or bigmap_geo.launch.py: both)
ros2 launch easynav_playground_geo easynav_geo.launch.yaml lat:=46.0207 lon:=7.7491 radius:=300
ros2 launch bigmap_bringup bigmap.launch.py config:=outdoor sim:=true
```

| Argument | Default | What it is |
|---|---|---|
| `config` | `outdoor` | the use case: `config/params_<config>.yaml` |
| `params_file` | `''` | a complete parameter file instead |
| `sim` | `false` | `true`: follow the last simulation launched: the mesh of the world of `easynav_playground_geo` (`~/.ros/easynav_geo/last_world.yaml`) or what `easynav_playground_bigmap` wrote (`~/.ros/bigmap/sim/sim.yaml`); `use_sim_time: true`, and EasyNav waits for the robot's transform (`tools/wait_for_robot.py`) |
| `area_holes` | `false` | `sim:=true` with a world of `easynav_playground_geo`: `true`, its buildings, walls and tree trunks are holes of the NavMap over the ground (their exact footprints); `false`, blocks of the DEM, left out of the NavMap as too steep (`dem_generator.max_slope_deg`) |
| `lat`, `lon`, `radius` | `''` (the file's place) | the place of the map (the DEM): centre (= the origin of the map and of the UKF) and half-side, m. Outside Spain the heights are Copernicus 30 m and the imagery Esri |
| `use_synthetic_terrain` | `''` (the file's) | `true`: offline, fake imagery and terrain |
| `navmap` | `''` | outdoors: load this NavMap instead of making one from the DEM of a place (see below) |
| `use_sim_time` | `''` | `true` / `false` for EasyNav and RViz; empty: `true` with `sim:=true`, `false` with `sim:=false`: the clock is the launch's decision, not the file's |
| `wait_for_robot` | `''` | `true`: EasyNav starts when the robot's `odom -> base_footprint` exists (default with `sim:=true`); `false`: right away |
| `rviz`, `rviz_config` | `true`, `''` | RViz2 and its configuration (`rviz/bigmap.rviz`) |

What the launch does with a file that has a `dem_generator` block (outdoors): `navmap_gis_tool`
downloads the DEM (elevation and satellite imagery) once and caches it where the file says
(`dem_generator.cache_file`), writes from it the NavMap of the place (`dem_generator.navmap_file`: two
NavCels per `grid_resolution` cell, the vertex colours of the imagery, without the ground steeper than
`max_slope_deg` and without the holes) and exits; then EasyNav (`system_main`) starts with the file and an
overrides file (`~/.ros/bigmap/easynav_overrides.yaml`: the full path of that NavMap for the maps manager
and, when the file has a GPS localizer, the UKF origin, the lat, lon and altitude of the DEM's origin) and
RViz2 opens. A file without that block (indoors) has its NavMap in `bigmap.package` +
`bigmap.navmap_path_file`: nothing is generated. Refused with a message, before anything starts: a place
(`lat:=`...) for a file without `dem_generator`, `navmap:=` for a file that has its own map, `lat:=`
without `lon:=`.

With `sim:=true` the DEM (and so the NavMap) is made from what the simulation wrote, on top of the file's `dem_generator`
block, so the map of the robot and the world it is in are of the same place: for a world of
`easynav_playground_geo`, its mesh (`navmap.stl`: the terrain, and the buildings, walls and trunks of
an area) rasterised with the origin of the world; for `easynav_playground_bigmap`, its place or the
mesh of its area. The launch says which simulation it follows and when it was written. `lat:= lon:=`
given on top of it win. The application never writes a world.

## In any place: `bigmap_geo.launch.py`

```bash
ros2 launch bigmap_bringup bigmap_geo.launch.py lat:=46.0207 lon:=7.7491 radius:=300                # terrain
ros2 launch bigmap_bringup bigmap_geo.launch.py lat:=40.4168 lon:=-3.7038 radius:=250 world:=area   # + buildings, walls, trees
ros2 launch bigmap_bringup bigmap_geo.launch.py world:=area area_holes:=true gui:=false
```

It is the two launches above in one: first `easynav_playground_geo` makes the world of the place
(once: it is kept in `~/.ros/easynav_geo/worlds/`) and starts Gazebo with the Summit XL in it; then
`bigmap.launch.py sim:=true` makes the DEM and the NavMap of that world and starts EasyNav, when the robot is up,
and RViz. Send goals from RViz.

| Argument | Default | What it is |
|---|---|---|
| `world`, `lat`, `lon`, `radius`, `trees`, `walls`, `roof`, `lidar`, `spawn_x`, `spawn_y`, `spawn_z`, `gui`, `gpu` | those of `easynav_playground_geo` (the URJC campus at Fuenlabrada, 300 m, `terrain`) | the world: see the README of `easynav_playground_geo` |
| `config` | `outdoor` | the use case; it must make its map from a DEM (a `dem_generator` block): the others are refused with a message |
| `params_file` | `''` | a complete parameter file instead (with a `dem_generator` block) |
| `area_holes` | `false` | `world:=area`: the buildings, walls and trunks as holes of the map (see above) |
| `rviz`, `rviz_config` | `true`, `''` | RViz2 and its configuration |

The place of the map is the world's: `lat`, `lon`, `radius` go to the simulation only, and the
application takes the world's mesh, origin and elevation from `last_world.yaml`. Outside Spain the
map's colours are Esri's, as the world's imagery.

## Outdoor

Notes for `config:=outdoor`:
- Keep `gps_origin.altitude: 0.0` (z = 0 at the origin, where the robot spawns).
- The UKF runs in 3D with the wheel odometry's vz = 0 as an anchor; its lat/lon/altitude origin
  comes from the generated overrides file, not from `params_outdoor.yaml` (with `navmap:=` only if
  the map has a georeferenced `<map>.yaml`; otherwise the file's `ukf.*_origin` are used and the
  launch says so).
- `grid_resolution` (1 m) is the NavMap's cell and `bigmap.cell_size.min`. The NavMap is made again
  at every launch from the cached DEM (a 1 km square at 1 m: 2 M NavCels, from which BigMap builds
  its tiles at start).
- `use_synthetic_terrain:=true|false` overrides the file's value only when given.
- GPS localization drifts a few metres over tens of metres of path in simulation.
- Elevation: `elevation_source: ign` (Spain only, 5 m, LiDAR-derived, free, no key) or
  `copernicus30` (the whole world, 30 m, free, no key: how to use it outside Spain is in the
  README of `easynav_bigmap_maps_manager`). Imagery: `imagery.source: ign` (PNOA orthophoto, Spain) or `xyz`
  (a tile server of your choice). Outdoors needs no account or API key. The elevation is
  requested every `elevation_resolution` and interpolated (bicubic) to `grid_resolution`: small NavCels give a smooth surface, not new real detail.
- In simulation the map is made of the mesh of the simulated world: see
  [In any place](#in-any-place-bigmap_geolaunchpy) and the README of `easynav_playground_geo`.

## Indoor, multi-level

```bash
# real robot, no Gazebo: everything is in config/params_indoor.yaml (use_sim_time false, external
# localization; set bigmap.navmap_path_file there, or copy the file and pass params_file:=<yours>)
ros2 launch bigmap_bringup bigmap.launch.py config:=indoor

# simulation: the playground's parking garage (params_parking_garage.yaml has the maps manager, the
# NavMap, the Bonxai map, AMCL and its start pose; the playground spawns the robot there)
ros2 launch easynav_playground_bigmap easynav_bigmap_scenario.launch.yaml scenario:=parking_garage
ros2 launch bigmap_bringup bigmap.launch.py config:=parking_garage sim:=true
```

**Where the values are.** Every use case has its own complete parameter file and the launch loads
that file as it is: there is no hidden override file indoors. The simulation starts Gazebo and the
robot (at `localizer_node.amcl.initial_pose`, which it reads from the file); the application starts
EasyNav and RViz with the NavMap the file names: `bigmap.package: bigmap_bringup` +
`bigmap.navmap_path_file: maps/<scenario>.navmap` (relative to that package's share directory, as the
Bonxai map's `package` + `bonxai_path_file`; with `--symlink-install` it is the one in `src`). Nothing
is copied or generated: indoors there is no overrides file, everything is in the YAML. Written to
`~/.ros/bigmap`: only the GPS maps, DEM caches and areas. Refused with a message, before anything
starts: `navmap:=` indoors (edit the YAML), a place (`lat:=`...) for a file without a DEM.
`spawn_x:=` / `spawn_y:=` of the simulation move only the Gazebo robot (AMCL starts at the file's `initial_pose`).
Set the robot's lidar topic, `robot_geometry` (0.5 m for the
Summit XL: 0.7 m does not fit a 2 m ramp between curbs) and the levels of detail in the file.

Floors over each other are the NavMap's own: BigMap cuts the map into tiles and simplifies them
(`navmap::simplify`), which keeps the map's topology (no hole closes, no wall opens, floors over each
other are not stitched together, however coarse), so the same parameters serve one floor and several.
The obstacle heights (`obstacle_min_height` .. `obstacle_max_height`, 0.2 .. 1.2 m indoors) are above
the surface under each point, so the floor above is out of reach.

**Choosing a floor in RViz.** The goal tool takes the first surface under the mouse, i.e. the
topmost one. Publish the goal by hand, with the floor's z, to choose another:
`ros2 topic pub --once /goal_pose geometry_msgs/msg/PoseStamped '{header: {frame_id: map}, pose:
{position: {x: -1.8, y: -4.1, z: 2.35}, orientation: {w: 1.0}}}'`.

## Point clouds to a NavMap: `pointcloud_to_navmap` (tens of millions of points)

The NavMap that bigmap starts from is the finest one it will ever use: bigmap simplifies it (its
finest level within `cell_size.min / 2`, the coarsest up to `cell_size.max`) and details it again near
the robot. `pointcloud_to_navmap` (package `navmap_tools`, in NavMap) makes it
from one or several `.pcd` files, however big:

```bash
ros2 run navmap_tools pointcloud_to_navmap --input cloud.pcd --output map.navmap --resolution 1.0 \
    --min-clearance 1.0 --recenter [--origin lat,lon,alt] [--crop x0,y0,x1,y1] [--zmax 2.5]
```

- **`--resolution`** is the finest NavCel: use `bigmap.cell_size.min` of your parameter file. Finer
  only costs memory and time at start (the finest level is simplified within `cell_size.min / 2`) and
  coarser throws detail away.
- **Big clouds.** ascii and binary files are streamed (a block of 1 M points at a time, never the whole
  file) and clouds above 5 M points are reduced by voxel first (`--voxel`, default resolution / 4:
  a voxel is replaced by the centroid of its points, so planes stay planes), so memory follows the
  *extent* of the map, not the number of points. `binary_compressed` cannot be streamed and is loaded
  whole by PCL. Several `--input` are joined.
- **Meshing** is `navmap_ros::from_points`: XY cells, one vertex per floor in a cell (several floors,
  `--min-clearance` = the free height that separates two of them; it must be BELOW the headroom of the
  lowest ramp: in the garage (floors 2.2 m apart, slabs 0.4 m) 2.0 cuts the ramp up to the top floor
  and that floor is left as a separate piece, 1.0-1.5 keeps all of them joined. The tool prints the
  heights where it found surface), surfaces never steeper than
  `--max-slope-deg` (walls stay as gaps), holes up to `--max-hole-area` interpolated.
- **Holes** (`--fill-holes`, 2 m): a SLAM cloud has no floor points where it did not see the
  floor, the mesher cannot invent them, and the ground the robot could drive over is cut into
  pieces. A stretch of empty cells up to that wide between two bits of the same floor, in a row
  or a column, gets floor points at the height in between and the cloud is meshed again, so the new
  triangles join the old ones (a straight border does not grow; 0 leaves the holes). On a SLAM map
  of two floors (346 000 points 0.2 m apart) this added 22 % of walkable area and made the largest
  connected piece 30 % bigger. What the cloud lacks entirely (a ramp nobody scanned, a room) stays
  missing: scan it again. `--max-hole-area` (1 m^2) is the mesher's own interpolation and does
  little by itself. `--min-surface-area` (m^2) drops the specks that are not connected to anything.
- **Resolution the data supports.** The tool prints "this data holds X m": below that, a cell has
  fewer than 3 points and holes and rough ground follow. A cloud with points 0.2 m apart holds
  0.37 m: use `--resolution 0.4`, not 0.3. The slope limit (`--max-slope-deg`) and `--max-dz` are
  not what cuts a SLAM floor: they changed nothing in the tests.
- **Colour** from the `rgb` field (or `r g b`): each vertex takes the colour of the nearest point of
  its own height, not of the floor below or above.
- **It tells you if the data holds the resolution**: the median points per cell and the finest
  resolution with at least 3 per cell (`WARNING` otherwise; a cloud that is already a grid of that
  resolution is fine with 1).
- **Output**: `map.navmap` and `map.yaml` (where the map's (0, 0, 0) is: `--origin` makes it
  georeferenced; `--recenter` shifts the map so that its centre is (0, 0) and writes the shift as
  `offset_x` / `offset_y`). Keep the cloud in local coordinates: a PCD stores float32, which is 0.5 m
  of precision at UTM northings.

Measured with the 2024 PNOA-LiDAR of the campus (4 sheets, 32 M points with colour, 2 x 2 km, 1 m,
Release): 84 s and 5.9 GB peak, 4.2 M vertices / 7.2 M triangles (93 MB). A cloud with *everything* (canopies, cars, roofs)
gives a 1 m map with a lot of steep surface and gaps: that is what the data holds, so give it the
ground or a height window (`--zmax`) if you want drivable terrain only.

## A simulated robot on your own map

You have a NavMap and the point cloud (and its Bonxai map) from a SLAM with a real robot, and want
a simulated robot to drive in it. Gazebo needs a world of that building: BigMap does not make one
(a `map_to_world` tool existed and was removed, its walls were not good enough), so bring your own
(the mesh of the building, or a world modelled from the plan) in the same frame as the NavMap.

Then a parameter file for a simulation with AMCL: copy `config/params_parking_garage.yaml` and set
`bonxai.package` + `bonxai_path_file` (the Bonxai plugin needs the cloud inside a package's
`share/`: `maps/` of this package works), `bigmap.package` + `navmap_path_file`, and
`localizer_node.amcl.initial_pose.x / y` (where the robot starts). Launch the simulation with the world and the
height of the floor you start on, and the application with the file (the NavMap's height there, plus ~0.2 m):

```bash
ros2 launch easynav_playground_bigmap bigmap_sim.launch.py world_file:=<your world.sdf> \
    spawn_x:=<x> spawn_y:=<y> spawn_z:=0.1
ros2 launch bigmap_bringup bigmap.launch.py params_file:=<yours.yaml> sim:=true
```

**Where to start.** AMCL starts from x, y only and takes the topmost floor under that point, so
where two floors are stacked Gazebo (the floor `spawn_z` says) and AMCL (the upper one) can
disagree on the level. Start where there is one floor. `config/params_two_floors.yaml` starts at (-6.8, -7.8), a single floor at
z = -0.12 with walls all around (3.7 m to the nearest, so the lidar has something to match):
there Gazebo and AMCL agree on the level and the pose is within ~0.5 m.

## Large warehouse (`large_warehouse_world`) and point clouds to NavMap

```bash
git clone https://github.com/juanscelyg/large_warehouse_world.git src/large_warehouse_world
colcon build --packages-select large_warehouse_world bigmap_bringup   # (Rolling shell, see Build)
ros2 launch easynav_playground_bigmap easynav_bigmap_scenario.launch.yaml scenario:=large_warehouse
ros2 launch bigmap_bringup bigmap.launch.py config:=large_warehouse sim:=true
# elsewhere in the warehouse: change localizer_node.amcl.initial_pose in the file (the robot is
# spawned there and AMCL starts there; the package suggests 100 300, 300 230, 587 140, 300 405,
# 100 190, 300 50; the robot spawns at z = 0.5)
```

The package ships the NavMap of the article's runs (`maps/large_warehouse_collision.navmap`, 2.5 M
NavCels at 0.5 m, the same file as `easynav_large_warehouse` of bigmap_experiments), and the `.pcd`
the Bonxai map is built from. To make another one from a cloud,
`ros2 run navmap_tools pointcloud_to_navmap --input cloud.pcd --output map.navmap --resolution 0.5`, put
it in `maps/` (or anywhere, with `bigmap.package: ""` and an absolute path) and point
`bigmap.navmap_path_file` of a copy of the file to it (`params_file:=<the copy>`). AMCL localizes on
the same cloud (`bonxai`); the world's origin is the south-west corner of the plan, so map and world
frames coincide. The maps manager has the values of the article's runs: `cell_size` 0.5 to 8 m,
`min_radius` 15 m, `max_radius` 60 m, `obstacle_max_height` 1.0 m (the shelves of the racks the robot
passes under are not obstacles). Building the tiles takes ~8 s at start (2.5 M NavCels, 6 790 tiles,
on every core) and the map around the robot (~31 k NavCels) ~45 ms each time it is made again, on
this machine. The world is heavy (5 400 visuals, 800 collisions) and needs the GPU; how the simulation
copes (`gpu:=`, `lite:=`, the slow spawner) is in the README of `easynav_playground_bigmap`, "A large
warehouse and its cost".

**AMCL cost.** Each correction casts one ray per point and particle through the Bonxai map (DDA,
one step per voxel): about particles x points x range / voxel. With the defaults (100 particles,
1500 points, 0.3 m voxels) the EasyNav thread that runs AMCL, the maps manager and the planner sat
at 100 % of a core in the garage, the maps manager only kept 1-3 Hz of its 10 Hz and an AMCL update
went over 100 ms in the timing table (measured with the previous maps manager). Tuned in
`localizer_node.amcl` of the parameter file:

| | particles | points | cloud voxel | Bonxai voxel | freq |
|---|---|---|---|---|---|
| garage (default AMCL: 100 / 1500 / 0.3 m / 0.3 m / 5 Hz) | 40 | 300 | 0.5 m | 0.3 m | 5 Hz |
| large warehouse (lidar sees 100 m) | 40 | 250 | 0.6 m | 0.6 m (`bonxai.resolution`) | 3 Hz |

In the garage that thread dropped to about 49 % and the maps manager kept 10 Hz (one measurement
each, same machine). If the pose drifts, raise `num_particles` / `correct_max_points` first; if it
is still slow, lower `freq`. The warehouse values are not measured (Gazebo at 1-35 % of real time
leaves EasyNav mostly idle): compare the `[localizer]` row of the timing table before and after.

## Levels of detail and sensed obstacles

How the plugin works and what it costs is in the README of `easynav_bigmap_maps_manager`. In short:

- **At start**, the NavMap is cut into square tiles of `min_radius / 2` and each tile is simplified at
  every level: within `cell_size.min / 2` at level 0, twice that at each level up, NavCels no larger
  than `cell_size.max`. It takes seconds, on every core, and it is done once.
- **Every cycle**, when the robot has moved `min_radius / 4`, its tiles change or the sensed obstacles
  do (at most every `rebuild_period`), the map is assembled again from the tiles: the finest level
  within `min_radius`, the coarsest from `max_radius`, geometric in between (the circles and the tiles
  are in RViz, `/maps_manager_node/bigmap/markers`). Within `min_radius` the borders of the map, the
  sensed obstacles and the NavCels within the inflation radius of them get NavCels of `cell_size.min`.
- **Sensed obstacles**: the points of the perceptions within `sensor_range`, between
  `obstacle_min_height` (plus `obstacle_min_height_per_meter` per metre) and `obstacle_max_height`
  above the map's surface under them. A point over no surface (a hole: a rack, a building), or next to
  one, is the map's own obstacle and is left out. They are remembered by cells of `cell_size.min / 2`
  in log-odds (`memory.p_hit`, `memory.p_miss`): the rays from the robot clear what moved away
  (`memory.clearing`), and they are forgotten beyond `forget_distance` (or after `memory.decay_time`).
  They are `LETHAL_OBSTACLE` in the layer `obstacles`; the inflation filter spreads the cost in
  `inflated_obstacles`, which A\* reads.

## Your own NavMap outdoors: `navmap:=`

```bash
ros2 launch easynav_playground_geo easynav_geo.launch.yaml                       # a world to drive in
ros2 launch bigmap_bringup bigmap.launch.py sim:=true navmap:=~/maps/campus.navmap
```

Any NavMap works, whatever the size of its NavCels: the maps manager loads it instead of the NavMap of a
place, and no DEM is made. `<map>.yaml` next to the file (`georeferenced: true`, `origin_lat`,
`origin_lon`, `reference_altitude`, as `pointcloud_to_navmap --origin` writes it) gives the UKF its
origin; without it the file's `localizer_node.ukf.*_origin` are used and the launch says so.

## Parameters

Complete configurations with the same sections, names and order: `config/params_outdoor.yaml`,
`config/params_indoor.yaml` (real robot), `config/params_parking_garage.yaml`, `params_two_floors.yaml` and
`config/params_large_warehouse.yaml` (simulations: they add the Bonxai map and AMCL). The header of
each file has the table of lengths. Every option the maps manager (`maps_manager_node.bigmap`) reads is
in every file, by function:

| Section | Options |
|---|---|
| 2.1 map | `package`, `navmap_path_file` (outdoors, the launch gives the NavMap it made) |
| 2.2 levels of detail | `cell_size.{min,max}`, `min_radius`, `max_radius`, `rebuild_period` |
| 2.3 sensed obstacles | `sensor_range`, `obstacle_min_height`, `obstacle_min_height_per_meter`, `obstacle_max_height`, `forget_distance`, `memory.{clearing,decay_time,p_hit,p_miss}` |
| 2.4 filters | `filters`, `inflation` (NavMap filters of easynav_navmap_maps_manager: their parameters are the plugin's) |

In order: `cell_size.min <= cell_size.max`, `min_radius < max_radius`, `sensor_range <=
forget_distance`, `inflation.inflation_radius >= system_node.robot_geometry.inscribed_radius`. The
values are those of the article's runs (bigmap_experiments) where it has the use case: the large
warehouse (0.5 to 8 m, 15 / 60 m) and the outdoor area (8 m, 15 / 60 m, with the DEM's 1 m cells);
the indoor ones are those of its garage runs (0.4 to 3.2 m, 5 / 20 m, `sensor_range` 3 m).

The plugin publishes `/maps_manager_node/bigmap/map` (the NavMap, when it changes, at most once a
second), `.../map_updates` (what the filters change), `.../markers` (the circles of the levels and
the tiles in use) and `.../stats` (the cost of each cycle), and sets `map.navmap` in the NavState.

## Tests and diagnosis

```bash
colcon test --packages-select easynav_bigmap_maps_manager bigmap_bringup && colcon test-result --verbose
```

- `easynav_bigmap_maps_manager`: `test_tiled_lod` (levels, no cracks, holes and narrow passages kept
  far away, layers) and `test_bigmap_plugin` (the plugin as EasyNav runs it: fine at the borders near
  the robot and coarse far, the map follows the robot, a sensed obstacle is added fine, inflated and
  forgotten far away, and cleared when it moves away).
- `bigmap_bringup`: `test/test_config.py` checks the `params_*.yaml` against each other and
  against the code: no key that no code reads (typos, also in `dem_generator`), every key
  the plugin reads is in every file, the same structure in all, none of the previous plugin's,
  lengths in order, inflation filters bigger than the robot, plugin ids that exist, the map files
  they point to, `use_sim_time` per use case, the AMCL start of the simulations, goal tolerances
  equal in system and controller, `bigmap.navmap_path_file` = the generator's `navmap_file`.
  `test/test_dem.py`: the `dem_generator` block into a `navmap_gis_tool` command (DEM and NavMap),
  the overrides file (the NavMap's full path, the UKF origin), a place into overrides, what a simulation leaves for the
  application, a world of `easynav_playground_geo`. `test/test_launch.py` calls the launch's `setup()` with
  arguments, without starting anything: which file and map each use case gets, following either
  simulation (the last one launched), and every refused combination with its message.
  `test/test_geo_launch.py`: `bigmap_geo.launch.py` includes the playground first and then the
  application, with the playground's arguments and defaults. `test/test_config.py` looks for the
  plugin next to this package, else for the source of `easynav_plugins` upwards (or `EASYNAV_PLUGINS_SRC`), and skips the checks
  against the plugin when it is not there.
- The simulation's tests are in `easynav_playground_geo` (`easynav_playgrounds`).
- At start the plugin logs the map it loaded, its tiles and its levels (cell size, from which
  distance, NavCels), and every 10 s the map around the robot (NavCels, tiles, sensed obstacles, the
  time to assemble and detail it). `/maps_manager_node/bigmap/stats` has the cost of every cycle.

## Known limitations

- The tiles of the whole map are built at start and kept in memory: seconds and memory that grow
  with the map, not with the robot's surroundings (the large warehouse: ~8 s; 2 x 2 km of Madrid at
  0.5 m, 13.8 M NavCels: ~45 s, see the plugin's README).
- Outdoors the NavMap of the place is made again at every launch from the cached DEM.
- The map is not saved by the plugin, and the sensed obstacles are not kept from one run to the next.
- Validated with the unit tests and by starting each use case without a robot (the map is loaded,
  its levels built and the map assembled); not driven in Gazebo with this maps manager yet.
- In a simulation EasyNav starts when the robot's odometry transform (`odom -> base_footprint`)
  appears (`tools/wait_for_robot.py`), or after 120 s with a warning if it never does.

## Author and license

Copyright 2026 José Miguel Guerrero (<josemiguel.guerrero@urjc.es>), author and maintainer.
Licensed under the Apache License, Version 2.0 (see `LICENSE` in the repository root).
