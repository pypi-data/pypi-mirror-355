include(FindPackageHandleStandardArgs)
set(${CMAKE_FIND_PACKAGE_NAME}_CONFIG ${CMAKE_CURRENT_LIST_FILE})
find_package_handle_standard_args(taily CONFIG_MODE)

if(NOT TARGET taily::taily)
  find_package(Boost REQUIRED)
  include("${CMAKE_CURRENT_LIST_DIR}/tailyTargets.cmake")
endif()
