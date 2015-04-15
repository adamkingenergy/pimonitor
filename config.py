#!/usr/bin/env python

import logging
import json

log = logging.getLogger(__name__)


def load_from_file(filename):
  """Read configuration from specified JSON file
  and return as python dictionary.
  """
  log.info('Reading configuration from %s.', filename)
  with open(filename, 'r') as configfile:
    return json.load(configfile)


