#!/usr/bin/env bash
set -e

git submodule update --init --recursive

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -e ${DIR}/firmware/source/build ]; then
  rm -rf ${DIR}/firmware/source/build
fi
mkdir -p ${DIR}/firmware/source/build
cd ${DIR}/firmware/source/build

if [ -e ./u2if_CUSTOM_1V8.uf2 ]; then
  rm ./u2if_CUSTOM_1V8.uf2
fi
cmake .. -DBOARD=CUSTOM_1V8 -DIS_1V8=1
make -j$(nproc --all)
cp ./u2if_CUSTOM_1V8.uf2 ${DIR}/dist/u2if_1v8.uf2

if [ -e ./u2if_CUSTOM_3V3.uf2 ]; then
  rm ./u2if_CUSTOM_3V3.uf2
fi
cmake .. -DBOARD=CUSTOM_3V3 -DIS_1V8=0
make -j$(nproc --all)
cp ./u2if_CUSTOM_3V3.uf2 ${DIR}/dist/u2if_3v3.uf2

if [ -e ./u2if_SL6945_1V8.uf2 ]; then
  rm ./u2if_SL6945_1V8.uf2
fi
cmake .. -DBOARD=SL6945_1V8 -DIS_1V8=1
make -j$(nproc --all)
cp ./u2if_SL6945_1V8.uf2 ${DIR}/dist

if [ -e ./u2if_MD6976.uf2 ]; then
  rm ./u2if_MD6976.uf2
fi
cmake .. -DBOARD=MD6976 -DIS_1V8=0
make -j$(nproc --all)
cp ./u2if_MD6976.uf2 ${DIR}/dist

if [ -e ./u2if_SL69008_1V8.uf2 ]; then
  rm ./u2if_SL69008_1V8.uf2
fi
cmake .. -DBOARD=SL69008_1V8 -DIS_1V8=1
make -j$(nproc --all)
cp ./u2if_SL69008_1V8.uf2 ${DIR}/dist

if [ -e ./u2if_SL6925_1V8.uf2 ]; then
  rm ./u2if_SL6925_1V8.uf2
fi
cmake .. -DBOARD=SL6925_1V8 -DIS_1V8=1
make -j$(nproc --all)
cp ./u2if_SL6925_1V8.uf2 ${DIR}/dist

if [ -e ./u2if_SL6925_3V3.uf2 ]; then
  rm ./u2if_SL6925_3V3.uf2
fi
cmake .. -DBOARD=SL6925_3V3 -DIS_1V8=0
make -j$(nproc --all)
cp ./u2if_SL6925_3V3.uf2 ${DIR}/dist
