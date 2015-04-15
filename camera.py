#!/usr/bin/env python

import io
import zmq
import picamera
import socket
import logging

log = logging.getLogger(__name__)

def video_send_loop(socket):
    """Read video stream from camera in blocks and publish 
    on ZeroMQ socket for recording and watching on other
    devices.
    """
    with picamera.PiCamera() as camera:
        with io.BytesIO() as buffer:
            camera.start_recording(buffer, format='h264', quality=23)
       
            while True: 
                data = buffer.read(4096)
                socket.send(data)
    


def main():
    hostname = socket.gethostname()
    log.info('Initialising camera feed.')
    
    port = 5869
    log.info('Binding ZeroMQ video port %s:%i', hostname, port)
    context = zmq.Context()

    videosocket = context.socket(zmq.PUB)
    videosocket.bind('tcp://*:%s' % port)

    video_send_loop(videosocket)

