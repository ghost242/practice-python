import yaml
import logging
from logging.config import dictConfig

def accept_conf():
  f = open("python_log_conf.yml")
  conf = yaml.safe_load(f)
  f.close()
  
  dictConfig(conf)

def write_log():
  logger = logging.getLogger()
  logger.warning("Hello!")
  """
  > WARNING:root:Hello!
  """

accept_conf()
write_log()
