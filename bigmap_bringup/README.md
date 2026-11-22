# bigmap_bringup

**BigMap on a robot, real or simulated.** The parameter files of the use cases, their maps, an RViz
configuration, and one launch file that starts EasyNav with the BigMap maps manager
(`easynav_bigmap_maps_manager/BigMapMapsManager`: a NavMap that is fine around the robot and coarse
far away) and RViz. Nothing else: no map is made, no file is written, nothing is read from a
simulation. The robot, real or simulated and launched first, gives the sensors, the odometry and
the TF.

Two commands, always:

```bash
# 1. the robot: a simulation (below) or the real one
# 2. EasyNav with BigMap and the parameter file of the use case
ros2 launch bigmap_bringup bigmap.launch.py config:=<use case>
```

The launch is only a shorthand. Without it, the second command is EasyNav with the parameter file,
and RViz:

```bash
SHARE=$(ros2 pkg prefix bigmap_bringup)/share/bigmap_bringup
ros2 run easynav_system system_main --ros-args --params-file $SHARE/config/params_<use case>.yaml
ros2 run rviz2 rviz2 -d $SHARE/rviz/bigmap.rviz
```

To use the plugin without this package, see the README of `easynav_bigmap_maps_manager`: its
parameters, how it works and what it costs.

## Use cases: `config:=`

`config:=<name>` is `config/params_<name>.yaml`. Every file is complete: the launch gives it to
EasyNav as it is.

| `config:=` | Map | Localization | Meant for |
|---|---|---|---|
| `outdoor` (default) | the NavMap of a place, made beforehand (`~/.ros/bigmap/place.navmap`) | GPS + odometry + IMU (UKF) | an outdoor ground robot; the Summit XL in `easynav_playground_geo` |
| `indoor` | your NavMap file (floors over each other, ramps) | external: your own localization gives `map -> odom` | an indoor real robot (a template to fill) |
| `parking_garage` | `maps/parking_garage.navmap` (two floors and ramps) | AMCL on its Bonxai map | simulation |
| `large_warehouse` | `maps/large_warehouse_collision.navmap` (700 x 450 m): the article's | AMCL | simulation |
| `two_floors` | `maps/two_floors.navmap` (two floors, one start) | AMCL | simulation |

| Argument | Default | What it is |
|---|---|---|
| `config` | `outdoor` | the use case: `config/params_<config>.yaml` |
| `params_file` | `''` | a complete parameter file of your own instead |
| `use_sim_time` | `''` | `true` / `false` for EasyNav and RViz; empty: the file's (`true` in the simulations, `false` in `indoor`) |
| `rviz`, `rviz_config` | `true`, `''` | RViz2 and its configuration (`rviz/bigmap.rviz`) |

## Build (ROS 2 Rolling)

This package is part of the [BigMap](https://github.com/EasyNavigation/BigMap) repository, with the
maps manager; `bigmap.repos` brings the rest (EasyNav and its plugins, NavMap, the playgrounds). One
distro per shell, and always a shell where only Rolling is sourced (a binary built with Rolling does
not run under Jazzy: `undefined symbol ... rclcpp ...`):

```bash
mkdir -p <ws>/src && cd <ws>/src
git clone https://github.com/EasyNavigation/BigMap.git && cd ..
vcs import src < src/BigMap/bigmap.repos
source /opt/ros/rolling/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-up-to bigmap_bringup easynav_playground_geo \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PROJECT_navmap_rviz_plugin_INCLUDE=$PWD/src/BigMap/bigmap_bringup/cmake/rolling_rviz_qt.cmake
source install/setup.bash
```

With `--symlink-install` the YAMLs, the launch file and `maps/` are links to `src`: edit them without
rebuilding. `rolling_rviz_qt.cmake` is a workaround for the Rolling packages released for Ubuntu
24.04 (no longer updated): their `rviz_common` is built against Qt5 but exports a bare `Qt5`
dependency and looks for Qt6 first. It only affects `navmap_rviz_plugin` and edits no third-party
code; it is not needed on a consistent Rolling (Ubuntu 26.04). Do not run two stacks on the same
`ROS_DOMAIN_ID` / `GZ_PARTITION`.

`maps/` is 180 MB: the NavMaps and the point clouds of the indoor use cases (AMCL localizes on the
clouds).

## Outdoor: any place (`easynav_playground_geo`)

```bash
# 1. the simulation: the Gazebo world of the place, with the Summit XL (made once, then reused)
ros2 launch easynav_playground_geo_worlds geo_sim.launch.py lat:=40.4168 lon:=-3.7038 radius:=250 world:=area
# 2. EasyNav with BigMap
ros2 launch bigmap_bringup bigmap.launch.py config:=outdoor
```

`params_outdoor.yaml` needs the NavMap of the place and the origin of its map frame, which are the
place's. Once per place, before step 2, make the NavMap from the world the simulation made
(`~/.ros/easynav_geo/worlds/<world>/`: its `world.yaml` has the centre and the height of the
ground there):

```bash
W=~/.ros/easynav_geo/worlds/area_40.41680_-3.70380_250
ros2 run navmap_tools navmap_gis_tool --center 40.4168,-3.7038 --size 500 --resolution 1.0 \
  --dem-source mesh --mesh-file $W/navmap_ground.stl --mesh-world-elevation 648.015 \
  --dem-holes-mesh $W/navmap_holes.stl --max-slope-deg 25 --navmap-keep 0,0 \
  --navmap-out ~/.ros/bigmap/place.navmap
```

- `--center` is the world's `latitude,longitude`, `--size` twice its `radius`, and
  `--mesh-world-elevation` its `ground_elevation`.
- `navmap_ground.stl` is the ground of the world and `navmap_holes.stl` its buildings, walls and
  tree trunks, which are left as holes of the NavMap. A `world:=terrain` has no holes: use
  `navmap.stl` and leave out `--dem-holes-mesh`.
- `--navmap-keep 0,0` keeps only the part of the map connected to where the robot is spawned
  (`spawn_x`, `spawn_y` of `world.yaml`), without roofs and closed patios.
- `--resolution` is the finest NavCel, `bigmap.cell_size.min` of the file (1 m). The ground steeper
  than `--max-slope-deg` is left out.

Then set in `params_outdoor.yaml` (or a copy, with `params_file:=`) the origin of the UKF,
`localizer_node.ukf.latitude_origin`, `longitude_origin` and `altitude_origin`: the world's
`latitude`, `longitude` and `ground_elevation`. The file has those of the example above (Puerta del
Sol, Madrid) and loads `~/.ros/bigmap/place.navmap` (`bigmap.navmap_path_file`; `~/` is the home
directory).

On a real robot, make the NavMap of its place from the terrain instead (`--dem-source ign` in Spain,
5 m; `copernicus30` anywhere, 30 m; `--buildings auto` adds the buildings as holes), and set the UKF
origin to the same `--center` and the altitude of the ground there. `navmap_gis_tool --help` has
every option.

Notes:
- The UKF runs in 3D with the wheel odometry's vz = 0 as an anchor. GPS localization drifts a few
  metres over tens of metres of path in simulation.
- The NavMap is loaded as it is: BigMap builds its tiles at start (a 500 m square at 1 m: a few
  seconds).

## Indoor, multi-level

```bash
# real robot, no Gazebo: config/params_indoor.yaml (use_sim_time false, external localization);
# set bigmap.navmap_path_file there, or copy the file and pass params_file:=<yours>
ros2 launch bigmap_bringup bigmap.launch.py config:=indoor

# simulation: the parking garage of easynav_playground_summit_worlds, with the robot at the start
# of the file (localizer_node.amcl.initial_pose: 0, 0)
ros2 launch easynav_playground_summit_worlds gazebo_sim.launch.yaml \
  world:=$(ros2 pkg prefix easynav_playground_summit_worlds)/share/easynav_playground_summit_worlds/worlds/parking_garage.world
ros2 launch bigmap_bringup bigmap.launch.py config:=parking_garage
```

Every use case has its own complete parameter file: the maps manager, the NavMap it loads
(`bigmap.package: bigmap_bringup` + `bigmap.navmap_path_file: maps/<scenario>.navmap`, relative to
the package's share directory, as the Bonxai map's `package` + `bonxai_path_file`), the Bonxai map,
AMCL and its start pose. The simulation must spawn the robot at that start pose. Set the robot's
lidar topic, `robot_geometry` (0.5 m for the Summit XL: 0.7 m does not fit a 2 m ramp between
curbs) and the levels of detail in the file.

Floors over each other are the NavMap's own: BigMap cuts the map into tiles and simplifies them
(`navmap::simplify`), which keeps the map's topology (no hole closes, no wall opens, floors over each
other are not stitched together, however coarse), so the same parameters serve one floor and several.
The obstacle heights (`obstacle_min_height` .. `obstacle_max_height`, 0.2 .. 1.2 m indoors) are above
the surface under each point, so the floor above is out of reach.

**Choosing a floor in RViz.** The goal tool takes the first surface under the mouse, i.e. the
topmost one. Publish the goal by hand, with the floor's z, to choose another:
`ros2 topic pub --once /goal_pose geometry_msgs/msg/PoseStamped '{header: {frame_id: map}, pose:
{position: {x: -1.8, y: -4.1, z: 2.35}, orientation: {w: 1.0}}}'`.

**Two floors** (`config:=two_floors`): the maps of a building of two floors from a SLAM with a
real robot (`maps/two_floors.navmap` and `.pcd`). There is no Gazebo world of it: to drive a
simulated robot in it, bring your own world of the building (its mesh, or one modelled from the
plan) in the frame of the NavMap, and spawn the robot at the start of the file, (-6.8, -7.8), a
single floor at z = -0.12 with walls all around: where two floors are stacked, Gazebo and AMCL
(which takes the topmost floor) could disagree on the level. The same goes for a map of your own:
copy `params_parking_garage.yaml` and set the Bonxai map, the NavMap and the AMCL start.

## Large warehouse (`large_warehouse_world`)

```bash
# the simulation of the article's runs (bigmap_experiments, package easynav_large_warehouse, with
# large_warehouse_world): Gazebo, the Summit XL at 100, 300, and EasyNav with this file
ros2 launch easynav_large_warehouse large_warehouse_sim.launch.py \
  params_file:=$(ros2 pkg prefix bigmap_bringup)/share/bigmap_bringup/config/params_large_warehouse.yaml \
  rviz_config:=$(ros2 pkg prefix bigmap_bringup)/share/bigmap_bringup/rviz/bigmap.rviz
```

The world is heavy (5 400 visuals, 800 collisions) and needs the GPU; its launcher lightens it
(`lite:=true`) and starts EasyNav when the robot is up, so here it is one command. Elsewhere in the
warehouse: change `localizer_node.amcl.initial_pose` in a copy of the file and spawn the robot there
(`x:=`, `y:=`; the world suggests 100 300, 300 230, 587 140, 300 405, 100 190, 300 50).

The package ships the NavMap of the article's runs (`maps/large_warehouse_collision.navmap`, 2.5 M
NavCels at 0.5 m) and the `.pcd` the Bonxai map is built from. The maps manager has the values of the
article's runs: `cell_size` 0.5 to 8 m, `min_radius` 15 m, `max_radius` 60 m, `obstacle_max_height`
1.0 m (the shelves of the racks the robot passes under are not obstacles). Building the tiles takes
~8 s at start (2.5 M NavCels, 6 790 tiles, on every core) and the map around the robot (~31 k
NavCels) ~45 ms each time it is made again.

**AMCL cost.** Each correction casts one ray per point and particle through the Bonxai map (DDA,
one step per voxel): about particles x points x range / voxel. Tuned in `localizer_node.amcl`:

| | particles | points | cloud voxel | Bonxai voxel | freq |
|---|---|---|---|---|---|
| garage (default AMCL: 100 / 1500 / 0.3 m / 0.3 m / 5 Hz) | 40 | 300 | 0.5 m | 0.3 m | 5 Hz |
| large warehouse (lidar sees 100 m) | 40 | 250 | 0.6 m | 0.6 m (`bonxai.resolution`) | 3 Hz |

In the garage the EasyNav thread that runs AMCL, the maps manager and the planner dropped from 100 %
to about 49 % of a core and the maps manager kept 10 Hz. If the pose drifts, raise `num_particles` /
`correct_max_points` first; if it is still slow, lower `freq`.

## Point clouds to a NavMap: `pointcloud_to_navmap`

The NavMap that BigMap starts from is the finest one it will ever use: BigMap simplifies it (its
finest level within `cell_size.min / 2`, the coarsest up to `cell_size.max`) and details it again near
the robot. `pointcloud_to_navmap` (package `navmap_tools`, in NavMap) makes it from one or several
`.pcd` files, however big:

```bash
ros2 run navmap_tools pointcloud_to_navmap --input cloud.pcd --output map.navmap --resolution 1.0 \
    --min-clearance 1.0 --recenter [--origin lat,lon,alt] [--crop x0,y0,x1,y1] [--zmax 2.5]
```

- **`--resolution`** is the finest NavCel: use `bigmap.cell_size.min` of your parameter file.
- **Big clouds** are streamed (1 M points at a time) and reduced by voxel above 5 M points
  (`--voxel`), so memory follows the *extent* of the map, not the number of points.
  `binary_compressed` cannot be streamed and is loaded whole.
- **Several floors**: one vertex per floor in a cell; `--min-clearance` (the free height that
  separates two floors) must be below the headroom of the lowest ramp (in the garage, 1.0-1.5 keeps
  every floor joined; 2.0 cuts the ramp to the top floor). Surfaces steeper than `--max-slope-deg`
  stay as gaps.
- **Holes** (`--fill-holes`, 2 m): where a SLAM cloud did not see the floor, a stretch of empty cells
  up to that wide between two bits of the same floor is filled. What the cloud lacks entirely (a
  ramp nobody scanned) stays missing. `--min-surface-area` drops specks connected to nothing.
- **Resolution the data supports**: the tool prints the finest resolution with at least 3 points per
  cell; below it, holes and rough ground follow.
- **Output**: `map.navmap` and `map.yaml` (`--origin` makes it georeferenced; `--recenter` centres it
  and writes the shift as `offset_x` / `offset_y`). Keep the cloud in local coordinates: a PCD stores
  float32, which is 0.5 m of precision at UTM northings.

Then point `bigmap.navmap_path_file` of a copy of a parameter file to it (`bigmap.package: ""` and a
path) and launch with `params_file:=<the copy>`.

## Levels of detail and sensed obstacles

How the plugin works and what it costs is in the README of `easynav_bigmap_maps_manager`. In short:

- **At start**, the NavMap is cut into square tiles of `min_radius / 2` and each tile is simplified at
  every level: within `cell_size.min / 2` at level 0, twice that at each level up, NavCels no larger
  than `cell_size.max`. It takes seconds, on every core, and it is done once.
- **Every cycle**, when the robot has moved `min_radius / 4`, its tiles change or the sensed obstacles
  do (at most every `rebuild_period`), the map is assembled again from the tiles: the finest level
  within `min_radius`, the coarsest from `max_radius`, geometric in between (the circles and the tiles
  are in RViz, `/maps_manager_node/bigmap/markers`). The borders of the map within `min_radius`, the
  sensed obstacles wherever they are, and the NavCels within the inflation radius of them get NavCels
  of `cell_size.min`.
- **Sensed obstacles**: the points of the perceptions within `sensor_range`, between
  `obstacle_min_height` (plus `obstacle_min_height_per_meter` per metre) and `obstacle_max_height`
  above the map's surface under them. A point over no surface (a hole: a rack, a building), or next to
  one, is the map's own obstacle and is left out. They are remembered by cells of `cell_size.min / 2`
  in log-odds (`memory.p_hit`, `memory.p_miss`): the rays from the robot clear what moved away
  (`memory.clearing`), and they are forgotten beyond `forget_distance` (or after `memory.decay_time`).
  They are `LETHAL_OBSTACLE` in the layer `obstacles`; the inflation filter spreads the cost in
  `inflated_obstacles`, which A\* reads.

## Parameters

Complete configurations with the same sections, names and order: `config/params_outdoor.yaml`,
`config/params_indoor.yaml` (real robot), `config/params_parking_garage.yaml`,
`config/params_two_floors.yaml` and `config/params_large_warehouse.yaml` (simulations: they add the
Bonxai map and AMCL). The header of each file has the table of lengths. Every option the maps manager
(`maps_manager_node.bigmap`) reads is in every file, by function:

| Section | Options |
|---|---|
| 1.1 map | `package`, `navmap_path_file` |
| 1.2 levels of detail | `cell_size.{min,max}`, `min_radius`, `max_radius`, `rebuild_period` |
| 1.3 sensed obstacles | `sensor_range`, `obstacle_min_height`, `obstacle_min_height_per_meter`, `obstacle_max_height`, `forget_distance`, `memory.{clearing,decay_time,p_hit,p_miss}` |
| 1.4 filters | `filters`, `inflation` (NavMap filters of easynav_navmap_maps_manager: their parameters are the plugin's) |

In order: `cell_size.min <= cell_size.max`, `min_radius < max_radius`, `sensor_range <=
forget_distance`, `inflation.inflation_radius >= system_node.robot_geometry.inscribed_radius`, and
the planner's `replan_hysteresis_horizon` within `min_radius` (beyond it the map is coarse and its
costs approximate). The values are those of the article's runs (bigmap_experiments) where it has the
use case: the large warehouse (0.5 to 8 m, 15 / 60 m) and the outdoor area (8 m, 15 / 60 m, with 1 m
cells); the indoor ones are those of its garage runs (0.4 to 3.2 m, 5 / 20 m, `sensor_range` 3 m).

The plugin publishes `/maps_manager_node/bigmap/map` (the NavMap, when it changes, at most once a
second), `.../map_updates` (what the filters change), `.../markers` (the circles of the levels and
the tiles in use) and `.../stats` (the cost of each cycle), and sets `map.navmap` in the NavState.

## Tests

```bash
colcon test --packages-select easynav_bigmap_maps_manager bigmap_bringup && colcon test-result --verbose
```

- `easynav_bigmap_maps_manager`: `test_tiled_lod` (levels, no cracks, holes and narrow passages kept
  far away, obstacles as fine far away as near, layers) and `test_bigmap_plugin` (the plugin as
  EasyNav runs it).
- `bigmap_bringup`: `test/test_config.py` checks the `params_*.yaml` against each other and against
  the code: no key that no code reads, every key the plugin reads in every file, the same structure in
  all, lengths in order, inflation filters bigger than the robot, plugin ids that exist, the map files
  they point to, `use_sim_time` per use case, the AMCL start of the simulations, goal tolerances equal
  in system and controller. It looks for the plugin next to this package, else for the source of
  `easynav_plugins` upwards (or `EASYNAV_PLUGINS_SRC`). `test/test_launch.py` calls the launch's
  `setup()` without starting anything: which file EasyNav and RViz get, and what is refused.

## Known limitations

- The tiles of the whole map are built at start and kept in memory: seconds and memory that grow
  with the map, not with the robot's surroundings (the large warehouse: ~8 s; 2 x 2 km of Madrid at
  0.5 m, 13.8 M NavCels: ~45 s, see the plugin's README).
- The map is not saved by the plugin, and the sensed obstacles are not kept from one run to the next.
- EasyNav starts right away: launch it once the robot (and, in simulation, Gazebo) is up.

## Author and license

Copyright 2026 José Miguel Guerrero (<josemiguel.guerrero@urjc.es>), author and maintainer.
Licensed under the Apache License, Version 2.0 (see `LICENSE` in the repository root).
