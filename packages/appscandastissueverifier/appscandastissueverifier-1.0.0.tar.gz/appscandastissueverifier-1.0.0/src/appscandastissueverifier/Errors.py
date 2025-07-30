#
# ****************************************************
# Licensed Materials - Property of HCL.
# (c) Copyright HCL America, Inc. 2025.
# Note to U.S. Government Users *Restricted Rights.
# ****************************************************
#

from .Logs import logger

# We're writing custom error handling to save the user from having to understand Python exceptions.
# TODO: Write an 'assert-like' function for expected errors?
def exception_wrapper(func):
    def new_func(*args, **kws):
        try:
            return func(*args, **kws)
        except Exception as caught_error:
            logger.error(f"!!! ERROR !!!: Execution failed with {type(caught_error).__name__}: {caught_error.args[0]}")
            # TODO: I still want the exception for my own debugging. Remove this at release.
            raise
            exit(0)
    
    return new_func
