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

"""EasyNav with the BigMap maps manager, and RViz: one parameter file, nothing else.

The robot (real, or simulated and launched before) provides the sensors, the odometry and the TF.

* config:=<name> is config/params_<name>.yaml of this package: outdoor, indoor, parking_garage,
  large_warehouse, two_floors. params_file:=<file> is any complete parameter file instead.
* use_sim_time:=true|false overrides the file's ('' keeps it).
* rviz:=false does not start RViz.
"""

import glob
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def configs(share):
    """The use cases: the names of config/params_<name>.yaml."""
    return sorted(os.path.basename(p)[len('params_'):-len('.yaml')]
                  for p in glob.glob(os.path.join(share, 'config', 'params_*.yaml')))


def params_file_of(share, config, params_file):
    """The parameter file: params_file if given, else config/params_<config>.yaml."""
    if params_file:
        path = os.path.abspath(os.path.expanduser(params_file))
        if not os.path.isfile(path):
            raise RuntimeError('params_file:=%s does not exist' % params_file)
        return path
    path = os.path.join(share, 'config', 'params_%s.yaml' % config)
    if not os.path.isfile(path):
        raise RuntimeError('config:=%s is not one of: %s' % (config, ', '.join(configs(share))))
    return path


def setup(context):
    share = get_package_share_directory('bigmap_bringup')

    def arg(name):
        return LaunchConfiguration(name).perform(context)

    params = [params_file_of(share, arg('config'), arg('params_file'))]
    sim_time = arg('use_sim_time')
    if sim_time not in ('', 'true', 'false'):
        raise RuntimeError("use_sim_time:=%s must be true, false or ''" % sim_time)
    if sim_time:
        params.append({'use_sim_time': sim_time == 'true'})
    rviz_config = arg('rviz_config') or os.path.join(share, 'rviz', 'bigmap.rviz')
    return [
        Node(package='easynav_system', executable='system_main', output='screen',
             parameters=params),
        Node(condition=IfCondition(LaunchConfiguration('rviz')), package='rviz2',
             executable='rviz2', output='screen', arguments=['-d', rviz_config],
             parameters=params[1:]),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('config', default_value='outdoor',
                              description='Use case: config/params_<config>.yaml'),
        DeclareLaunchArgument('params_file', default_value='',
                              description='A complete parameter file instead of config'),
        DeclareLaunchArgument('use_sim_time', default_value='',
                              description="true or false: overrides the file's ('' keeps it)"),
        DeclareLaunchArgument('rviz', default_value='true', description='Start RViz2'),
        DeclareLaunchArgument('rviz_config', default_value='',
                              description='RViz2 configuration. Default: rviz/bigmap.rviz'),
        OpaqueFunction(function=setup),
    ])
