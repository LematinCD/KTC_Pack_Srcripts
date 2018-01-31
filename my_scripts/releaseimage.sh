#!/bin/bash
MODULE_NAME=$1
#split-fs-partition $PARTITION_NAME $PARTITION_SIZE $PARTITION_LZO
function split-fs-partition()
{
	
    echo -e "\033[31mSplit fs $1 partition...\033[0m"
    local PARTITION_NAME=$1
    local PARTITION_SIZE=$2
    local PARTITION_LZO=$3
	local PARTITION_MODULE_NAME=$4
	PRODUCT_OUT=../$PARTITION_MODULE_NAME
    # We only have about 200MB free memory for TFTP, and the compression ratio of lzo is > 75%.
    # Split size is 150MB better.
    local SPLIT_SIZE=157286400
    
    local count=$((($(stat -c %s $PRODUCT_OUT/$PARTITION_NAME.img)-1)/$SPLIT_SIZE+1))

    # Split image
    # this parameter 150m is related to SPLIT_SIZE, please modify both of them is you want to modify splited image size
    split -b 150m $PRODUCT_OUT/$PARTITION_NAME.img $PRODUCT_OUT/$PARTITION_NAME.img

    # Compress & Copy image
    local str="a b c d e f g h i j k l m n o p q r s t u v w x y z"
    local i=0
    for j in $str
    do
        for k in $str
        do
            if [ $i -ge $count ]; then
                break
            fi

            if [ "$PARTITION_LZO" == "true" ]; then
                 ./MM_scripts/lzop -f -o $PRODUCT_OUT/$PARTITION_NAME.img$j$k.lzo $PRODUCT_OUT/$PARTITION_NAME.img$j$k
				echo "$PARTITION_NAME.img$j$k.lzo"
            fi
            i=`expr $i + 1`
        done
    done   
}

split-fs-partition system 0x32000000 true $MODULE_NAME
