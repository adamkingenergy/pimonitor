#!/usr/bin/env python

# General modules 
import wx
import os
import io
import sys
import zmq
import datetime
import threading
import socket
import logging

# Project modules
from gui.imagepanel import ImagePanel
import config 

log = logging.getLogger(__name__)

class MonitorFrame(wx.Frame):
    """Frame holding image panel for monitor which runs maximised."""
 
    def __init__(self, hostname):
        """Constructor"""
        wx.Frame.__init__(self, None, title="Camera Monitor")
        
        self.hostname = hostname

        log.info('Loading network and monitor configuration files.')
        module_dir = os.path.dirname(__file__)
        self.network_config = config.load_from_file(os.path.join(module_dir, 'config/network.json'))
        self.monitor_config = config.load_from_file(os.path.join(module_dir, 'config/monitor.json'))

        log.info('Creating image panel.')
        self.panel = ImagePanel(self)
        self.ShowFullScreen(True)

        log.info('Starting image retrieval background thread.')
        self.thread = threading.Thread(target=self.image_retrieval_loop)
        self.thread.start()


    def image_retrieval_loop(self):
        reload_delay = self.monitor_config['image_reload_delay']
        camera_ip_addrs = self.monitor_config['camera_ip_addrs']

        eventport = self.network_config['event_pub_port']
        jpegport = self.network_config['jpeg_router_port']

        context = zmq.Context()

        eventsockets = []
        jpegsockets = {}
        jpegsocketstoip = {}

        for cameraip in camera_ip_addrs:
            log.info('Connecting to camera event feed: %s:%i.', cameraip, eventport)
            eventsocket = context.socket(zmq.SUB)
            eventsocket.connect('tcp://%s:%s' % (cameraip, eventport))
            eventsocket.setsockopt(zmq.SUBSCRIBE, '')
            eventsockets += [eventsocket]

            log.info('Connecting to camera JPEG feed: %s:%i.', cameraip, jpegport)
            jpegsocket = context.socket(zmq.REQ)
            jpegsocket.setsockopt(zmq.IDENTITY, self.hostname)
            jpegsocket.connect('tcp://%s:%s' % (cameraip, jpegport))
            jpegsockets[cameraip] = jpegsocket
            jpegsocketstoip[jpegsocket] = cameraip

        poller = zmq.Poller()
        for jpegsocket in jpegsockets.itervalues():
            poller.register(jpegsocket, zmq.POLLIN)

        for eventsocket in eventsockets:
            poller.register(eventsocket, zmq.POLLIN)

        ongoing_reqs = {}
        last_reqs = dict((ip, datetime.datetime.min) for ip in camera_ip_addrs)

        while True:
            socks = dict(poller.poll(100))
            for sock, status in socks.iteritems():
                if sock in jpegsockets.values() and status == zmq.POLLIN: 
                    data = sock.recv()
                    if data:
                        ongoing_reqs[jpegsocketstoip[sock]].write(data)
                        sock.send('NEXT')
                    else:
                        stream = ongoing_reqs[jpegsocketstoip[sock]]
                        stream.seek(0)
                        wx.CallAfter(self.panel.update_image, stream)
                        del ongoing_reqs[jpegsocketstoip[sock]]
                        sock.send('ENDACK')
                        sock.recv()

                elif sock in eventsockets and status == zmq.POLLIN: 
                    _ = sock.recv_multipart()
            
            for ip in camera_ip_addrs:
                if ip not in ongoing_reqs and datetime.datetime.now() > last_reqs[ip] + datetime.timedelta(seconds=reload_delay):
                    last_reqs[ip] = datetime.datetime.now()
                    ongoing_reqs[ip] = io.BytesIO()
                    jpegsockets[ip].send('NEW') 

 
if __name__ == "__main__":
    # Setup logging    
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    hostname = socket.gethostname()

    app = wx.App(False)
    frame = MonitorFrame(hostname)
    app.MainLoop()


