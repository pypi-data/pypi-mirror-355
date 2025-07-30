#
# ****************************************************
# Licensed Materials - Property of HCL.
# (c) Copyright HCL America, Inc. 2025.
# Note to U.S. Government Users *Restricted Rights.
# ****************************************************
#
from types import SimpleNamespace
import urllib
import urllib.parse

from .Logs import logger
from .Errors import exception_wrapper
from .Utilities import http_response_to_string

ISSUE_STATUS_TYPES = {
    "NOT_FIXED" : 1,
    "FIXED"     : 0,
}
IssueStatus = SimpleNamespace(**ISSUE_STATUS_TYPES)

# TODO: Only supporting one validation method for now.
VALIDATION_METHODS = {
    "ERROR_STRING_IN_RESPONSE_BODY" : "ERROR_STRING_IN_RESPONSE_BODY",
    "HTTP_ERROR_IN_RESPONSE"     : "HTTP_ERROR_IN_RESPONSE",
}
Validation = SimpleNamespace(**VALIDATION_METHODS)

def _validate__error_string_in_response_body(response, validation_string):

    found_strings = [v_string for v_string in validation_string if v_string in response.text]
    if found_strings:
        first_found_string = found_strings[0]  # Get the first found string
        logger.info(f'Validation string "{first_found_string}" found in response body. The page is (likely) still vulnerable.')

        # Create response chunk:
        # TODO: Highlight the string again?
        response_string = http_response_to_string(response)
        found_index = response_string.index(first_found_string)
        before_lines = ['...'] + response_string[:found_index].splitlines()[-5:]
        after_lines = response_string[found_index:].splitlines()[:5] + ['...']
        reponse_chunk = '\n'.join(before_lines) + '\n'.join(after_lines)
        logger.debug(reponse_chunk)

        return True
    else:
        if len(validation_string) == 1:
            logger.info(f'Validation string "{next(iter(validation_string))}" was not found in the response, indicating that the issue might be resolved.')
        else:
            logger.info(f'None of the validation strings "{", ".join(validation_string)}" was found in the response, indicating that the issue might be resolved.')
        return False
    
def _validate__http_error_in_response(response, validation_string):
    status_codes = [v_string for v_string in validation_string if v_string == str(response.status_code)]
    if status_codes:
        status_code = status_codes[0]  # Get the first found status code
        logger.info(f'HTTP status code "{status_code}" was received in the response, indicating that the page might still be vulnerable.')

        # Create response chunk:
        response_string = http_response_to_string(response)
        response_lines = response_string.splitlines()[:10] + ['...']
        reponse_chunk = '\n'.join(response_lines)
        logger.debug(reponse_chunk)

        return True
    else:
        if len(validation_string) == 1:
            logger.info(f'HTTP status code "{next(iter(validation_string))}" was not found in the response, indicating that the issue might be resolved.')
        else:
            logger.info(f'None of the validation strings "{", ".join(validation_string)}" was found in the response, indicating that the issue might be resolved.')
        return False

def _check_response_status_code(response, request_url):
    
    logger.info("")
    # Check if the response status code is between 200 and less than 300, this means the response received is valid.
    if 200 <= response.status_code < 300:          
        unquoted_request_url = urllib.parse.unquote(request_url)
        unquoted_response_url = urllib.parse.unquote(response.url)
        if unquoted_request_url != unquoted_response_url:
            logger.info(f"Request URL ({unquoted_request_url}) and response URL ({unquoted_response_url}) do not match. This could be a sign of a redirect. Please check the session tokens or URL.")
    
    # Check if the response status code is between 300 and less than 400, this means the response received is a redirect.
    elif 300 <= response.status_code < 400:
        logger.info(f"Received HTTP status code {response.status_code} ({response.reason}). This could be a sign of a redirect. Please check the session tokens or URL.")
        
    # Check if the response status code is between 400 and less than 500, this means the response received is a client error.
    elif 400 <= response.status_code < 500:
        if response.status_code == 401:
            logger.info(f"Received HTTP status code {response.status_code} ({response.reason}). You're not authenticated to access the URL. Please check the session tokens.")
        elif response.status_code == 403:
            logger.info(f"Received HTTP status code {response.status_code} ({response.reason}). You're not authorized to access the URL. Please check the session tokens.")
        else:
            logger.info(f"Received HTTP status code {response.status_code} ({response.reason}). This could be a sign of a client error. Please check the session tokens.")
        
    # Check if the response status code is greater than or equal to 500, this means the response received is a server error.
    elif 500 <= response.status_code:
        logger.info(f"Received HTTP status code {response.status_code} ({response.reason}). This could be an internal server error OR a successful attack with issue still persisting. Please review all the request parameters.")


@exception_wrapper
def validate_attack_response(validation_method, response, validation_string, request_url):

    if validation_method == Validation.ERROR_STRING_IN_RESPONSE_BODY:
        issue_reproduced = _validate__error_string_in_response_body(response, validation_string)
        if not issue_reproduced:
            _check_response_status_code(response, request_url)
    elif validation_method == Validation.HTTP_ERROR_IN_RESPONSE:
        issue_reproduced = _validate__http_error_in_response(response, validation_string)
    else:
        # TODO: Replace with custom error function.
        raise ValueError("Invalid validation method")
    
    if issue_reproduced:
        exit_code = IssueStatus.NOT_FIXED
    else:
        exit_code = IssueStatus.FIXED
    return exit_code