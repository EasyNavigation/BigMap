# BigMap

**A NavMap fine around the robot and coarse far away, for EasyNav.** BigMap is a maps manager for
[EasyNavigation](https://github.com/EasyNavigation/EasyNavigation) for NavMaps too big to plan on at full
detail (a warehouse, a town). The map is cut into tiles, each simplified at several levels of detail
once at start. Every cycle the map around the robot is assembled from them: fine near the robot,
coarse far from it. The obstacles the sensors see are added near the robot and forgotten when it is
far from them. On 2 x 2 km of Madrid (13.8 M NavCels), routes of up to 1.5 km are planned 63 times
faster than on the full map, within 1 % of their length (see
[`easynav_bigmap_maps_manager`](easynav_bigmap_maps_manager/README.md)).

This repository has the plugin, the application that runs it on a robot (real or simulated), and the
EasyNav plugins it is used with, at the versions of the article's experiments.

| path | what it is |
|---|---|
| [`easynav_bigmap_maps_manager/`](easynav_bigmap_maps_manager/README.md) | the maps manager plugin (`easynav_bigmap_maps_manager/BigMapMapsManager`) |
| [`bigmap_bringup/`](bigmap_bringup/README.md) | the application: launch files, the parameter files of the use cases (outdoor, indoor, parking garage, large warehouse, two floors), maps, RViz, and `bigmap_geo.launch.py` (BigMap in the simulated world of any real place) |
| [`easynav_plugins/`](easynav_plugins) | the EasyNav plugins BigMap is used with, at the versions of the article's experiments (see below) |
| [`bigmap.repos`](bigmap.repos) | the other repositories of the workspace |

### `easynav_plugins/`

Copies of packages of [easynav_plugins](https://github.com/EasyNavigation/easynav_plugins), from branch
`fractal-bigmap` of `jmguerreroh/easynav_plugins` (commit `17e8842e`, tag `bigmap-experiments-v2`: the
experiments of the article). This repository builds on its own, without the whole of
`easynav_plugins` (a workspace cannot have the same package twice):

| package | why | changes over `rolling` |
|---|---|---|
| `maps_managers/easynav_navmap_maps_manager` | its filters (inflation) run on BigMap's map | Fractal filter (a merged copy of the map for planning), sensed obstacles at the pose of each cloud, `navmap_path_file` without a package |
| `planners/easynav_navmap_planner` | the A* on the NavMap | `map_key`, dense paths from the robot on large NavCels, planner fixes |
| `controllers/easynav_regulated_pp_controller` | the controller of the use cases | none |
| `localizers/easynav_navmap_localizer` | AMCL in the indoor simulations | none |
| `localizers/easynav_fusion_localizer` | GPS + odometry + IMU outdoors | none |
| `maps_managers/easynav_bonxai_maps_manager` | the Bonxai map AMCL localizes on | none |

When those changes and BigMap itself (easynav_plugins#183) are merged in `easynav_plugins`, these
copies go and `bigmap.repos` takes `easynav_plugins` instead.

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

`bigmap.repos` brings EasyNavigation and `yaets`, NavMap and `easynav_playgrounds`. Two come from the
`jmguerreroh` forks until their pull requests are merged in EasyNavigation:

- NavMap, branch `bigmap`: `simplify` with `keep_vertices`, `cut_along_lines` and `refine`
  (NavMap#47), bounds that change from place to place (#46), `navmap_gis_tool` with buildings,
  `--navmap-out` and `--navmap-keep` (#45), geometry patches and chunked RViz meshes. It is branch
  `fractal-ws` (commit `fdee528`, the article's) plus `--navmap-keep`, which keeps only the part of
  the NavMap of a place the robot can reach (without roofs and closed patios); to rebuild exactly
  what the article measured, check out `fractal-ws`.
- `easynav_playgrounds`, branch `playground_geo` (`easynav_playground_geo`).

`rolling_rviz_qt.cmake` is explained in [`bigmap_bringup`](bigmap_bringup/README.md#build-ros-2-rolling).

## Run

```bash
# the world of any place in Gazebo, with the Summit XL, and BigMap on it
ros2 launch bigmap_bringup bigmap_geo.launch.py lat:=46.0207 lon:=7.7491 radius:=300                # terrain (Zermatt)
ros2 launch bigmap_bringup bigmap_geo.launch.py lat:=40.4168 lon:=-3.7038 radius:=250 world:=area   # + buildings, walls, trees

# on a robot, real or simulated: one of the use cases of config/
ros2 launch bigmap_bringup bigmap.launch.py config:=outdoor
```

See [`bigmap_bringup`](bigmap_bringup/README.md) for the use cases and every parameter, and
[`easynav_bigmap_maps_manager`](easynav_bigmap_maps_manager/README.md) for how the plugin works and what
it costs.

## License

Apache-2.0.
