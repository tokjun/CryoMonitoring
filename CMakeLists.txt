cmake_minimum_required(VERSION 2.8.9)

project(CryoMonitoring)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://www.example.com/Slicer/Extensions/CryoMonitoring")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "Junichi Tokuda (Brigham and Women's Hospital)")
set(EXTENSION_DESCRIPTION "This module computes T2* from two MR images with different TEs")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/CryoMonitoring.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/CryoMonitoring/Screenshots/1.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(ComputeT2Star)
add_subdirectory(ComputeTemp)
add_subdirectory(ComputeTempRelativeR2s)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
