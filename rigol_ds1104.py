
'''

This script will handle setting and getting the ABSOLUTE MINIMUM parameters required to control the CNT alignment system.
Different oscilloscopes may be used, but which one is used will be abstracted to the main script.

'''

# standard python libraries #

import logging
logging.basicConfig(level=logging.DEBUG)		# enable debug messages
import time
import sys

import socket           # required to communicate via scpi

# project libraries #

import soft_lib_rigol_ds1104.config as config

class rigol_ds1104():

    socket_ip = config.socket_ip_address                            # fixed ip at the current lab setup, may change.
    socket_port = config.socket_port                                # default port for the OWON XDS3104AE
    device_id = "RIGOL TECHNOLOGIES,DS1104Z "                       # device ID


    sock = None                                     # placeholder for the not yet existing socket

# class methods #########################


    channel1 = "channel1"
    channel2 = "channel2"
    channel3 = "channel3"
    channel4 = "channel4"
    channels = [channel1, channel2, channel3, channel4]

    scales = ["0.1","0.2","0.5","1","2","5","10","20"]
    attennuations = ["0.001X","0.002X","0.005X","0.01X","0.02X","0.05X","0.1X","0.2X","0.5X","1X","2X","5X","10X","20X","50X","100X","200X","500X","1000X"]


    def __init__(self):
        logging.debug("__init__ method was called")

        # creating the socket
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # what does this mean??
        except socket.error:
            logging.warning("failed to create socket")
            sys.exit();
        logging.debug("socket created")


    def connect(self):
        logging.debug("connect method was called")

        # connecting to remote:
        try:
            self.sock.connect((self.socket_ip, self.socket_port))  # attention !!! socket takes a TUPLE as input parameter
            self.connected = True  # enable connected flag, used to keep track of connection
        except socket.error:
            logging.warning("Failed to connect to ip " + self.socket_ip)
        logging.debug("socket connected")
        return self.connected

    def send_command(self, cmd_str):
        logging.debug("send_command method was called")
        logging.debug(cmd_str)
        cmd_str = cmd_str + '\n'
        cmd = cmd_str.encode('utf-8')
        try:
            self.sock.sendall(cmd)
            time.sleep(
                0.2)  # FASTER THAN 0.5 GIVS PROBLEMS WITH SOME COMMANDS !!! # maybe not necessary??? check how to do this async.
        except socket.error:
            logging.error("Socket Failed to send")
            logging.error("QUITTING")
            sys.exit()

    def receive_command(self):
        logging.debug("receive_command method was called")
        reply = self.sock.recv(4096)  # ATTENTION !!! DATA SIZE IS LIMITED HERE, THIS WON'T WORK WITH BIG WAVEWFORMS !!!
        reply.replace(b'\n', b' ')
        logging.debug(reply)
        reply_str = reply.decode('utf-8')

        return (reply_str)

    def get_device_id(self):                # to be sure we connected to the right oscilloscope
        self.send_command("*IDN?")
        return(self.receive_command())


    def confirm_device_id(self):
            id = self.get_device_id()
            logging.debug(id)
            ret = None
            logging.debug(id.find(self.device_id))
            if (id.find(self.device_id) != -1):  # instance of the device id found
                ret = True
            else:
                ret = False
            return (ret)

    def reset(self):
        self.send_command("*rst")
    def autoset(self):                   # in order for the measurements to be accurate, we first need to set the osc to the right range.
        self.send_command(":autoset on")
        time.sleep(4)                      # autoset takes some time, so better to wait for some seconds until everything stabilizes
    def get_max_voltage(self,channel):      # only two parameters necessary max voltage and frequency
        command = ":measurement:"
        command = command + channel + ':'
        command = command + "max?"
        self.send_command(command)
        response = self.receive_command()
        response = response.split(': ')
        response = response[1]
        millis = False
        if(response[5] == "m"):
            millis = True
        response = response[0:4]
        response = float(response)
        if(millis == True):
            response = response/1000
        return (response)

    def get_frequency(self, channel):                # getting the frequency parameter
        command = ":measurement:"
        command = command + channel + ':'
        command = command + "freq?"
        self.send_command(command)
        response = self.receive_command()
        response = response.split(': ')
        response = response[1]
        kilo = 0
        if(response[5] == "K"):
            kilo = 1
        response = response[0:4]
        try:
            response = float(response)
            if(kilo == 1):
                response = response * 1000
        except:
            logging.warning("Failed measuring frequency")
            response = "?"
        return (response)

    def set_time_scale(self, scale):
        command = ":horizontal:scale "
        command = command + scale
        self.send_command(command)

    def set_probe_atten(self,channel,atten):
        command = ":" + channel
        command = command + ":probe "
        command = command + atten
        logging.debug(command)
        self.send_command(command)

    def set_amplitude_scale(self,channel,scale):
        command = ":" + channel
        command = command + ":scale "
        command = command + scale
        logging.debug(command)
        self.send_command(command)

    def set_y_offset(self, channel, offset):
        command = ":" + channel
        command = command + ":offset "
        command = command + offset
        logging.debug(command)
        self.send_command(command)


    def set_default_values(self):
        self.reset()
        #self.autoset()
        #time.sleep(2)  # autosetting the oscilloscope takes a little IMPROVE IT BY JUST GIVING THE RIGHT CONFIGURATION
        self.set_time_scale("50us")
        self.set_probe_atten(channel="ch1", atten="1X")
        self.set_probe_atten(channel="ch2", atten="1X")

        self.set_y_offset(channel = "ch1", offset = "0")
        self.set_y_offset(channel = "ch2", offset = "0")


        self.set_amplitude_scale(channel = "ch1", scale = "2V")
        self.set_amplitude_scale(channel = "ch2", scale = "500mV")


    def test(self):
        for channel_val in self.channels:
            for scale_val in self.scales:
                print("changing amplitude scale on "+ str(channel_val) + " to " + str(scale_val))
                self.set_amplitude_scale(channel=channel_val, scale=scale_val)
                time.sleep(1)


# MAIN FUNCTION ########################################################

if __name__ == "__main__":


    osc = rigol_ds1104()
    osc.connect()
    print("confirming device id")
    print(osc.confirm_device_id())

    osc.autoset()
    time.sleep(1)

    osc.test()

    # for channel_val in channels:
    #     for atten_val in atten_list:
    #         print("changing probe attenuation values")
    #         osc.set_probe_atten(channel = channel_val, atten = atten_val)
    #         time.sleep(.1)



    # for i in range(1,100):
    #     volt = osc.get_max_voltage("ch1")
    #     print(volt)
    #     freq = osc.get_frequency("ch1")
    #     print(freq)
    #