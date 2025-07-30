# example main
add_executable(siscone_main options.cpp main.cpp)
target_link_libraries(siscone_main PUBLIC siscone)

# example area
add_executable(siscone_area options.cpp area.cpp)
target_link_libraries(siscone_area PUBLIC siscone)

# example test
add_executable(siscone_test options.cpp test.cpp)
target_link_libraries(siscone_test PUBLIC siscone)

# example times
add_executable(times options.cpp times.cpp)
target_link_libraries(times PUBLIC siscone)

# example sample
add_executable(sample options.cpp sample.cpp)
target_link_libraries(sample PUBLIC siscone)

# example spherical
add_executable(spherical options.cpp spherical.cpp)
target_link_libraries(spherical PUBLIC siscone_spherical)

if (MSVC)
  find_package(unofficial-getopt-win32 REQUIRED)
  target_link_libraries(siscone_main PRIVATE unofficial::getopt-win32::getopt)
  target_link_libraries(siscone_area PRIVATE unofficial::getopt-win32::getopt)
  target_link_libraries(siscone_test PRIVATE unofficial::getopt-win32::getopt)
  target_link_libraries(times PRIVATE unofficial::getopt-win32::getopt)
  target_link_libraries(sample PRIVATE unofficial::getopt-win32::getopt)
  target_link_libraries(spherical PRIVATE unofficial::getopt-win32::getopt)
endif()