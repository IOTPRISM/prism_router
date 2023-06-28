# PRISM Router Docker image

The image of the software can be downloaded here: https://liveuclac-my.sharepoint.com/:f:/g/personal/uceeam9_ucl_ac_uk/EoLg4IaFT95Pk223wwD2xo0B1NImw33hPPT3XuCISytAJQ 

This module is a Docker-packaged Debian image for performing anomaly detection on Internet of Things (IoT) network traffic. The anomaly detection algorithms are based on NetML library ([https://github.com/noise-lab/netml](https://github.com/noise-lab/netml))

### Prerequisites
Before proceeding with the deployment, ensure that you have Docker installed and running on your armv7l platform. If not, you can install it using the following commands:

```bash
sudo apt-get update
sudo apt-get install docker.io
```

Once you have Docker installed, follow these steps to run the Docker image for NetML-based IoT traffic classification:
1. Load the Docker image from the .tar.gz file:
```bash
docker load < netml_cli_armv7l_demo.tar.gz
```
2. The `/root` directory contains all .deb files of the necessary libraries for running netml on armv7l. These libraries are already installed on the current image. If you are running another docker image, you can copy those files and use `dpkg` to install .deb files:
```bash
sudo dpkg -i /path/to/library.deb
```
Replace `/path/to/library.deb` with the actual paths of your .deb files.

### Deploying the demo
1. Capture the required amount of IoT traffic for training and save it as a .pcap file (e.g., `train.pcap`). Use the `tcpdump` tool for this:
```bash
tcpdump -i wlan0 -w train.pcap
```
2. Use the `pcap2features.py` script to extract features from the `train.pcap` file. The extracted features are saved to the `normal-features.dat` file:
```bash
python3 pcap2features.py train.pcap
```
3. Run the `feature2model.py` script to create the OCSVM model. The model will be saved as `ocsvm.dat`
```bash
python3 feature2model.py
```
4. To run the anomaly detector in live mode, run the `capture.py` script:
```bash
python3 capture.py ocsvm.dat X
```
Replace `X` with a number of packets after which anomaly detection should be performed. E.g. X=1000 means anomaly classification is performed every 1000 packets. 
5. To run the anomaly detector on already captured traffic, use the `classify.py` script with the .pcap file as input:
```bash
python3 classify.py traffic.pcap
```
Replace `traffic.pcap` with your actual .pcap file name.

# Router-Software

## Introduction

This repository contains code that runs the app on a router running OpenWrt. It supports the following:
- device level dns-filtering
- automatic dns-filtering from a remote blocklist
- retrieving latest blocklist from a remote API
- traffic logging
- traffic location identification
- device product identification through a remote API
- device vendor lookup by mac
- a user web interface for device management and traffic visualization and system information.

The router software is a Python3 application that uses the Flask web framework. 

It requires the following:
- an instance off open-wrt (tested with dd-wrt)
- A USB drive (formatted as EXT2/3/4) with sufficient space must be mounted to `/opt/`.
- wifi access point(s)
- dnsmasq configured to log dns queries to `/opt/iotrimmer/dns-override/dnsmasq.log`
- dnsmasq configured to execute the callback script `/opt/iotrimmer/register-device.sh`.
- `router-startup` script to be executed at router boot
- ssh active (necessary for setup and development)
- remote access enabled

IoTrimmer may require a second USB drive formatted as linux swap. check swap is active with `free` command. This is useful especially if installing the python dependencies in `requiremnets.txt` as this is memory intensive.  

## High level design

The Flask app (`iotrimmer.py`) runs the user interface and allows the user to manage devices, block traffic and visualize traffic data. It is also responsible for running the blocklist fetch (`BlocklistFetch/py`) as a scheduled task.

A separate python process (`DnsLogger.py`) polls the dnsmasq logs and parses the traffic data into the database.

The DHCP server (dnsmasq) that runs on open-wrt is configured to run a callback script that is called whenever a new device is connected. The callback script is run by dnsmasq with 3 arguments, the hostname (optional), ip and mac. The script will add the newly connected device to the database, as well as doing various other task such as device identification, vendor lookup by mac and starting the DNS blocking for the nre device.

The software uses a relation database (`iotrimmer.db`) to store data about devices and their traffic. The database is a shared resource between the flask app, dns logging process and blocklist fetching process. The database is accessed by different parts of the software using a cursor object, which is passed between objects to maintain an open connection.

## Breakdown of Python objects

Most `.py` files contain 1 or more Python object which are imported into the main program `iotrimmer.py`. The `BlocklistFetch.py`, `DnsOverride.py`, `DnsLogger.py`, `iotrimmer.py` are written to be executed directly.

### BlocklistFetch.py

The blocklist contains the domains that should be blocked for each product. It is served through an API that returns a JSON list of blocked domains for each device on the blocklist. Each domain on the blocklist is associated with a party: first, third or support.

`BlocklistFetch.py` retrieves the latest blocklist from the remote API and parses the blocked domains into the database. The latest version number of the local blocklist is kept in the database under the `BLOCKLIST_VERSION` table. The blocklist will only be parsed into the database if the remote API returns a newer version number. 

When the object is initialized it will fetch the blocked domains. When the `save` method is called it delete all existing domains in the `BLOCKLIST` table and replace them with the updated domains.

### Clock.py

The clock object can return the current datetime as well as the datetime 24 hours ago. For the purposes of plotting the time-series traffic data, a list of times over the past 24 hours is required. The clock object will generate a time list of times at 10 minute intervals, with the final element being the current time rounded down to the nearest 10 minutes.

### Database.py

This file contains the schema for the router software database. It provides a context manager that returns a cursor to the database. It also provides functions for clearing all values in the database as well as creating a new database file.

By default the `Database.py` object operates on `/opt/iotrimmer/iotrimmer.db`. It will also work with other databases.

The object will also return metrics about the database file such as total destination count, distinct destination count, database size etc.

#### Database schema

The scheme contains the following tables:
- DEVICE : contains devices.
- PRODUCTS : contains device products.
- DESTINATION : contains a URL/destination/endpoint and its location and party data
- BLOCK_ALLOW : contains domains that are either blocked or explicitly allowed
- QUERIED : contains every query event for each device
- BLOCKLIST : contains the blocked domains retrieved from the API.
- BLOCKLIST_VERSION : contains a single row with the version number of the blocklist

The `BLOCK_ALLOW` table contains destinations that are explicitly blocked or explicitly allowed. THe domains may or may not appear in `BLOCKLIST` OR `QUERIED` but all domains that are in `BLOCKLIST` will be copied to `BLOCK_ALLOW`.

### Device.py

This object models a connected device. It inherits from the `DictObj` object and can be initialized from a dictionary. In the database a device may have a product and vendor of NULL. The object will convert these to "unknown" instead, so it can be displayed on the UI.

Changing attributes of a device is achieved by changing the attributes of the object and then calling the `update_database` method, which will save the changes permanently to the database. 

A device can have a custom icon (chosen by the user through the UI) or a default icon (chosen depending on the device's product). Setting a custom icon involves saving the uploaded image file, updating the `icon` path attribute of the device and updating the device in the database. 

A device's name can be set manually by the user. There is a method to auto-generate a name, which counts how many devices of the same product are in the database and uses that number creates a new name e.g. my-google-home-\*. If the product is unknown, the generated name is new-device-\*.

Setting a device's product involves removing the blocked destinations from the `BLOCK ALLOW` table, updating the object's product, adding the blocked destinations from the blocklist to the `BLOCK ALLOW` table, auto-generating a new name if necessary, updating the icon, saving the updated device to the database and synchronizing the DNS override.

The device class also provides an interface for blocking or allowing certain domains for specific devices. [^1] These methods will take a comma separated list of domains, identify the location for each one, save them to the `DESTINATION` table in the database, then add them directly to the DNS Override through the DnsOverride object.

The `set_default_blocking_policy` can configure the device so that new domains that are not explicitly allowed will be blocked by default. By default this attribute is set to false. It will first update the attribute, then update the database. The DnsLogger will alter its behaviour based on the updated column in the database.
Note that domains must first be queried before they can be blocked, and the DNS logger process only runs at a set time interval, so it is possible that domains may be queried multiple times before they are blocked.

The device class can also contains the locations of destinations queried by a device. There are methods that set, normalise and get locations. Setting is done by the `Devices.py` class. Normalising the locations scales the number of times a location has been visited between a maximum and minimum value. This is explained further in `Location.py`. 

The `activate` and ` deactivate` methods are used to enable or disable the DNS override for a specific device. They update the attribute of the object, update the object in the database and then change the behaviour of the DNS blocking through the `DnsOverride.py` class.

The class also provides various 'getter' methods. `get_iso_codes` will return a list of tuples containing the ISO code visited, and the numberof times it has been visited. `enumerate_blocked` returns all the blocked destinations ordered by name and `enumerate_allowed` assembles a set of all the domains and removes the blocked domains from it. This way it returns domains that are explicitly allowed and not just domains that have been queried. `print_product` displays the device's product in title case and with dashes replaced with whitespace.

### Device Classifier

This object is responsible for predicting the type of a device. The current method of device classification assembles 30 seconds woth of queried DNS requests from the `QUERIED` table, calculates their frequency, hashes the second level domain and sends the has-frequency pair as a JSON-ified list to the API. It assumes that the device has just connected, and operates after a delay, to allow enough DNS traffic to be captured. The `classify-device` method returns the predicted device from the API.

### Device Registrar

This object is responsible for logging a new device to the database when it is first connected to the IoTrimmer access point.The `DeviceRegistrar.py` file that contains the object is run as a script with `<mac> <ip>` and an optional `<hostname>` argument. It is called from the register `device script` which is called when a new DHCP lease is asigned to a device. The `register_device` method is the entry point for registering a device. It will first check if the device is in the database and will update the IP address if it has changed, otherwise it will exit. It will automatically generate a name and set the new name, it will then update the database. this must happen before the automatic identification because if the device is not in the database, the DNS logger cannot log domains to the database, and domains are required for the identification to work. 

The `_add_new_device` method will then attempt to identify the product and set the devices product should identification succeed.

Finally the object will initialise the DNS override for the newly connected device using the `DnsOverride` object.

### Devices

The `Devices` class acts as an iterable container for the device Objects. It accepts commands to modify the devices and propogates the changes to the relevant device object. The `load_devices` responsible for loading the devices from the database and initialising the device objects from the device data in the database. 

The `update_connected` method uses a shell object to find the MAC addresses of all connected devices and will update the `Device` objects accordingly. 

The `load_devices_destinations` finds the destinations that appear in the `BLOCK_ALLOW` table and those in the `QUERIED` table filtered by the MAC address of each device. These 2 lists of destinations are saved as attributes to each `Device` object.
In a similar way, the location of these destinations are saved to each `Device` object throug the `load_devices_locations` method and the `set_locations` method of the `Device` objects.

The `set_device_properties` method is responsible for interpreting commands from the UI. It checks tha command against a known list and executes the relevant functions. `_delete_device` first deletes all traffic data from the database for a particaulr device, updates the deleted attribute of the device (which mwans it will be ignored by the UI, DNS logger, auto name generator, DNS override etc.). It will then deactivate DNS override for the device. 

### DictObj

A helper object that allows a basic dictionary's attributes to be accessed with the `.` syntax aswell as the `[]` syntax. It can be initialised a dictionary (such as the dictionary-style database returned by the python sqlite3 fetchone function. It is useful to reduce the number of brackets in the templated html.

### DnsLogger

`DnsLogger` class parses dns logs to the database. Since it works with device specific logging, it will parse all logs in the `dns-override` directory. including device specific dnsmasq logs and the global log from the regular system dnsmasq.
It uses a line of bash to filter the log files for queries that are answered, and uses the IP address in the logs to identify the devices before logging them to the database. It turns the datetime string to a python datetime object, but it doesn't check include the year so a simple check is required to caclulate the year.

When the object adds a domain and its time to the `QUERIED` table of the database it checks if default blocking is enabled for the device and adds it to the `BLOCK_ALLOW` table if necessary. It then identifies the location of the destination through the `Locator` object and adds the data to the `DESTINATION` table. If the destination has already been identified, it is skipped. 

Times are saved to the database as Python datetime objets. IP addressea and MAC addresses are saved as an integer.

### DnsOverride

The `DnsOverride.py` file contains 2 objects, `DnsConfFile` models a dnsmasq config file. `DnsOverride` handles the dnsmasq processes and the iptables rules.
The DNS override works by running a separate dnsmasq process for each device, and redirecting the traffic from each connected device to the respective dnsmasq instance using iptables rules. 

#### DnsConfFile

On initialisation, `DnsConfFile` will create a new default file or read an existing file and load the blocked domains. A dns conf file looks like this:

bind-interfaces  
listen-address=127.53.185.19  
port=48895  
resolv-file=/tmp/resolv.dnsmasq  
cache-size=0  
log-queries  
log-facility=/opt/iotrimmer/dns-override/20:df:b9:13:e5:2e_dnsmasq.log  
address=/fcm.googleapis.com/  
address=/youtube-ui.l.google.com/  
address=/clientservices.googleapis.com/  
address=/storage.googleapis.com/  
address=/static.doubleclick.net/  
address=/googlevideo.com/  
address=/google-analytics.com/  

The addresses at the bottom of the file are the blocked domains. 

The dnsmasq instance has to run on a unique port and local IP address so devices do not collide with each other and use the same dnsmasq instance. A device's mac address is used to compute a unique port, IP pair, by using the second and third octets of the mac address to create a local IP address of the form 127.53.*.*
The port is calculated by adding the 4th and 5th octets of the mac address (in base 10) to the integer 48620. This means the same port and IP will always be calculated for the same device.

The DnsConfFile object loads the addresses in the file (if present) into memory and provides an `add` and `remove` interface to change them. Calling the `save_domains` method will update the domains in the actual conf file.

The `log-queries` and `log-facility` parameters in the config files set the query logging each devices queries are logged to their own log file, to be later read by the DNS logger process.

#### DnsOverride

The `DnsOverride` object controls the dnsmasq processes and the iptables rules. Upon initialisation it will find running dnsmasq processes and iptables rules and store them as dictionaries with a device's MAC address as the key. It provides an interface to start and stop specific dnsmasq processes, and bring iptables rules up or down, for example the deactivate method will kill the relevant dnsmasq process and remove the iptables rule.

The `sync` method will first kill the dnsmasq process, remove the blocked addresses from the DNS conf file, copy the blocked destinations found in the `BLOCK_ALLOW` table, save the domains to the DNS conf file through the `DnsConfFile` object. The dnsmasq process is then restarted.

### InterfaceColor

`InterfaceColor` sets the colour of the user interface. It edits css file directly.

### IpAddress

Models an IP address and can convert between string representation and a base 10 integer. Contains a hash dunder method so it can be used as a key in a dictionary, a comparator, a copy constructor and a converter function for storing the address in the database as a custom type.

### Locator

The `Locator.py` object contains the `Locator` class and the `Location` dataclass.

#### Locator

The `Locator` class is responsible for locating destinations. The `socket` python library is used resolve the destination and the Max Mind API is used to geolocate the IP address.

The API key must be kept in the `maxmind.key` file for the API to work, it is not stored in the git repository. The client number can be changed in the `Locator.py` file.

Certain errors for example the API running out of queries, non-resolvable address and address not in MaxMind database are logged and ignored.

The object will save the destination to the database, or update an existing destination.

#### Location

The `Location` object inherits from `dictObj` and holds the data for a destination, including its location. The normalise method will normalise the count of the object between maximum and minimum values given as arguments. The `to_normalised_list` method returns a list of the latitude, longitude and normalised count which is useful for displaying data on the UI.

### MacAddress

Models a MAC address and supports conversion between integer and string form. Contains a hash dunder method so it can be used as a key in a dictionary, a comparator, a copy constructor and a converter function for storing the address in the database as a custom type.

### Network

The `Network` class is responsible for acquiring network data from the system in order to display it on the user interface. It also handles changing network settings through the user interface, for example setting WiFi SSID, name servers etc.

This is mostly acheived using the `nvram` command line tool, after which the `save` method must be called in order to commit the changes permenantly. 

Upon initialisation the object will load information from the system including the hostname, information about different interfaces, public IP address and more.

The object also supports `print_*` methods which display data from the object in a UI friendly way.

### Products

The `Products` class maitains a list of products that are in the database. It loads these from the `PRODUCT` table and will also load the blocked destinations from the `BLOCKLIST` table. There are various getter fuctions to display this information on the UI.

### Shell

The `Shell` object is a executes commands on the command line and returns the output as a list of lines.

### System

The `System` class is responsible for acquiring data about the system, including cpu usage, mem usage, disk space etc. It executes bash commands and saves the results as attributes.

### Traffic

The `Traffic` class loads traffic data so that it can be plotted on the UI.. 

It loads  the blocked and queried traffic, aswell as loading traffic by the party type. It also loads device traffic through the `*_device_traffic` methods, which is accessed through a dictionary by the devices mac address. 

Accessing traffic by time is acheived by comparing the clock object to the text used to display the datetime in the database. Queries are grouped into 10 minute buckets by only considering the first characters of the string timestamp, not the final minute value. The character 0 is then appended to the timestamp

## User

This class is used by the flask-login module. it contains some required methods and attributes for flask-login to work. 
There is only 1 user.

### VendorLookup

This class identifies the vendor of a device from its MAC address. It uses the `mac_vendor_lookup` library and will log any errors. The only method is `find_vendor` which returns either None or the predicted vendor as a string.

## Other files and scripts..

### custom_errors.py

Various custom errors to make debugging a little easier.

### Application Entry Point

The `IoTrimmer.py` file starts the webapp and is run the argument `-debug=<True | False>` The debug option runs on port 5000 rather than 90, and will show errors to the user if they occur. The `fetch_blocklist` function is run every 14 hours using flask apscheduler's `BackgroundScheduler` object. 

### first-time-setup.sh

This is a utility script that configures a new instance of open-wrt to work with IoTrimmer. It relies on this repository having been cloned to `/opt/iotrimmer` already. It creates required directories, configures dd-wrt using `nvram` command line too, sets the DHCP callback script, sets dnsmasq logging, sets the startup commands, sets the access point names and other system settings and creates an empty database.
THe default username and password for the iotrimmer webui (and dd-wrt webui) are iotrimmer and iotrimmer.

### register-device.sh

This script acts as a bridge between the dnsmasq DHCP callback and the `DeviceRegistrar` class. It is responsible for checking the dns lease is new before registering the device, and acting as a logger for all DHCP activity.

### requirements.txt

python requirements file, install with `pip3 install -r requirements.txt`

### router-startup.sh

This script contains all the commands that must be run when the router first boots. To make development easier, it copies the `.bashrc` and `.vimrc` dotfiles to the home directory. This is because the while filesystem is not persistent across restarts, only the mounted USB drives. It bridges the port 90 and 5000 of the LAN interface to port 50 and 90 of the WAN interface.

It starts the `IoTrimmer.py`, `DnsLogger.py`, `DnsOverride.py` processes and configures the ipv4.conf.all.route_localnet option which is required for DNS override to work.

### utils.py

Various Python utility functions used throughout the software.

## Directory Structure

### dns-override

This folder contains auto-generated files. When IoTrimmer is running it will contain the dnsmasq conf files for each dnsmasq instance for each device with DNS blocking enabled. It also contains the query logs for each instance of dnsmasq and is the folder the DNS logger will look through ehrn logging queries.

### static

this folder contains static assets including custom and default product images, and non templated javascript.

### templates

Jinja2 templated html with some embedded javascript for the UI.

### tests

see testing

### util-scripts

anything useful to have that isn't strictly required for the iotrimmer.

## Logging

## Testing
