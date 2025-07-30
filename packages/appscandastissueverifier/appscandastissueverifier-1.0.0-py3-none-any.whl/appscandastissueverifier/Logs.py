#
# ****************************************************
# Licensed Materials - Property of HCL.
# (c) Copyright HCL America, Inc. 2025.
# Note to U.S. Government Users *Restricted Rights.
# ****************************************************
#
import sys
import logging
from types import SimpleNamespace


# We're wrapping everything with custom structs to make it easier on the user.
OUTPUT_STREAMS = {
    "STDERR" : sys.stderr,
    "STDOUT" : sys.stdout
}
OutputStream = SimpleNamespace(**OUTPUT_STREAMS) # This makes the dict keys accessible with '.'.

LOG_LEVELS = {
    "NONE" : logging.CRITICAL, # Since we're not logging anything critical, this effectively means nothing will be logged.
    "INFO" : logging.INFO,
    "DEBUG" : logging.DEBUG
}
LogLevel = SimpleNamespace(**LOG_LEVELS)

# TODO: When/if this is split into several modules, this will make sense (the logger name reflects the module running it)
logger = logging.getLogger(__name__)

def log_to_console(stream):
    assert stream in OUTPUT_STREAMS.values(), f"Log stream must be one of {['OutputStream.' + name for name in OUTPUT_STREAMS]}"
    stream_handler = logging.StreamHandler(stream)
    logger.addHandler(stream_handler)

def log_to_file(path):
    file_handler = logging.FileHandler(path)
    logger.addHandler(file_handler)

def set_log_level(level):
    assert level in LOG_LEVELS.values(), f"Log level must be one of {['LogLevel.' + name for name in LOG_LEVELS]}"
    logger.setLevel(level)
