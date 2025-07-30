# recurse into the header directory
add_subdirectory(fastjet)

# local sources
list(APPEND fastjettools_SOURCES
  BackgroundEstimatorBase.cc 
  JetMedianBackgroundEstimator.cc 
  GridMedianBackgroundEstimator.cc 
  Recluster.cc 
  Filter.cc
  Pruner.cc
  Subtractor.cc
  MassDropTagger.cc
  RestFrameNSubjettinessTagger.cc
  CASubJetTagger.cc 
  JHTopTagger.cc
  TopTaggerBase.cc
)

#-------------------------------------------------------------------------
# main code 
add_library(fastjettools SHARED ${fastjettools_SOURCES})
target_link_libraries(fastjettools PUBLIC ${fastjet_LIBRARIES} fastjet)
target_include_directories(fastjettools 
                           PUBLIC 
                            $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                            $<INSTALL_INTERFACE:include>
                           )
add_library(fastjet::fastjettools ALIAS fastjettools)

# NB this is specifically for building scikit-hep/fastjet wheels
if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set_target_properties(fastjettools PROPERTIES INSTALL_RPATH "@loader_path")
else()
  set_target_properties(fastjettools PROPERTIES INSTALL_RPATH "$ORIGIN")
endif()

install(TARGETS fastjettools EXPORT FastjetTargets DESTINATION ${CMAKE_INSTALL_LIBDIR})
