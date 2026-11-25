# BigMap

**A NavMap fine around the robot and coarse far away, for EasyNav.** BigMap is a maps manager for
[EasyNavigation](https://github.com/EasyNavigation/EasyNavigation) for NavMaps too big to plan on at full
detail (a warehouse, a town). The map is cut into tiles, each simplified at several levels of detail
once at start. Every cycle the map around the robot is assembled from them: fine near the robot,
coarse far from it. The obstacles the sensors see are added near the robot and forgotten when it is
far from them. On 2 x 2 km of Madrid (13.8 M NavCels), routes of up to 1.5 km are planned 63 times
faster than on the full map, within 1 % of their length (see
[`easynav_bigmap_maps_manager`](easynav_bigmap_maps_manager/README.md)).

This repository has the plugin and the application that runs it on a robot (real or simulated).

| path | what it is |
|---|---|
| [`easynav_bigmap_maps_manager/`](easynav_bigmap_maps_manager/README.md) | the maps manager plugin (`easynav_bigmap_maps_manager/BigMapMapsManager`) |
| [`bigmap_bringup/`](bigmap_bringup/README.md) | the application: the parameter files of the use cases (outdoor, indoor, parking garage, large warehouse, two floors), their maps, RViz, and a launch file that starts EasyNav with one of them |
| [`bigmap.repos`](bigmap.repos) | the other repositories of the workspace |

## Build (ROS 2 Rolling)

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

`bigmap.repos` brings EasyNavigation and `yaets`, `easynav_plugins`, NavMap and
`easynav_playgrounds`. Three come from the `jmguerreroh` forks until their pull requests are merged
in EasyNavigation:

- `easynav_plugins`, branch `bigmap`: tag `bigmap-experiments-v2` (the plugins of the article's
  experiments) without its `easynav_bigmap_maps_manager`, which is this repository's (a workspace
  cannot have the same package twice). Over `rolling`, the NavMap maps manager has the Fractal
  filter (a merged copy of the map for planning), sensed obstacles at the pose of each cloud and
  `navmap_path_file` without a package; the NavMap planner `map_key`, dense paths from the robot on
  large NavCels and planner fixes (easynav_plugins#182, #184, #185). When those are merged,
  `bigmap.repos` takes `EasyNavigation/easynav_plugins`.

- NavMap, branch `bigmap`: EasyNavigation/NavMap `rolling`, where what BigMap needs is already
  merged (`simplify` with `keep_vertices`, `cut_along_lines` and `refine`, NavMap#47; bounds that
  change from place to place, #46; `navmap_gis_tool` with buildings, `--navmap-out` and
  `--navmap-keep`, #45), plus geometry patches and chunked RViz meshes (#48, still open), which RViz
  needs to show large maps and `easynav_plugins` (its Fractal filter) to build. When #48 is merged,
  `bigmap.repos` takes `EasyNavigation/NavMap`. The article's versions are listed in
  [bigmap_experiments](https://github.com/jmguerreroh/bigmap_experiments/blob/main/experiments/REPRODUCIBILITY.md).
- `easynav_playgrounds`, branch `playground_geo` (`easynav_playground_geo`).

`rolling_rviz_qt.cmake` is explained in [`bigmap_bringup`](bigmap_bringup/README.md#build-ros-2-rolling).

## Run

Two commands: the robot (a simulation, or the real one), then EasyNav with BigMap and the parameter
file of the use case.

```bash
# the world of any place in Gazebo, with the Summit XL
ros2 launch easynav_playground_geo_worlds geo_sim.launch.py lat:=40.4168 lon:=-3.7038 radius:=250 world:=area
# EasyNav with BigMap (the NavMap of the place is made once beforehand: see bigmap_bringup)
ros2 launch bigmap_bringup bigmap.launch.py config:=outdoor
```

The second command is only a shorthand for EasyNav with that parameter file, plus RViz:

```bash
SHARE=$(ros2 pkg prefix bigmap_bringup)/share/bigmap_bringup
ros2 run easynav_system system_main --ros-args --params-file $SHARE/config/params_outdoor.yaml
ros2 run rviz2 rviz2 -d $SHARE/rviz/bigmap.rviz
```

See [`bigmap_bringup`](bigmap_bringup/README.md) for the use cases, how to make the NavMap of a
place, and every parameter, and [`easynav_bigmap_maps_manager`](easynav_bigmap_maps_manager/README.md)
for how the plugin works and what it costs.

## License

Apache-2.0.
