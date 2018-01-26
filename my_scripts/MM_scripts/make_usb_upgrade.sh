#!/bin/bash
pwd
#----------------------------------------
# PATH Define
#----------------------------------------
TARGET_DEVICE=ktc_8g
TARGET_DIR=$(pwd)
#PRODUCT_BRAND=$(tr '[A-Z]' '[a-z]' <<<"$(get_build_var PRODUCT_BRAND)")
#TARGET_DIR=$ANDROID_BUILD_TOP/../images/marshmallow/$TARGET_DEVICE
#TARGET_DEVICE_DIR=$ANDROID_BUILD_TOP/device/$PRODUCT_BRAND/$TARGET_DEVICE
AUTO_UPDATE_SCRIPT=$TARGET_DIR/auto_update.txt
TMP_UPGRADE_FILE=TMP_348_DVBT_8G.bin
PADDED_BIN=$TARGET_DIR/padded.bin
PAD_DUMMY_BIN=$TARGET_DIR/dummy_pad.
UPGRADE_FILE=$TARGET_DIR/348_DVBT_8G.bin
SCRIPT_FILE=$TARGET_DIR/upgrade_script.txt

#lunch `print_lunch_menu | grep aosp_$TARGET_DEVICE-userdebug | cut -d. -f1`

#----------------------------------------
# Globe Value Define
#----------------------------------------
SECURE_UPGRADE=0
USB_CRC_CHECK=0
SPILT_SIZE=16384
SCRIPT_SIZE=0x4000 #16KB
PAD_DUMMY_SIZE=10240 #10KB
currentImageOffset=$SCRIPT_SIZE
MAGIC_STRING=12345678
FullUpgrade="n"
#CRC_SEGMENT_SIZE should align to 0x1000
CRC_SEGMENT_SIZE=0x200000 #2MB

function func_process_main_script()
{
    BUILD_TIME=`date '+%Y-%m-%d %T'`
    BUILD_PATH=`pwd`
    if [ "$USB_CRC_CHECK" == "1" ]; then
        echo "#-------------USB Check Integrity----------------" >> $SCRIPT_FILE
        echo "# CRC Segment Size : $CRC_SEGMENT_SIZE" >> $SCRIPT_FILE
    else
        echo "#-------------USB Upgrade Bin Info----------------" >> $SCRIPT_FILE
    fi
    echo "# Device : $TARGET_DEVICE" >> $SCRIPT_FILE
    echo "# Build PATH : $BUILD_PATH" >> $SCRIPT_FILE
    echo "# Build TIME : $BUILD_TIME" >> $SCRIPT_FILE

    fullUpgrade=$1
    if [ "$fullUpgrade" == "Y" ]  || [ "$fullUpgrade" == "y" ] ; then
        mainScript=$(grep -Ev "^$|#|%" $AUTO_UPDATE_SCRIPT)
    else
        #confirm each image is upgrade or not.
        mainScript=""
        tmp2="
"
        tmpScript=$(grep "^mstar" $AUTO_UPDATE_SCRIPT | grep "\[\[")
		
        for mainContent in $tmpScript
        do
            imageName=$(echo $mainContent | awk '{print $2}' | cut -d '/' -f 2)
            read -p "Upgrade $imageName? (y/N)" temp
            if [ "$temp" == "Y" ] || [ "$temp" == "y" ]; then
                mainScript=$mainScript$mainContent$tmp2
            fi
        done
        #pad set_config to usb script
        tmpScript=$(grep "set_config" $AUTO_UPDATE_SCRIPT)
        mainScript=$mainScript$tmpScript
    fi

    echo "UpgradeImage Generating....."
    for mainContent in $mainScript
    do
        if [ "$(echo $mainContent | awk '{print $1}')" == "mstar" ];then
            func_process_sub_script $(echo $mainContent|awk '{print $2}')
        else
            if [ "$mainContent" != "reset" ] && [ "$mainContent" != "printenv" ] && [ "$mainContent" != "% <- this is end of file symbol" ];then
                echo $mainContent >> $SCRIPT_FILE
            fi
        fi
    done
}

function func_process_sub_script()
{
    filePath=$1
    fileName=$(echo $1 | cut -d '/' -f 2 | cut -d '[' -f 3)
    echo "" >> $SCRIPT_FILE
    echo "# File Partition: "$fileName >> $SCRIPT_FILE
    filecontent=$(grep -Ev "^\s*$|#" $TARGET_DIR/$filePath)
    for subContent in $filecontent
    do
        if [ "$subContent" != "% <- this is end of file symbol" ] && [ "$subContent" != "sync_mmap" ]; then
            subContent_prefix=$(echo $subContent | awk '{print $1}')
            if [ "$subContent_prefix" == "tftp" ]; then
                DRAM_BUF_ADDR=$(echo $subContent | awk '{print $2}')
                imagePath=$(echo $subContent | awk '{print $3}')
                imageSize=$(stat -c%s $TARGET_DIR/$imagePath)
                printf "filepartload %s \$(UpgradeImage) 0x%x 0x%x\n" $DRAM_BUF_ADDR $currentImageOffset $imageSize >> $SCRIPT_FILE
                cat $TARGET_DIR/$imagePath >> $TMP_UPGRADE_FILE

                # align image to 0x1000(4K)
                ImageAlignSize=0
                NOT_ALAIN_IMAGE_SIZE=$(($imageSize & 0xfff))
                if [ $NOT_ALAIN_IMAGE_SIZE != 0 ]; then
                    ImageAlignSize=$((0x1000-$NOT_ALAIN_IMAGE_SIZE))
                    for ((i=0; i<$ImageAlignSize; i++))
                    do
                        printf "\xff" >>$PADDED_BIN
                    done

                    cat $PADDED_BIN >>$TMP_UPGRADE_FILE
                    rm $PADDED_BIN
                fi
                currentImageOffset=$(($currentImageOffset+$imageSize+$ImageAlignSize))
            else
                #fix ubi write 0x20400000 tvcustomer ${filesize} to ubi write 0x20400000 tvcustomer 0xfffff
                #Begin
                CMD=$(echo $subContent | awk '{print $2}')
                if [ "$CMD" == "write.p" ] || [ "$CMD" == "write.boot" ] || [ "$CMD" == "unlzo" ] || [ "$CMD" == "unlzo.cont" ] || [ "$CMD" == "write.e" ] || [ "$CMD" == "write" ]; then
                    #change 10 mechanism to 16 mechanism
                    imageSize_16=0x$(echo "obase=16; $imageSize" | bc)
                    imageAddr=$(echo "$DRAM_BUF_ADDR")
                    subContent=${subContent/'$(filesize)'/$imageSize_16}
                    subContent=${subContent/'${filesize}'/$imageSize_16}
                    subContent=${subContent/'${fileaddr}'/$imageAddr}
                fi
                #fix nand write.e ${fileaddr} recovery $(filesize) to nand write.e xxx recovery xxx
                #fix setenv recoverycmd nand read.e 0x25000000 recovery $(filesize) to setenv recoverycmd nand read.e 0x25000000 recovery xxx
                CMD_NAND=$(echo $subContent | awk '{print $1}')
                if [ "$CMD_NAND" == "ncishash" ] || [ "$CMD_NAND" == "setenv" ]; then
                    imageSize_16=0x$(echo "obase=16; $imageSize" | bc)
                    subContent=${subContent/'$(filesize)'/$imageSize_16}
                fi
                #End
                subContent=$(echo $subContent | tr -d '\r\n')
                echo $subContent >> $SCRIPT_FILE
            fi
        fi
    done
}

function func_init()
{
    # delete related file
    rm -f $SCRIPT_FILE
    rm -f $UPGRADE_FILE
    rm -f $TMP_UPGRADE_FILE
    ANDROID_BUILD_TOP=`pwd`
    export PATH=$PATH:$TARGET_DIR/crc
    dos2unix $AUTO_UPDATE_SCRIPT $TARGET_DIR/scripts/* 1>/dev/null 2>&1
}

function func_generate_script_file()
{
    echo "setenv 348_DVBT_8G_complete 1" >>$SCRIPT_FILE
    echo "setenv sync_mmap 1" >>$SCRIPT_FILE
    echo "setenv db_table 0" >>$SCRIPT_FILE
    echo "saveenv" >>$SCRIPT_FILE
    echo "printenv" >>$SCRIPT_FILE
    echo "% <- this is end of script symbol" >>$SCRIPT_FILE

    # pad script to script_file size
    SCRIPT_FILE_SIZE=$(stat -c%s $SCRIPT_FILE)
    PADDED_SIZE=$(($SCRIPT_SIZE-$SCRIPT_FILE_SIZE))

    printf "\xff" >$PAD_DUMMY_BIN
    for ((i=1; i<$PAD_DUMMY_SIZE; i++))
    do
        printf "\xff" >>$PAD_DUMMY_BIN
    done

    while [ $PADDED_SIZE -gt $PAD_DUMMY_SIZE ]
    do
        cat $PAD_DUMMY_BIN >> $SCRIPT_FILE
        PADDED_SIZE=$(($PADDED_SIZE-$PAD_DUMMY_SIZE))
    done

    if [ $PADDED_SIZE != 0 ]; then
        printf "\xff" >$PADDED_BIN
        for ((i=1; i<$PADDED_SIZE; i++))
        do
            printf "\xff" >>$PADDED_BIN
        done
        cat $PADDED_BIN >> $SCRIPT_FILE
        rm $PADDED_BIN
    fi
}

function func_generate_upgrade_file()
{
    # generate $UPGRADE_FILE
    cat $SCRIPT_FILE > $UPGRADE_FILE
    cat $TMP_UPGRADE_FILE >> $UPGRADE_FILE
    rm $TMP_UPGRADE_FILE

    # pad mangic to $UPGRADE_FILE
    printf "%s" $MAGIC_STRING >> $UPGRADE_FILE

    # pad $UPGRADE_FILE crc to $UPGRADE_FILE
    CRC_VALUE=`crc -a $SCRIPT_FILE | grep "CRC32" | awk '{print $3;}'`
    split -d -a 2 -b $SPILT_SIZE $SCRIPT_FILE $SCRIPT_FILE.
    printf "script file crc %s\n" $CRC_VALUE
    cat $SCRIPT_FILE.01 >> $UPGRADE_FILE
    rm -f $SCRIPT_FILE.*
    crc -a $UPGRADE_FILE

    # copy the first 16 bytes to last
    dd if=$UPGRADE_FILE of=./first16.bin bs=16 count=1;
    cat ./first16.bin >> $UPGRADE_FILE
    rm -f ./first16.bin
}

function parsing_para()
{
    while [ $# != 0 ]; do
        tmp1=$1
        tmp2=`echo $1|cut -d= -f1`
		echo "tmp1:$tmp1"
		echo "tmp2:$tmp2"
        case "$tmp2" in
        "FullUpgrade" )
            FullUpgrade=`echo $tmp1|cut -d= -f2`
            ;;
        * )
            echo "unknown parameter !!"
            exit 1
            ;;
        esac
        shift
    done

    if [ "$FullUpgrade" == "Y" ];then
        tmp=$FullUpgrade
    else
#         read -p "Full Upgrade? (Y/n)" tmp
tmp='Y'
    fi
}

function func_generate_secure_file()
{
    if [ "$SECURE_UPGRADE" == "1" ]; then
        local SECURE_TOOLDIR=$TARGET_DIR/secureboot
        local SECURE_UPGRADE_AES_KEY=$TARGET_DIR/AESupgrade.bin
        local SECURE_UPGRADE_RSA_PRIVATE_KEY=$TARGET_DIR/RSAupgrade_priv.txt
        local SECURE_UPGRADE_RSA_PUBLIC_KEY=$TARGET_DIR/RSAupgrade_pub.txt
        #segment size: 655360->640K; 2097152->2M; 5242880->5M
        local SECURE_SEGMENT_SIZE=2097152
        local SEGMENT_ENABLE=1

        #==============Pack.sh=================================
        cd $SECURE_TOOLDIR
        ./Pack.sh $SECURE_UPGRADE_RSA_PRIVATE_KEY $SECURE_UPGRADE_RSA_PUBLIC_KEY $SECURE_UPGRADE_AES_KEY $UPGRADE_FILE ./abc.bin $SEGMENT_ENABLE $SECURE_SEGMENT_SIZE
        cp -f abc.bin.aes $UPGRADE_FILE
        rm -rf abc.bin.aes abc.bin
        cd -
        #==============Pack.sh end=================================
    fi
}

############################### ktc add power on mode start ##############################
# select power on mode
echo "Select the power on mode:"
#select mode in direct secondary memory
#do
#       if [ -z $mode ] ; then
#               echo "you have select error num!"
#               continue
#       fi
	mode='direct'
       POWER_MODE=$mode
#       break;
#done
if [ ! -z "$POWER_MODE" ] ; then
       sed -i "s~\(factory_poweron_mode\).*~\1 $POWER_MODE~" $ANDROID_BUILD_TOP/../$TARGET_DIR/scripts/set_config
fi
printf "POWER_ON_MODE: $POWER_MODE\n"

############################# ktc add power on mode end ####################################

#-----------------------------------------------
# Main():Generate Upgrade Image via Tftp Script
#-----------------------------------------------
IFS="
"
func_init;
parsing_para $*;
func_process_main_script $tmp
func_generate_script_file;
func_generate_upgrade_file;
func_generate_secure_file;
