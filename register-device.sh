#!/bin/sh
[ $1 == "add" ] && /opt/bin/python3 /opt/iotrimmer/DeviceRegistrar.py $2 $3 $4

TIME=$(date +"%T")
[ $1 == "add" ] && echo "$TIME - New lease: $2 $3 $4" >> /opt/iotrimmer/logs/dhcp.log
[ $1 == "old" ] && echo "$TIME - Existing lease found: $2 $3 $4" >> /opt/iotrimmer/logs/dhcp.log
[ $1 == "del" ] && echo "$TIME - Lease destroyed: $2 $3 $4" >> /opt/iotrimmer/logs/dhcp.log

# used for debugging
#[ $1 == "old" ] && /opt/iotrimmer/DeviceRegistrar.py $2 $3 $4
