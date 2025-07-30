#
# ****************************************************
# Licensed Materials - Property of HCL.
# (c) Copyright HCL Technologies Ltd. 2025.
# Note to U.S. Government Users *Restricted Rights.
# ****************************************************
#
from .Logs import logger
def compare_session_tokens(session_tokes, original_session_tokens):
    """
    Compare the session tokens with the original session tokens.
    Returns True if any token is found changed.
    """
    changed = False
    for token_key, token_dict in session_tokes.items():
        if token_key in original_session_tokens:
            for name, token in token_dict.items():
                if name in original_session_tokens[token_key]:
                    if token != original_session_tokens[token_key][name]:
                        changed = True
    if not changed:
       logger.warning("WARNING: Session tokens are same as the original ones. You might need to change the session tokens before sending the request.")