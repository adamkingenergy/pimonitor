#!/usr/bin/env python

import zmq
import io

class ZeroMqOutput(object):
    def __init__(self, socket, framesize=4096):
        self.socket = socket
        self.framesize = framesize
        self.buffer = io.BytesIO()

    def _get_buffer_len(self):
        # Record where we are now.
        startpos = self.buffer.tell()
        
        # Go to the end of the buffer and tell the position.
        self.buffer.seek(0, io.SEEK_END)
        bufferlen = self.buffer.tell()
        
        self.seek(startpos)
        return bufferlen

    def write(self, s):
        # Add the incoming data to the buffer
        self.buffer.write(s)

        while self._get_buffer_len() >= self.framesize:
            self.socket.send(self.buffer.read(self.framesize)), zmq.SNDMORE)
            
    def flush(self):
        # Only use SNDMORE if we have strictly more data that framesize.
        # This leaves remaining data to be sent by final send (without SNDMORE)
        while self._get_buffer_len() > self.framesize:
            self.socket.send(self.buffer.read(self.framesize)), zmq.SNDMORE)

        self.socket.send(self.buffer.read())

