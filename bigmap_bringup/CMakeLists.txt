cmake_minimum_required(VERSION 3.8)
project(bigmap_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch rviz maps DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  # the parameter files against each other and against the code that reads them
  ament_add_pytest_test(config_files test/test_config.py)
  # the launch file: which parameter file it gives EasyNav (no process is started)
  ament_add_pytest_test(launch_logic test/test_launch.py)
endif()

ament_package()
