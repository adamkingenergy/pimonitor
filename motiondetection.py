#!/usr/bin/env python

import numpy as np
import picamera
import picamera.array

class VectorThresholdMotionDetect(picamera.array.PiMotionAnalysis):

    def __init__(self, event_callback, magnitude_threshold, block_threshold, camera, size=None):
        super(picamera.array.PiMotionAnalysis, self).__init__(camera, size)
        self.event_callback = event_callback
        self.magnitude_threshold = magnitude_threshold
        self.block_threshold = block_threshold

    def analyse(self, a):
        magnitude_series = np.sqrt(np.square(a['x'].astype(np.float)) + 
                                   np.square(a['y'].astype(np.float))).clip(0, 255).astype(np.uint8)

        if (magnitude_series > self.magnitude_threshold).sum() > self.block_threshold:
            self.event_callback()


