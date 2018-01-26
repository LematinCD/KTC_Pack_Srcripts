#!/bin/bash

echo -e "开始打包 images "

export LD_LIBRARY_PATH=./my_lib
MODULE_NAME=$1
echo $MODULE_NAME
pwd
./MM_scripts/make_ext4fs -T -1 -S ./MM_scripts/file_contexts -L system -l 0x32000000 -a system ../$MODULE_NAME/system.img ../$MODULE_NAME/system ../$MODULE_NAME/system
./SN_scripts/make_ext4fs -S ./SN_scripts/file_contexts -l 0x1A00000 -a tvconfig ../$MODULE_NAME/tvconfig.img ../$MODULE_NAME/tvconfig
./SN_scripts/make_ext4fs -S ./SN_scripts/file_contexts -l 0x1600000 -a tvdatabase ../$MODULE_NAME/tvdatabase.img ../$MODULE_NAME/tvdatabase

echo -e "打包images成功"

./MM_scripts/releaseimage.sh $MODULE_NAME

echo -e "转换img文件成功，输出到image目录"


#rm system.*
#rm tvconfig.*
#rm tvdatabase.*
cp ./MM_scripts/make_usb_upgrade.sh ../$MODULE_NAME
cd ../images_test
pwd
./make_usb_upgrade.sh
pwd
echo -e "升级文件成功制作"

#rm system.*
#rm tvconfig.*
#rm tvdatabase.*

#echo -e "\n***************************************************"
#echo -e " Make Time：" `date +"%F %H:%M:%S"` 
#echo -e "***************************************************\n"
