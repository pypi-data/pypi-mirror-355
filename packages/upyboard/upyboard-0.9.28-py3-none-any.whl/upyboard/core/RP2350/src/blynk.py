import sys
import time
import json
import usocket
import ubinascii

import machine
from umqtt.robust2 import MQTTClient


__version__ = "0.4.0"

print("""
    ___  __          __
   / _ )/ /_ _____  / /__
  / _  / / // / _ \\/  '_/
 /____/_/\\_, /_//_/_/\\_\\2@MQTT
        /___/ for Python v""" + __version__ + " (" + sys.platform + ")\n")


class BlynkMQTTClient:
    """
    Blynk MQTT Client for MicroPython
    """
    
    __DOWNLINK = "downlink/"
    __DOWNLINK_TOPIC_ALL = __DOWNLINK + "#"
    __DOWNLOAD_TOPIC_DS_HEADER = __DOWNLINK + "ds"
    __DOWNLOAD_TOPIC_UTC = __DOWNLINK + "utc/all/json"
    __DOWNLOAD_TOPIC_REBOOT = __DOWNLINK + "reboot"
    __UPLINK_TOPIC_DS_HEADER = "ds"
    __UPLINK_TOPIC_UTC = "get/utc/all/json"
    
    __USER_NAME = "device"

    def __init__(self, auth_token:str, server:str="blynk.cloud", keepalive:int=45, ssl:bool=False, verbose:bool=False):      
        """
        Blynk MQTT Client constructor\r
\1 auth_token: Blynk authentication token
        :param server: Blynk server address (default: blynk.cloud)
        :param keepalive: MQTT keepalive interval in seconds (default: 45)
        :param ssl: Use SSL/TLS (default: False)
        :param verbose: Enable verbose logging (default: False)
        """
          
        self.__blynk_server_name = server
        self.__blynk_server_port = 8883 if ssl else 1883
        self.__keeepalive = keepalive
        self.__ssl = ssl
        self.__verbose = verbose

        self.__blink_mqtt_client = MQTTClient(
            client_id=ubinascii.hexlify(machine.unique_id()).decode(),
            server=self.__blynk_server_name,
            port=self.__blynk_server_port,
            user=self.__USER_NAME,
            password=auth_token,
            ssl=self.__ssl,
            ssl_params={"server_hostname": self.__blynk_server_name} if self.__ssl else {}
        )

        self.__downlink_callbacks = {}
        self.__is_connected = False
        self.__last_ping = 0
    
    def __send_ping(self):
        """
        Send a ping to the MQTT broker to keep the connection alive.
        """
        
        if time.ticks_diff(time.ticks_ms(), self.__last_ping) > self.__keeepalive * 1000:
            self.__blink_mqtt_client.ping()
            self.__last_ping = time.ticks_ms()
                    
    def __on_message(self, topic:bytes, payload:bytes, retained:bool, duplicate:bool):
        """
        Callback function for incoming MQTT messages.\r
\1 topic: MQTT topic
        :param payload: MQTT payload
        :param retained: Retained message flag
        :param duplicate: Duplicate message flag
        """
        if self.__verbose:
            print(f"[MQTT RX] Topic={topic}, Msg={payload} ({type(payload)}), {retained=}, {duplicate=}")

        topic_str = topic.decode()
        payload_str = payload.decode()

        try:
            if "__all__" in self.__downlink_callbacks:    
                self.__downlink_callbacks["__other__"](topic_str, payload_str)
        
            elif topic_str.startswith(self.__DOWNLOAD_TOPIC_DS_HEADER):
                next_stream = topic_str[len(self.__DOWNLOAD_TOPIC_DS_HEADER)+1:]
                self.__downlink_callbacks[next_stream](payload_str)

            elif topic_str.startswith(self.__DOWNLOAD_TOPIC_UTC):
                self.__downlink_callbacks["utc"](payload_str)

            elif topic_str.startswith(self.__DOWNLOAD_TOPIC_REBOOT):
                self.__downlink_callbacks["reboot"]()
        except KeyError:
            pass

    def connect(self):
        """
        Connect to the Blynk MQTT broker.
        :return: True if connected, False otherwise
        """
        
        if self.__verbose:
            print(f"[MQTT] Connecting to {self.__blynk_server_name}:{self.__blynk_server_port} (TLS={self.__ssl})")

        try:
            usocket.getaddrinfo(self.__blynk_server_name, self.__blynk_server_port)
            self.__blink_mqtt_client.set_callback(self.__on_message)
            self.__blink_mqtt_client.DEBUG = self.__verbose
            self.__blink_mqtt_client.connect()
            self.__blink_mqtt_client.ping()
        except OSError as e:
            if self.__verbose:
                print("MQTT connection failed:", e)
            self.__blink_mqtt_client = None
            return False

        if self.__verbose:
            print("Connected to Blynk MQTT broker")

        self.__blink_mqtt_client.subscribe(self.__DOWNLINK_TOPIC_ALL.encode())
        if self.__verbose:
            print(f"Subscribed to '{self.__DOWNLINK_TOPIC_ALL}'")

        self.__is_connected = True
        self.__last_ping = time.ticks_ms()    
        return True

    def disconnect(self):
        """
        Disconnect from the Blynk MQTT broker.
        """
        
        if self.__is_connected:
            self.__blink_mqtt_client.disconnect()
            self.__is_connected = False
            self.__last_ping = 0
            if self.__verbose:
                print("Disconnected from MQTT broker")        

    def add_subscribe_callback(self, datastream:str, callback:callable):
        """
        Register a callback for a specific datastream.\r
\1 datastream: Datastream name
        :param callback: Callback function to be called when a message is received
        """
        
        self.__downlink_callbacks[datastream] = callback
        if self.__verbose:
            print(f"[SUB] Registered callback for '{datastream}'")

    def remove_subscribe_callback(self, datastream:str):
        """
        Remove the callback for a specific datastream.\r
\1 datastream: Datastream name
        """
        
        if datastream in self.__downlink_callbacks:
            del self.__downlink_callbacks[datastream]
            if self.__verbose:
                print(f"[SUB] Removed callback for '{datastream}'")

    def publish(self, datastream:str, value:str|int|float):
        """
        Publish a message to a specific datastream.\r
\1 datastream: Datastream name
        :param value: Value to be published (string, integer, or float)
        """
        
        topic, payload = f"{self.__UPLINK_TOPIC_DS_HEADER}/{datastream}", str(value)
        try:
            self.__blink_mqtt_client.publish(topic, payload)
            self.__last_ping = time.ticks_ms()    
                
            if self.__verbose:
                print(f"[MQTT TX] Topic={topic}, Payload={payload}")
        except Exception as e:
            raise Exception("MQTT publish error:", e)
        
    def get_utc(self):
        """
        Get the current UTC time from the Blynk server.
        
        :return: Dictionary containing the UTC time and timezone name
        """
        
        data = None
        
        def __on_utc(payload):
            nonlocal data
                    
            t_data = json.loads(payload)
            data = {"time":t_data["iso8601"], "zome":t_data["tz_name"]}

        self.add_subscribe_callback("utc", __on_utc)
        self.__blink_mqtt_client.publish(self.__UPLINK_TOPIC_UTC, '')
        while data is None:
            self.__blink_mqtt_client.check_msg()
            time.sleep_ms(100)
        self.remove_subscribe_callback("utc")
        return data
    
    def loop_forever(self):
        """
        Run the MQTT client loop indefinitely.
        """
        
        while self.__is_connected:
            self.__blink_mqtt_client.check_msg()
            self.__send_ping()
            time.sleep_ms(1)

    def loop(self):
        """
        Run the MQTT client loop for a short period.
        """
        
        if self.__is_connected:
            self.__blink_mqtt_client.check_msg()
            self.__send_ping()
