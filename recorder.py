#!/usr/bin/env python

# General modules
import zmq
import logging

# Project modules
import config


def main():
    hostname = socket.gethostname()
    log.info('Starting recording client on %s.', hostname)

    configfile = 'config/recorder.json'
    log.info('Loading config from %s.', configfile)
    configdata = config.load_from_file(configfile)

    cameraip = configdata['network']['camera_ip_addr']
    eventport = configdata['network']['event_sub_port']
    videoport = configdata['network']['h264_sub_port']

    context = zmq.Context()
    log.info('Connecting to camera event feed: %s:%i.', cameraip, eventport)
    eventsocket = context.socket(zmq.PUB)
    eventsocket.bind('tcp://*:%s' % eventport)

    log.info('Connecting to camera video feed: %s:%i.', cameraip, videoport)
    videosocket = context.socket(zmq.PUB)
    videosocket.bind('tcp://*:%s' % videoport)

    


if __name__ == '__main__':
    main()



