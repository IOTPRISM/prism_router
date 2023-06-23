#!/bin/bash

# script for first time setup
mkdir -p /opt/iotrimmer/logs
mkdir -p /opt/iotrimmer/dns-override
mkdir -p /opt/iotrimmer/static/custom-icons
# set nvram values
nvram set router_name=IoTrimmer
nvram set router_hostname=IoTrimmer
nvram set rc_status=/opt/iotrimmer/router_startup.sh
nvram set dnsmasq_options='dhcp-script=/opt/iotrimmer/register-device.sh
log-queries
log-facility=/opt/iotrimmer/dns-override/main_dnsmasq.log'
nvram set rc_startup='sleep 5 && /opt/iotrimmer/router-startup.sh &'
nvram set ath2_ssid=IoTrimmer
nvram set ath1_ssid=IoTrimmer
nvram set ath0_ssid=IoTrimmer
nvram set forward_spec='IoTrimDebug:on:both:5000>192.168.1.1:5000 IoTrimProd:on:both:90>192.168.1.1:90'
nvram set time_zone=Europe/London
nvram set iotrimmer_user=iotrimmer
nvram set iotrimmer_passwd=iotrimmer
nvram set no_crossdetect=1
nvram commit
cd /opt/iotrimmer
# create database
echo """from Database import Database
Database().create_database()""" | /opt/bin/python3
echo "First time setup complete"
