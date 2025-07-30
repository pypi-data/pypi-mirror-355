list(APPEND siscone_spherical_SOURCES
  geom_2d.cpp
  momentum.cpp
  hash.cpp
  vicinity.cpp
  protocones.cpp
  split_merge.cpp
  siscone.cpp)

#-------------------------------------------------------------------------
# headers
install(FILES 
  geom_2d.h
  momentum.h
  hash.h
  protocones.h
  siscone.h
  split_merge.h
  vicinity.h
  DESTINATION include/siscone/spherical)


#-------------------------------------------------------------------------
# main code
if (MSVC)
  add_library(siscone_spherical STATIC ${siscone_spherical_SOURCES})
else()
  add_library(siscone_spherical SHARED ${siscone_spherical_SOURCES})
endif()
target_link_libraries(siscone_spherical PUBLIC siscone)

# NB this is specifically for building scikit-hep/fastjet wheels
if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set_target_properties(siscone_spherical PROPERTIES INSTALL_RPATH "@loader_path")
elseif (NOT MSVC)
  set_target_properties(siscone_spherical PROPERTIES INSTALL_RPATH "$ORIGIN")
endif()

install(TARGETS siscone_spherical EXPORT SisconeTargets DESTINATION ${CMAKE_INSTALL_LIBDIR})

add_library(siscone::siscone_spherical ALIAS siscone_spherical)