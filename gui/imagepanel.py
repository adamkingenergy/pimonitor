#!/usr/bin/env python

import wx
import logging

log = logging.getLogger(__name__)
 
class ImagePanel(wx.Panel):
    """This panel displays the images from the monitored camera."""
 
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)
        self.bitmap = wx.StaticBitmap(self, wx.ID_ANY, wx.EmptyBitmap(640, 480))
        self.Bind(wx.EVT_LEFT_UP, self.on_click)
 
    def on_click(self, event):
        """Click event handler to check where was clicked and dispatch relevant event."""
        # Here we add behaviour to check click position and
        # take appropriate action.
        pass

    def update_image(self, image_stream):
        """Update the bitmap with the specified stream."""
        log.debug('Updating image from stream.')
        self.bitmap.SetBitmap(wx.BitmapFromImage(wx.ImageFromStream(image_stream)))

 
