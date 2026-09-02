cmake_minimum_required(VERSION 3.8)
project(nori_description NONE)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY launch urdf ros2_control meshes rviz config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(
    test_rviz_configs
    test/test_description_rviz.py
  )
endif()

ament_package()
