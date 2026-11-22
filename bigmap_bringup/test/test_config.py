# Copyright 2026 José Miguel Guerrero
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Checks of the parameter files (config/params_*.yaml) against each other and against the
code that reads them: every key is one the plugin knows (no typos), every key the plugin reads is
in every file (nothing is left to a default by accident), the options that depend on each other
agree, and the files they point to exist. Run: python3 -m pytest test/test_config.py"""

import glob
import os
import re

import pytest
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIGS = sorted(glob.glob(os.path.join(ROOT, 'config', 'params_*.yaml')))


def plugins_src():
    """The source of easynav_plugins, looked for upwards from this package (the workspace's
    src/easynav_plugins, whatever the depth this repository is cloned at), or EASYNAV_PLUGINS_SRC."""
    if os.environ.get('EASYNAV_PLUGINS_SRC'):
        return os.environ['EASYNAV_PLUGINS_SRC']
    d = ROOT
    for _ in range(4):
        d = os.path.dirname(d)
        for candidate in (os.path.join(d, 'easynav_plugins'), os.path.join(d, 'src', 'easynav_plugins')):
            if os.path.isdir(os.path.join(candidate, 'maps_managers')):
                return candidate
    return os.path.join(os.path.dirname(ROOT), 'easynav_plugins')


def plugin_dir():
    """The source of the plugin: next to this package (the BigMap repository), else with the maps
    managers of easynav_plugins."""
    sibling = os.path.join(os.path.dirname(ROOT), 'easynav_bigmap_maps_manager')
    if os.path.isdir(sibling):
        return sibling
    return os.path.join(plugins_src(), 'maps_managers', 'easynav_bigmap_maps_manager')


PLUGIN = plugin_dir()
SOURCE = os.path.join(PLUGIN, 'src', 'BigMapMapsManager.cpp')
# what each file is: real robot or simulation (use_sim_time), AMCL (its start is the spawn)
REAL_ROBOT = {'params_indoor.yaml', 'params_indoor_real.yaml'}
SIM_WITH_AMCL = {'params_parking_garage.yaml', 'params_large_warehouse.yaml',
                 'params_two_floors.yaml'}

# keys that exist in some scenarios only, and why (none: every file has every option)
SCENARIO_ONLY = {}
# blocks that belong to a borrowed plugin: bigmap does not read their keys, the plugin does
BORROWED = ('inflation', 'obstacle_filter')


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def bigmap(path):
    return load(path)['maps_manager_node']['ros__parameters']['bigmap']


def flat(d, prefix=''):
    out = {}
    for k, v in d.items():
        key = prefix + k
        if isinstance(v, dict):
            out.update(flat(v, key + '.'))
        else:
            out[key] = v
    return out


def keys_read_by_the_code():
    """The first (= current) name of every parameter BigMapMapsManager.cpp reads."""
    with open(SOURCE) as f:
        code = f.read()
    keys = set(re.findall(r'param\(\s*"([^"]+)"', code))
    for group in re.findall(r'param_any\(\s*\{([^}]*)\}', code):
        keys.add(re.findall(r'"([^"]+)"', group)[0])
    return keys


needs_source = pytest.mark.skipif(not os.path.isfile(SOURCE), reason='easynav_bigmap_maps_manager source not found')


@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_every_file_parses_and_has_all_the_nodes(path):
    d = load(path)
    for node in ('maps_manager_node', 'controller_node', 'localizer_node', 'planner_node',
                 'sensors_node', 'system_node'):
        assert node in d, node
        assert 'ros__parameters' in d[node]
    assert 'bigmap' in d['maps_manager_node']['ros__parameters']['map_types']


@needs_source
@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_no_key_the_code_does_not_know(path):
    known = keys_read_by_the_code() | {'plugin', 'freq', 'filters'}
    b = {k: v for k, v in bigmap(path).items() if k not in BORROWED}
    unknown = sorted(k for k in flat(b) if k not in known)
    assert not unknown, 'keys no code reads (typo, or removed option): %s' % unknown


@needs_source
@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_every_key_the_code_reads_is_in_the_file(path):
    present = set(flat({k: v for k, v in bigmap(path).items() if k not in BORROWED}))
    missing = sorted(k for k in keys_read_by_the_code() - present
                     if k not in SCENARIO_ONLY)
    assert not missing, 'options left to their default (document them in the file): %s' % missing


def test_the_files_have_the_same_structure():
    sets = {os.path.basename(p): set(flat(bigmap(p))) for p in CONFIGS}
    union = set().union(*sets.values())
    for name, keys in sets.items():
        gap = sorted(k for k in union - keys if k not in SCENARIO_ONLY)
        assert not gap, '%s lacks %s' % (name, gap)
    # the scenario-only keys appear where the DEM is (outdoor) and nowhere else
    for name, keys in sets.items():
        has = {k for k in SCENARIO_ONLY if k in keys}
        assert has == (set(SCENARIO_ONLY) if 'outdoor' in name else set()), name


def test_the_options_of_the_previous_plugin_are_gone_from_the_files():
    """The maps manager is the tiled one: the sections of the grid / hierarchy engines are not
    read any more (test_no_key_the_code_does_not_know says it too, when the source is there)."""
    for path in CONFIGS:
        b = bigmap(path)
        for old in ('terrain', 'multilevel', 'lengths', 'lod', 'recovery', 'traversed', 'obstacles',
                    'dynamic_map', 'output', 'obstacle_filter'):
            assert old not in b, '%s: %s' % (os.path.basename(path), old)


@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_lengths_agree_with_each_other(path):
    b = bigmap(path)
    c = b['cell_size']
    assert 0 < c['min'] <= c['max']
    assert 0 < b['min_radius'] < b['max_radius']
    assert b['sensor_range'] <= b['forget_distance']
    assert 0 <= b['obstacle_min_height'] < b['obstacle_max_height']
    assert b['rebuild_period'] > 0
    m = b['memory']
    assert 0.5 < m['p_hit'] < 1.0 and 0.0 < m['p_miss'] < 0.5 and m['decay_time'] >= 0


@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_the_followed_path_is_checked_only_where_the_map_is_fine(path):
    """Beyond min_radius the map is coarse and its costs approximate: a path checked there would
    read closed where it is not, be dropped, and taken again from afar (the robot would turn back
    and forth)."""
    astar = load(path)['planner_node']['ros__parameters']['astar']
    assert 0 < astar['replan_hysteresis_horizon'] <= bigmap(path)['min_radius']


def instance_kinds(b):
    """name -> 'obstacle' | 'inflation' for every entry of `filters`, from its plugin."""
    kinds = {}
    for name in b['filters']:
        assert name in b and 'plugin' in b[name], "'%s' is in filters but has no plugin" % name
        plugin = b[name]['plugin']
        assert plugin.endswith(('ObstaclesFilter', 'InflationFilter')), plugin
        kinds[name] = 'obstacle' if plugin.endswith('ObstaclesFilter') else 'inflation'
    return kinds


@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_the_filters_are_inflations_bigger_than_the_robot(path):
    b = bigmap(path)
    kinds = instance_kinds(b)
    # the sensed obstacles are bigmap's own: an ObstaclesFilter would add them a second time
    assert set(kinds.values()) <= {'inflation'}, kinds
    inscribed = load(path)['system_node']['ros__parameters']['robot_geometry']['inscribed_radius']
    for name in kinds:
        assert b[name]['inflation_radius'] >= inscribed


@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_the_map_files_exist(path):
    b = bigmap(path)
    if b['package'] and b['navmap_path_file']:
        # relative to the package's share directory, which is this source tree once installed
        assert b['package'] == 'bigmap_bringup', 'only maps of this package are checked here'
        assert os.path.isfile(os.path.join(ROOT, b['navmap_path_file'])), b['navmap_path_file']
    elif 'indoor' not in os.path.basename(path) and 'outdoor' not in os.path.basename(path):
        # (params_indoor.yaml is the real robot's template: its map is the one thing to fill in;
        # outdoors the launch makes the NavMap of the place)
        assert b['navmap_path_file'], 'navmap_path_file is the map: set it'
    bonxai = load(path)['maps_manager_node']['ros__parameters'].get('bonxai')
    if bonxai and bonxai.get('package') == 'bigmap_bringup':
        assert os.path.isfile(os.path.join(ROOT, bonxai['bonxai_path_file']))


@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_simulation_flag_is_the_same_in_every_node(path):
    d = load(path)
    values = {n: v['ros__parameters']['use_sim_time'] for n, v in d.items()
              if isinstance(v, dict) and 'use_sim_time' in v.get('ros__parameters', {})}
    assert len(set(values.values())) == 1, values


FILTER_XML = os.path.join(plugins_src(), 'maps_managers', 'easynav_navmap_maps_manager')


@pytest.mark.skipif(not os.path.isdir(FILTER_XML), reason='easynav_navmap_maps_manager not found')
@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_every_filter_plugin_is_declared_by_easynav_navmap_maps_manager(path):
    declared = set()
    for xml in glob.glob(os.path.join(FILTER_XML, '*filter.xml')):
        with open(xml) as f:
            declared.update(re.findall(r'<class\s+name="([^"]+)"', f.read()))
    b = bigmap(path)
    for name in b['filters']:
        assert b[name]['plugin'] in declared, (name, b[name]['plugin'], sorted(declared))


@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_simulation_or_real_robot_as_the_file_is_meant(path):
    d = load(path)
    sim = d['system_node']['ros__parameters']['use_sim_time']
    assert sim == (os.path.basename(path) not in REAL_ROBOT)


@pytest.mark.parametrize('path', [p for p in CONFIGS if os.path.basename(p) in SIM_WITH_AMCL],
                         ids=os.path.basename)
def test_simulations_say_where_the_robot_starts(path):
    # the launch spawns the robot at localizer_node.amcl.initial_pose: without it, at (0, 0)
    pose = load(path)['localizer_node']['ros__parameters']['amcl']['initial_pose']
    float(pose['x'])
    float(pose['y'])


@pytest.mark.parametrize('path', CONFIGS, ids=os.path.basename)
def test_goal_tolerances_agree_between_system_and_controller(path):
    d = load(path)
    system = d['system_node']['ros__parameters']
    ctrl = d['controller_node']['ros__parameters']
    for name in ctrl['controller_types']:
        c = ctrl[name]
        if 'xy_goal_tolerance' in c:
            assert c['xy_goal_tolerance'] == system['position_tolerance'], name
            assert c['yaw_goal_tolerance'] == system['angle_tolerance'], name


def outdoor():
    return [p for p in CONFIGS if 'dem_generator' in load(p)]


@pytest.mark.parametrize('path', outdoor(), ids=os.path.basename)
def test_the_maps_manager_loads_the_navmap_the_generator_writes(path):
    d = load(path)
    gen = d['dem_generator']['ros__parameters']
    b = d['maps_manager_node']['ros__parameters']['bigmap']
    # (the launch passes its full path in the overrides file; the file says which it is)
    assert b['navmap_path_file'] == gen['navmap_file'] and not b['package']
    # the smallest NavCel is the DEM's node spacing (finer would only repeat nodes)
    assert b['cell_size']['min'] == gen['grid_resolution']


def dem_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'bigmap_dem', os.path.join(ROOT, 'bigmap_bringup', 'dem.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('path', outdoor(), ids=os.path.basename)
def test_no_generator_key_the_launch_does_not_read(path):
    """The `dem_generator` block is read by the launch (dem_generator_command): a key it does
    not know would be silently ignored."""
    launch = dem_module()
    gen = load(path)['dem_generator']['ros__parameters']
    unknown = sorted(k for k in flat(gen) if k not in launch.DEM_KEYS | launch.DEM_IGNORED_KEYS)
    assert not unknown, 'keys the launch does not read: %s' % unknown
