
list(APPEND fastjet_SOURCES
  DnnPlane.cc
  Dnn4piCylinder.cc
  Dnn3piCylinder.cc
  Dnn2piCylinder.cc
  ClusterSequence.cc
  PseudoJet.cc
  Selector.cc
  ClusterSequence_N2.cc
  ClusterSequence_TiledN2.cc
  ClusterSequence_Delaunay.cc
  ClusterSequence_DumbN3.cc
  ClusterSequence_CP2DChan.cc
  ClosestPair2D.cc
  MinHeap.cc
  ClusterSequenceAreaBase.cc
  ClusterSequenceActiveAreaExplicitGhosts.cc
  ClusterSequenceArea.cc
  GhostedAreaSpec.cc
  ClusterSequenceActiveArea.cc
  Voronoi.cc
  ClusterSequenceVoronoiArea.cc
  ClusterSequencePassiveArea.cc
  ClusterSequence1GhostPassiveArea.cc
  PseudoJetStructureBase.cc
  ClusterSequenceStructure.cc
  BasicRandom.cc
  JetDefinition.cc
  Error.cc
  AreaDefinition.cc
  RangeDefinition.cc
  CompositeJetStructure.cc
  FunctionOfPseudoJet.cc
  LimitedWarning.cc
  TilingExtent.cc
  LazyTiling9.cc
  LazyTiling9Alt.cc
  LazyTiling25.cc
  LazyTiling9SeparateGhosts.cc
  RectangularGrid.cc
)

#-------------------------------------------------------------------------
# main code 
add_library(fastjet SHARED ${fastjet_SOURCES})
if (FASTJET_ENABLE_CGAL)
  target_link_libraries(fastjet PUBLIC CGAL::CGAL)
endif()
target_include_directories(fastjet 
                           PUBLIC
                            $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
                            $<INSTALL_INTERFACE:include>
                           )
target_include_directories(fastjet 
                           PUBLIC
                            $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}/include>
                            $<INSTALL_INTERFACE:include>
                           )

add_library(fastjet::fastjet ALIAS fastjet)

install(TARGETS fastjet EXPORT FastjetTargets DESTINATION ${CMAKE_INSTALL_LIBDIR})
