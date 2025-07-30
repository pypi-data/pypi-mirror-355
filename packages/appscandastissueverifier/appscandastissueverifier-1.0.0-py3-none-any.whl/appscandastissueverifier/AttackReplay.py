#
# ****************************************************
# Licensed Materials - Property of HCL.
# (c) Copyright HCL America, Inc. 2025.
# Note to U.S. Government Users *Restricted Rights.
# ****************************************************
#
import urllib
import requests

from .Logs import logger
from .Errors import exception_wrapper
from .Utilities import http_request_to_string, http_response_to_string


def _replace_hosts(original_host, replay_host, headers):
    original_scheme, original_domain, _, _, _ = urllib.parse.urlsplit(original_host)

    replay_host = replay_host.strip('/')

    # Covering the case where the user replaces the domain but doesn's specify http/https.
    # We use the original url's scheme in this case.
    if "://" not in replay_host:
        replay_host = urllib.parse.urlunsplit((original_scheme, replay_host, '', '', ''))

    replay_scheme, replay_domain, null_path, null_query, null_fragment = urllib.parse.urlsplit(replay_host)
    # TODO: Replace with custom assert as mentioned in TODO above. Also make this not terrible.
    assert null_path == null_query == null_fragment == '', "Replay host must only contain scheme and domain."
    
    replaced_headers = {}
    for key, value in headers.items():
        # Replace all occurrences including the scheme:
        replaced_value = value.replace(original_host, replay_host)

        # Replace all occurrences not including the scheme:
        replaced_value = replaced_value.replace(original_domain, replay_domain)

        replaced_headers[key] = replaced_value

    return replay_host, replaced_headers

# TODO: There's potential for duplication/discrepency with the dict in ScriptGenerator.py.
SESSION_HEADER_SEPARATORS = { # Values are: separator between name and token; separator between two name-token pairs.
    "Cookie" : ('=', '; '),
    "Authorization" : (' ', ' ')
}

# TODO: Technically there could be multiple headers with the same key and I don't support that here (nor in the parsing).
def _replace_session_tokens(headers, session_tokens):
    replaced_headers = headers

    for header_key, token_dict in session_tokens.items():
        name_token_separator, token_pair_separator = SESSION_HEADER_SEPARATORS[header_key]
        token_pairs = []
        for name, token in token_dict.items():
            token_pair = name_token_separator.join((name, token))
            token_pairs.append(token_pair)
        
        header_value = token_pair_separator.join(token_pairs)
        replaced_headers[header_key] = header_value

    return replaced_headers

def _construct_url(host, path):
    # Remove the host from the path if it exists
    if path.startswith(host):
        path = path[len(host):]

    # Ensure the path starts with a single slash
    if not path.startswith("/"):
        path = "/" + path

    # Concatenate host and path
    return host + path

@exception_wrapper
def send_attack_request(protocol,
                        original_host,
                        replay_host,
                        path,
                        method,
                        session_tokens,
                        headers,
                        body,
                        original_response_status_code):
    
    host, headers = _replace_hosts(original_host, replay_host, headers)
    headers = _replace_session_tokens(headers, session_tokens)

    request_url = _construct_url(host, path)
    logger.info("")
    logger.info(f"Sending attack to: {request_url}")

    #headers = auth_headers | other_headers

    # TODO: I'm logging the 'protocol' but I'm not actually using it, as it's taken from the url scheme.
    request_string = http_request_to_string(method, path, protocol, headers, body)
    logger.debug(request_string)

    response = requests.request(method = method,
                                url = request_url,
                                headers = headers,
                                data = bytes(body, 'utf-8'),
                                )
    
    status_code = response.status_code
    status_text = response.reason
    logger.info(f"Received response from: {response.url} {status_code} {status_text} ")
    logger.info(f"Original response status code was {original_response_status_code} and current response status code is {response.status_code}.")

    
    response_string = http_response_to_string(response)
    logger.debug(response_string)
    logger.info("")

    return response, request_url

