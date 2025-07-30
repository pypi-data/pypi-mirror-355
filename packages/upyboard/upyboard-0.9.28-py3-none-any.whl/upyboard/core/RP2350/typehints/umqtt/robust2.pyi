from utime import ticks_ms, ticks_diff
from . import simple2


class MQTTClient(simple2.MQTTClient):
    DEBUG = False

    # Information whether we store unsent messages with the flag QoS==0 in the queue.
    KEEP_QOS0 = True
    # Option, limits the possibility of only one unique message being queued.
    NO_QUEUE_DUPS = True
    # Limit the number of unsent messages in the queue.
    MSG_QUEUE_MAX = 5
    # How many PIDs we store for a sent message
    CONFIRM_QUEUE_MAX = 10
    # When you reconnect, all existing subscriptions are renewed.
    RESUBSCRIBE = True

    def __init__(self, *args, **kwargs):
        """
        See documentation for `umqtt.simple2.MQTTClient.__init__()`
        """

    def is_keepalive(self) -> bool:
        """
        It checks if the connection is active. If the connection is not active at the specified time,
        saves an error message and returns False.

        :return: If the connection is not active at the specified time returns False otherwise True.
        """

    def set_callback_status(self, f):
        """
        See documentation for `umqtt.simple2.MQTTClient.set_callback_status()`
        """

    def cbstat(self, pid:int, stat:int):
        """
        Captured message statuses affect the queue here.

        stat == 0 - the message goes back to the message queue to be sent
        stat == 1 or 2 - the message is removed from the queue
        """

    def connect(self, clean_session:bool=True) -> bool:
        """
        See documentation for `umqtt.simple2.MQTTClient.connect()`.

        If clean_session==True, then the queues are cleared.

        Connection problems are captured and handled by `is_conn_issue()`
        
        :return: Existing persistent session of the client from previous interactions.
        """

    def log(self):
        """
        if DEBUG is True then print internal state
        """

    def reconnect(self):
        """
        The function tries to resume the connection.

        Connection problems are captured and handled by `is_conn_issue()`
        """

    def resubscribe(self):
        """
        Function from previously registered subscriptions, sends them again to the server.
        """

    def things_to_do(self) -> int:
        """
        The sum of all actions in the queues.

        When the value equals 0, it means that the library has sent and confirms the sending:
          * all messages
          * all subscriptions

        When the value equals 0, it means that the device can go into hibernation mode,
        assuming that it has not subscribed to some topics.

        :return: 0 (nothing to do) or int (number of things to do)
        """

    def add_msg_to_send(self, data):
        """
        By overwriting this method, you can control the amount of stored data in the queue.
        This is important because we do not have an infinite amount of memory in the devices.

        Currently, this method limits the queue length to MSG_QUEUE_MAX messages.

        The number of active messages is the sum of messages to be sent with messages awaiting confirmation.\r
\1 data:
        """


    def disconnect(self):
        """
        See documentation for `umqtt.simple2.MQTTClient.disconnect()`

        Connection problems are captured and handled by `is_conn_issue()`
        """

    def ping(self):
        """
        See documentation for `umqtt.simple2.MQTTClient.ping()`

        Connection problems are captured and handled by `is_conn_issue()`
        """

    def publish(self, topic:bytes, msg:bytes, retain:bool=False, qos:int=0) -> Optional[int]:
        """
        See documentation for `umqtt.simple2.MQTTClient.publish()`

        The function tries to send a message. If it fails, the message goes to the message queue for sending.

        The function does not support the `dup` parameter!

        When we have messages with the retain flag set, only one last message with that flag is sent!

        Connection problems are captured and handled by `is_conn_issue()`

        :return: None od PID for QoS==1 (only if the message is sent immediately, otherwise it returns None)
        """
 
    def subscribe(self, topic:bytes, qos:int=0, resubscribe:bool=True) -> int:
        """
        See documentation for `umqtt.simple2.MQTTClient.subscribe()`

        The function tries to subscribe to the topic. If it fails,
        the topic subscription goes into the subscription queue.

        Connection problems are captured and handled by `is_conn_issue()`
        """

    def send_queue(self) -> bool:
        """
        The function tries to send all messages and subscribe to all topics that are in the queue to send.

        :return: True if the queue's empty.
        """

    def is_conn_issue(self) -> bool:
        """
        With this function we can check if there is any connection problem.

        It is best to use this function with the reconnect() method to resume the connection when it is broken.

        You can also check the result of methods such as this:
        `connect()`, `publish()`, `subscribe()`, `reconnect()`, `send_queue()`, `disconnect()`, `ping()`, `wait_msg()`,
        `check_msg()`, `is_keepalive()`.

        The value of the last error is stored in self.conn_issue.

        :return: Connection problem
        """

    def wait_msg(self) -> Optional[int]:
        """
        See documentation for `umqtt.simple2.MQTTClient.wait_msg()`

        Connection problems are captured and handled by `is_conn_issue()`
        
        :return: check_msg()
        """

    def check_msg(self) -> Optional[int]:
        """
        See documentation for `umqtt.simple2.MQTTClient.check_msg()`

        Connection problems are captured and handled by `is_conn_issue()`
        """