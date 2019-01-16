#!/bin/sh
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_CXX_FLAGS="-DTBB_USE_GCC_BUILTINS=1 -D__TBB_64BIT_ATOMICS=0"  \
    -D ENABLE_VFPV3=ON -D ENABLE_NEON=ON  \
    -D BUILD_TESTS=OFF -D WITH_TBB=ON \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-3.2.0/modules \
    -D BUILD_EXAMPLES=OFF ..