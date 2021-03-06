#!/usr/bin/env python

import logging
import json

log = logging.getLogger(__name__)


def load_from_file(filename):
  """Read configuration from specified JSON file
  and return as python dictionary.
  """
  with open(filename, 'r') as configfile:
    log.info('Reading config from %s.', filename)
    return json.load(configfile)


