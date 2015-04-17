#!/usr/bin/env python

import logging
import numpy as np
import picamera
from picamera.array import PiMotionAnalysis

log = logging.getLogger(__name__)

class VectorThresholdMotionDetect(PiMotionAnalysis):

    def __init__(self, event_callback, magnitude_threshold, block_threshold, eventsocket, camera, size=None):
        super(VectorThresholdMotionDetect, self).__init__(camera, size)
        self.event_callback = event_callback
        self.magnitude_threshold = magnitude_threshold
        self.block_threshold = block_threshold
        self.eventsocket = eventsocket

    def analyse(self, a):
        magnitude_series = np.sqrt(np.square(a['x'].astype(np.float)) + 
                                   np.square(a['y'].astype(np.float))).clip(0, 255).astype(np.uint8)

        blocksoverthreshold = (magnitude_series > self.magnitude_threshold).sum()
        log.debug('Motion analysed. %i blocks over threshold %i.', blocksoverthreshold, self.block_threshold)
        if blocksoverthreshold > self.block_threshold:
            self.event_callback(self.eventsocket)


