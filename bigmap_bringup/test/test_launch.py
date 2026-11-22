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

"""launch/bigmap.launch.py: which parameter file it gives EasyNav and RViz, and what it refuses,
taken by calling its setup() with launch arguments, without starting any process. Needs the
workspace built and sourced (the share directory of bigmap_bringup)."""

import importlib.util
import os

import pytest

launch = pytest.importorskip('launch')
pytest.importorskip('ament_index_python')
from ament_index_python.packages import get_package_share_directory  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCH_FILE = os.path.join(os.path.dirname(HERE), 'launch', 'bigmap.launch.py')


def module():
    spec = importlib.util.spec_from_file_location('bigmap_launch', LAUNCH_FILE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class FakeNode:
    """Stands for launch_ros' Node: keeps what the launch file gives it, as written."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.node_executable = kwargs['executable']


def setup(**given):
    """The nodes the launch starts with the declared defaults and `given` on top."""
    m = module()
    m.Node = FakeNode
    ctx = launch.LaunchContext()
    for action in m.generate_launch_description().entities:
        if isinstance(action, launch.actions.DeclareLaunchArgument):
            ctx.launch_configurations[action.name] = given.pop(action.name, None) or ''.join(
                s.perform(ctx) for s in action.default_value)
    assert not given, 'unknown launch arguments %s' % given
    return m.setup(ctx)


def params_of(node):
    """The parameters given to a Node, as the launch file wrote them (paths and dicts)."""
    return node.kwargs.get('parameters', [])


def share():
    try:
        return get_package_share_directory('bigmap_bringup')
    except Exception:
        pytest.skip('bigmap_bringup is not installed (build and source the workspace)')


def test_it_starts_easynav_and_rviz_and_nothing_else():
    share()
    nodes = setup()
    assert [n.node_executable for n in nodes] == ['system_main', 'rviz2']


@pytest.mark.parametrize('config', ['outdoor', 'indoor', 'parking_garage', 'large_warehouse',
                                    'two_floors'])
def test_each_config_is_its_own_parameter_file(config):
    path = os.path.join(share(), 'config', 'params_%s.yaml' % config)
    easynav = setup(config=config)[0]
    assert params_of(easynav) == [path]


def test_a_parameter_file_of_your_own_instead(tmp_path):
    share()
    mine = tmp_path / 'mine.yaml'
    mine.write_text('{}\n')
    assert params_of(setup(params_file=str(mine))[0]) == [str(mine)]


def test_use_sim_time_overrides_the_file_in_easynav_and_rviz():
    share()
    easynav, rviz = setup(use_sim_time='false')
    assert params_of(easynav)[1] == {'use_sim_time': False}
    assert params_of(rviz) == [{'use_sim_time': False}]
    easynav, rviz = setup()
    assert len(params_of(easynav)) == 1 and not params_of(rviz)


@pytest.mark.parametrize('given, message', [
    ({'config': 'nowhere'}, 'is not one of'),
    ({'params_file': '/no/such/file.yaml'}, 'does not exist'),
    ({'use_sim_time': 'yes'}, 'must be true, false'),
])
def test_what_it_refuses(given, message):
    share()
    with pytest.raises(RuntimeError, match=message):
        setup(**given)
