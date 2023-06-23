#!/opt/bin/bash
sleep 1

# something to do with external USB drives
/opt/etc/init.d/rc.unslung start


# move useful conf files from /opt to read only filesystem
cp /opt/.vimrc /tmp/root/.vimrc
cp /opt/.bashrc /tmp/root/.bashrc

sleep 1

# start dns logger, iotrimmer and trafficSampler python processes
/opt/bin/python3 /opt/iotrimmer/DnsLogger.py > /opt/iotrimmer/logs/dnsLogger.log 2>&1 &
/opt/bin/python3 /opt/iotrimmer/IoTrimmer.py -debug=False &
/opt/bin/python3 /opt/iotrimmer/TrafficSampler.py > /opt/iotrimmer/logs/trafficSampler.log 2>&1 &

sleep 1

# run dns override python process to start blocking
/opt/bin/python3 /opt/iotrimmer/DnsOverride.py

# allow redirect between local IP addresses
/opt/sbin/sysctl -w net.ipv4.conf.all.route_localnet=1

