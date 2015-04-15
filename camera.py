#!/usr/bin/env python

# General modules
import io
import zmq
import picamera
import socket
import logging

# Project modules
import config
import motiondetection
import zmqoutput

log = logging.getLogger(__name__)

jpeg_requests = {}

def video_loop(videosocket, jpegsocket, eventsocket, config):
    """Read video stream from camera in blocks and publish 
    on ZeroMQ socket for recording and watching on other
    devices.
    """
                camera.start_recording(video_output, format='h264', motion_output=motion_detector)

                # The camera is up and running so now we poll JPEG request socket for
                # any requests for a JPEG still which is delivered piece by piece.
                poller = zmq.Poller()
                poller.register(jpegsocket, zmq.POLLIN)
                while True:
                    socks = dict(poller.poll())
                    if jpegsocket in socks and socks[jpegsocket] == zmq.POLLIN:
                        address, empty, req = jpegsocket.recv_multipart()
                        handle_jpeg_request(camera, jpegsocket, net_frame_size, address, req)


def handle_jpeg_request(camera, jpegsocket, net_frame_size, address, req):
    global jpeg_requests

    if req == 'NEW':
        if address in jpeg_requests:
            jpeg_requests[address].close()
            del jpeg_requests[address]

        # Create new stream and capture image to memory.
        jpeg_requests[address] = io.BytesIO()
        camera.capture(jpeg_requests[address], use_video_port=True)
        data = jpeg_requests[address].read(net_frame_size)

    elif req == 'NEXT':
        # Check for still in progress and send next frame.
        data = jpeg_requests[address].read(net_frame_size)

    elif req == 'ENDACK':
        # Transfer is complete and file acknowledged.
        data = b''
        
    jpegsocket.send_multipart([address, b'', data])


def main():
    hostname = socket.gethostname()
    log.info('Starting camera feed server on %s.', hostname)
    
    configfile = 'config/cameraconfig.json'
    log.info('Loading config from %s.', configfile)
    configdata = config.load_from_file(configfile)
    
    eventport = configdata['network']['event_pub_port']
    videoport = configdata['network']['h264_pub_port']
    jpegport = configdata['network']['jpeg_router_port']
    
    context = zmq.Context()
    log.info('Binding event socket to port %i.', eventport)
    eventsocket = context.socket(zmq.PUB)
    eventsocket.bind('tcp://*:%s' % eventport)
    
    log.info('Binding video socket to port %i.', videoport)
    videosocket = context.socket(zmq.PUB)
    videosocket.bind('tcp://*:%s' % videoport)

    log.info('Binding jpeg socket to port %i.', jpegport)
    jpegsocket = context.socket(zmq.ROUTER)
    jpegsocket.bind('tcp://*:%s' % jpegport)

    log.info('Assembling configuration variables.')
    magnitude_threshold = config['motion']['magnitude_threshold']
    block_threshold = config['motion']['block_threshold']

    bitrate = config['camera']['bitrate']
    framerate = config['camera']['framerate']

    net_frame_size = config['network']['net_frame_size']

    with picamera.PiCamera() as camera:
        with zmqoutput.ZeroMqOutput(videosocket, net_frame_size) as video_output:
    
            with motiondetection.VectorThresholdMotionDetect(motion_event_handler, 
                                                             magnitude_threshold,
                                                             block_threshold,
                                                             camera) as motion_detector:
        

    
                log.info('Entering video processing loop.')
                video_loop(camera, video_output, motion_detector)


if __name__ == '__main__':
    main()


