# run this file directly to start debug server
from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from apscheduler.schedulers.background import BackgroundScheduler
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from Network import Network
from Devices import Devices
from Products import Products
from Database import Database
from System import System
from Clock import Clock
from User import User
from BlocklistFetch import BlocklistFetch
from MacAddress import MacAddress
from DnsOverride import DnsOverride
from Traffic import Traffic, TrafficMetrics
from InterfaceColor import InterfaceColor
from TrafficSampler import TrafficSampler
import logging, sys, os, json


BLOCKLIST_FETCH_INTERVAL = 24 #hours
DATABASE_WIPE_INTERVAL = 168 #hours 

app = Flask(__name__)


@app.route('/login', methods=['GET', 'POST'])
def login():
    systm = System()
    user = User(systm.username, systm.password) 
    
    class LoginForm(FlaskForm):
        user_name  = StringField('UserName')
        password = PasswordField('Password')
        submit = SubmitField('Sign In')

    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        if user.name != form.user_name.data or user.password != form.password.data:
            return render_template('login.html', title = 'Sign In', form = form, error = True)
        login_user(user, remember = True)
        return redirect('/')
    return render_template('login.html', title = 'Sign In', form = form, error = False)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def fetch_blocklist():
    with Database() as cur:
        BlocklistFetch(cur).save()


fetch_blocklist()
os.environ["TZ"] = "Europe/London" #set timezone
schedule = BackgroundScheduler(daemon=True)
schedule.add_job(fetch_blocklist, 'interval', hours = BLOCKLIST_FETCH_INTERVAL) # scheduled job for pulling latest blocklists
schedule.add_job(lambda : Database().clear_database, 'interval', hours = DATABASE_WIPE_INTERVAL) #scheduled job for wiping db
schedule.start()


@login_manager.user_loader
def load_user(_):
    systm = System()
    return User(systm.username, systm.password) # we only ever have 1 user


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


@app.route('/index', methods=['GET'])
@app.route('/', methods=['GET'])
@login_required
def index():

    with Database() as cur:
        products = Products(cur)
        products.load_blocked()

        devices = Devices(cur).load_devices()
        devices.load_devices_destinations()
        devices.load_devices_locations()
        devices.update_connected()

        traffic = Traffic(cur)
        traffic.load_last_day_device_traffic(devices)

        trafficMetrics = TrafficMetrics(cur)

    return render_template('index.html',
                           devices = devices,
                           products = products,
                           clock = Clock(),
                           traffic = traffic,
                           trafficMetrics = trafficMetrics)


@app.route('/edit', methods=['POST'])
@login_required
def edit():
    # merge dictionaries
    data = dict(request.form)
    data.update(dict(request.files))

    with Database() as cur:
        devices = Devices(cur)
        devices.load_devices()

        for cmd, data in data.items():
            devices.set_device_properties(cmd, data)

    return redirect("/")


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    network = Network()
    system = System()
    trafficSampler = TrafficSampler()

    with Database() as cur:
        dnsOverride = DnsOverride(cur)

    interfaceColor = InterfaceColor()
    interfaceColor.load_color()

    if request.method == 'POST':
        data = request.form
        system.set_login_password(data['admin_password'])
        system.set_login_username(data['admin_username'])

        network.set_wifi_passphrase(data['passphrase'])
        network.set_wifi_ssid(data['ssid'])
        network.set_name_servers(data['nameservers'])
        network.save_changes()

        trafficSampler.set_interval(data['scanning_interval'])
        trafficSampler.set_window_size(data['scanning_window'])
        trafficSampler.restart()

        interfaceColor.set_color(data['color'])

    return render_template('settings.html',
                           network = network,
                           interfaceColor = interfaceColor,
                           system = System(),
                           trafficSampler = trafficSampler,
                           dnsOverride = dnsOverride)


@app.route('/<mac>_on', methods=['POST'])
@login_required
def deviceUp(mac):
    with Database() as cur:
        devices = Devices(cur).load_devices()
        devices.devices[MacAddress(mac)].activate(cur)
    return redirect("/")


@app.route('/<mac>_off', methods=['POST'])
@login_required
def deviceDown(mac):
    with Database() as cur:
        devices = Devices(cur).load_devices()
        devices.devices[MacAddress(mac)].deactivate(cur)
    return redirect("/")


@app.route('/<mac>_<data>_default', methods=['POST'])
@login_required
def setDefaultBlockingPolicy(mac, data):
    cmd = mac + '_set_default_blocking_policy'
    with Database() as cur:
        devices = Devices(cur).load_devices()
        devices.set_device_properties(cmd, data)
    return redirect("/")


@app.route('/dest-ctrl_<mac>_<dest>_<cmd>', methods=['POST'])
@login_required
def dest_ctrl(mac, dest, cmd):
    cmd = f"{mac}_allow_domains" if cmd == 'allow' else f"{mac}_block_domains" 
    with Database() as cur:
        devices = Devices(cur).load_devices()
        devices.set_device_properties(cmd, dest)
    return redirect("/")


@app.route('/<mac>_sniff_<cmd>', methods=['POST'])
@login_required
def toggle_sniff(mac, cmd):
    cmd = True if cmd == 'on' else False
    with Database() as cur:
        devices = Devices(cur).load_devices()
        devices.devices[MacAddress(mac)].toggle_sniff(cmd, cur)
    return redirect("/")

# used by a newly installed IoTrimmer app,
# a token is registered into the database for push notifications
# @app.route('/registerToken', methods=['POST'])
# def registerToken():
#     db.DBup()
#     sqlString = """ INSERT OR IGNORE INTO
#                         fcm_token (token)
#                     VALUES (:token);"""

#     token = request.data.decode("utf-8")
#     db.executeSql(sqlString, {"token": token})
#     db.DBdown()
#     return jsonify(success=True)


# @app.route('/getTrafficCsv', methods = ['POST'])
# def getTrafficCsv():
#     csv = traffic.exportTrafficCsv()
#     return Response(
#         csv,
#         mimetype="text/csv",
#         headers={"Content-disposition":
#                  "attachment; filename=trafficExport.csv"})


@app.route('/about/')
@login_required
def about():
    with Database() as cur:
        devices = Devices(cur).load_devices()
        devices.load_device_metrics()
    return render_template('about.html',
                           network = Network(),
                           dbMetrics = Database().metrics(),
                           devices = devices,
                           sys = System())

def main():
    try:
        debug = eval(sys.argv[1].split('=')[1])
    except IndexError:
        print(f"Script run with arguments: {sys.argv[1:]}")
        print("Script must be called with -debug=<True | False>")
        print(f"example: python3 {sys.argv[0]} -debug=True")
        exit(-1)

    logDir = "/opt/iotrimmer/logs/iotrimmer"
    logDir += "-debug.log" if debug else "-production.log"

    logLevel = logging.DEBUG if debug else logging.INFO
    port = 5000 if debug else 90
        
    logging.basicConfig(filename = logDir,
                        filemode = 'a',
                        format = '%(asctime)s - %(name)s %(levelname)s %(message)s',
                        datefmt = '%H:%M:%S',
                        level = logLevel)

    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.run(debug = debug, host = '0.0.0.0', port = port)


print("Hello")
if __name__ == "__main__":
    print("Hi")
    main()
