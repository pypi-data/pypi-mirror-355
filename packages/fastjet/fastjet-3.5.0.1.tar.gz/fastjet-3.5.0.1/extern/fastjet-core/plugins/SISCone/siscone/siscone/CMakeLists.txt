list(APPEND siscone_SOURCES
  ranlux.cpp
  reference.cpp
  geom_2d.cpp
  momentum.cpp
  hash.cpp
  quadtree.cpp
  vicinity.cpp
  protocones.cpp
  split_merge.cpp
  siscone.cpp
  siscone_error.cpp
  area.cpp)

#-------------------------------------------------------------------------
# headers
install(FILES area.h
  circulator.h
  defines.h
  geom_2d.h
  hash.h
  momentum.h
  protocones.h
  quadtree.h
  ranlux.h
  reference.h
  siscone_error.h
  siscone.h
  split_merge.h
  vicinity.h
  ${CMAKE_CURRENT_BINARY_DIR}/config.h
  DESTINATION include/siscone)


#-------------------------------------------------------------------------
# main code
if (MSVC)
  add_library(siscone STATIC ${siscone_SOURCES})
else()
  add_library(siscone SHARED ${siscone_SOURCES})
endif()
target_include_directories(siscone
                           PUBLIC
                            $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}>
                            $<INSTALL_INTERFACE:include>
                           )
target_include_directories(siscone
                           PUBLIC
                            $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}>
                            $<INSTALL_INTERFACE:include>
                           )
target_link_libraries(siscone PUBLIC ${siscone_LIBRARIES})
install(TARGETS siscone EXPORT SisconeTargets DESTINATION ${CMAKE_INSTALL_LIBDIR})

# for packages that submodule siscone (e.g. fastjet)
add_library(siscone::siscone ALIAS siscone)
#-------------------------------------------------------------------------
# spherical version
add_subdirectory(spherical)
