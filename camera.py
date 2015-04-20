#!/usr/bin/env python

# General modules
import io
import os
import sys
import zmq
import picamera
import socket
import datetime
import logging

# Project modules
import config
from motion.motiondetection import VectorThresholdMotionDetect
from data.zmqoutput import ZeroMqOutput

log = logging.getLogger(__name__)
hostname = socket.gethostname()

def stills_event_loop(jpegsocket, camera, net_frame_size, hostname, annotation, annotation_strftime):
    """This function handles any incoming requests for JPEG stills.
    Any clients requesting stills receive back chunks of the file
    and must send continuation requests.
    """

    poller = zmq.Poller()
    poller.register(jpegsocket, zmq.POLLIN)

    jpeg_requests = {}

    while True:
        socks = dict(poller.poll(100))
        if jpegsocket in socks and socks[jpegsocket] == zmq.POLLIN:
            address, empty, req = jpegsocket.recv_multipart()

            if req == 'NEW':
                log.info('Request for JPEG still received from %s.', address)
                if address in jpeg_requests:
                    jpeg_requests[address].close()
                    del jpeg_requests[address]

                # Create new stream and capture image to memory.
                jpeg_requests[address] = io.BytesIO()
                camera.capture(jpeg_requests[address], format='jpeg', use_video_port=True)
                jpeg_requests[address].seek(0)
                data = jpeg_requests[address].read(net_frame_size)

            elif req == 'NEXT':
                # Check for still in progress and send next frame.
                data = jpeg_requests[address].read(net_frame_size)

            elif req == 'ENDACK':
                # Transfer is complete and file acknowledged.
                log.info('JPEG still transfer to %s acknowledged complete.', address)
                data = b''
        
            jpegsocket.send_multipart([address, b'', data])

        annotation_data = {'hostname': hostname, 'datetime': datetime.datetime.now().strftime(annotation_strftime)}
        camera.annotate_text = annotation % annotation_data


def motion_event_handler(eventsocket):
    """Handle motion event using specified event socket.
    """
    log.info('Motion event detected.')
    eventsocket.send_multipart([hostname, 'MOTION', datetime.datetime.now().isoformat()])


def main():
    log.info('Starting camera feed server on %s.', hostname)
    
    module_dir = os.path.dirname(__file__) 
    
    motion_config = config.load_from_file(os.path.join(module_dir, 'config/motion.json'))
    camera_config = config.load_from_file(os.path.join(module_dir, 'config/camera.json'))
    network_config = config.load_from_file(os.path.join(module_dir, 'config/network.json'))
    
    magnitude_threshold = motion_config['magnitude_threshold']
    block_threshold = motion_config['block_threshold']

    bitrate = camera_config['bitrate']
    framerate = camera_config['framerate']
    resolution = camera_config['resolution_x'], camera_config['resolution_y']
    vflip = True if camera_config['vflip'] else False
    hflip = True if camera_config['hflip'] else False
    annotation = camera_config['annotation']
    annotation_strftime = camera_config['annotation_strftime']

    net_frame_size = network_config['net_frame_size']
    eventport = network_config['event_pub_port']
    videoport = network_config['h264_pub_port']
    jpegport = network_config['jpeg_router_port']
    
    context = zmq.Context()
    log.info('Binding event publish socket to port %i.', eventport)
    eventsocket = context.socket(zmq.PUB)
    eventsocket.bind('tcp://*:%s' % eventport)
    
    log.info('Binding video publish socket to port %i.', videoport)
    videosocket = context.socket(zmq.PUB)
    videosocket.bind('tcp://*:%s' % videoport)

    log.info('Binding JPEG router socket to port %i.', jpegport)
    jpegsocket = context.socket(zmq.ROUTER)
    jpegsocket.bind('tcp://*:%s' % jpegport)

    with picamera.PiCamera() as camera, \
         ZeroMqOutput(videosocket, hostname, net_frame_size) as video_output, \
         VectorThresholdMotionDetect(motion_event_handler, 
                                     magnitude_threshold,
                                     block_threshold,
                                     eventsocket,
                                     camera) as motion_detector:

        log.info('Starting camera video capture.')
        camera.resolution = resolution
        camera.framerate = framerate
        camera.vflip = vflip
        camera.hflip = hflip
        camera.start_recording(video_output,
                               motion_output=motion_detector,
                               format='h264', 
                               inline_headers=True,
                               bitrate=bitrate)
        
        try:
            log.info('Entering JPEG still event loop.')
            stills_event_loop(jpegsocket, camera, net_frame_size, hostname, annotation, annotation_strftime)
        finally:
            camera.stop_recording()


if __name__ == '__main__':
    # Setup logging    
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Start main execution
    main()


