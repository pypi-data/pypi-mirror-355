#
# ****************************************************
# Licensed Materials - Property of HCL.
# (c) Copyright HCL America, Inc. 2025.
# Note to U.S. Government Users *Restricted Rights.
# ****************************************************
#
def _http_message_to_string(first_line, headers, body):
    output_lines = ['']
    # TODO: I'm logging the 'protocol' but I'm not actually using it, as it's taken from the url scheme.
    output_lines.append(first_line)
    output_lines.append("")
    for key, value in headers.items():
        output_lines.append(f"{key : <20}: {value}")
    output_lines.append("")
    output_lines.append(body)

    return '\n'.join(output_lines)

def http_request_to_string(method, path, protocol, headers, body):
    first_line = f"{method} {path} {protocol}"
    return _http_message_to_string(first_line, headers, body)

def http_response_to_string(response):
    status_code = response.status_code
    status_text = response.reason   
    headers = response.headers
    body = response.text

    # The requests module doesn't support any other protocol.
    protocol = "HTTP/1.1"

    first_line = f"{protocol} {status_code} {status_text}"
    return _http_message_to_string(first_line, headers, body)
