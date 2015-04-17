#!/usr/bin/env python

# General modules
import io
import sys
import zmq
import picamera
import socket
import datetime
import logging

# Project modules
import config
import motiondetection
import zmqoutput

log = logging.getLogger(__name__)
hostname = socket.gethostname()

def stills_event_loop(jpegsocket, camera, net_frame_size):
    """This function handles any incoming requests for JPEG stills.
    Any clients requesting stills receive back chunks of the file
    and must send continuation requests.
    """

    poller = zmq.Poller()
    poller.register(jpegsocket, zmq.POLLIN)

    jpeg_requests = {}

    while True:
        socks = dict(poller.poll())
        if jpegsocket in socks and socks[jpegsocket] == zmq.POLLIN:
            address, empty, req = jpegsocket.recv_multipart()

            if req == 'NEW':
                log.info('Request for JPEG still received from %s.', address)
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
                log.info('JPEG still transfer to %s acknowledged complete.', address)
                data = b''
        
            jpegsocket.send_multipart([address, b'', data])


def motion_event_handler(eventsocket):
    """Handle motion event using specified event socket.
    """
    log.info('Motion event detected.')
    eventsocket.send_multipart([hostname, 'MOTION:%s' % datetime.datetime.now().isoformat()])


def main():
    log.info('Starting camera feed server on %s.', hostname)
    
    configfile = 'config/cameraconfig.json'
    log.info('Loading config from %s.', configfile)
    configdata = config.load_from_file(configfile)
    
    magnitude_threshold = configdata['motion']['magnitude_threshold']
    block_threshold = configdata['motion']['block_threshold']

    bitrate = configdata['camera']['bitrate']
    framerate = configdata['camera']['framerate']

    net_frame_size = configdata['network']['net_frame_size']
    eventport = configdata['network']['event_pub_port']
    videoport = configdata['network']['h264_pub_port']
    jpegport = configdata['network']['jpeg_router_port']
    
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
         zmqoutput.ZeroMqOutput(videosocket, hostname, net_frame_size) as video_output, \
         motiondetection.VectorThresholdMotionDetect(motion_event_handler, 
                                                     magnitude_threshold,
                                                     block_threshold,
                                                     eventsocket,
                                                     camera) as motion_detector:

        log.info('Starting camera video capture.')
        camera.framerate = framerate
        camera.start_recording(video_output,
                               motion_output=motion_detector,
                               format='h264', 
                               inline_headers=True,
                               bitrate=bitrate)
        
        log.info('Entering JPEG still event loop.')        
        stills_event_loop(jpegsocket, camera, net_frame_size)



if __name__ == '__main__':
    
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    main()


