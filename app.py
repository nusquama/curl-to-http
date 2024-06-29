import json
import re
import shlex

def parse_curl_command(curl_command):
    # Replace newlines and multiple spaces with a single space
    curl_command = re.sub(r'\s+', ' ', curl_command.replace('\\\n', ' ').strip())
    
    # Split the command into tokens, respecting quoted strings
    tokens = shlex.split(curl_command)

    url = None
    method = "get"
    qs = []
    headers = []

    i = 1  # Skip 'curl'
    while i < len(tokens):
        token = tokens[i]
        if token in ['-X', '--request']:
            method = tokens[i + 1].lower()
            i += 2
        elif token in ['-H', '--header']:
            header = tokens[i + 1].split(':', 1)
            headers.append({"name": header[0].strip(), "value": header[1].strip()})
            i += 2
        elif token in ['-d', '--data', '--data-urlencode']:
            param = tokens[i + 1].split('=', 1)
            qs.append({"name": param[0], "value": param[1] if len(param) > 1 else ''})
            i += 2
        elif token.startswith('http'):
            url = token
            i += 1
        else:
            i += 1

    if not url:
        raise ValueError("Could not find URL in cURL command")

    return url, method, qs, headers

def generate_make_config(url, method, qs, headers):
    config = {
        "subflows": [
            {
                "flow": [
                    {
                        "id": 1,
                        "module": "http:ActionSendData",
                        "version": 3,
                        "parameters": {
                            "handleErrors": False,
                            "useNewZLibDeCompress": True
                        },
                        "mapper": {
                            "url": url,
                            "method": method,
                            "headers": headers,
                            "qs": qs,
                            "bodyType": "raw",
                            "parseResponse": True,
                            "authUser": "",
                            "authPass": "",
                            "timeout": "",
                            "shareCookies": False,
                            "ca": "",
                            "rejectUnauthorized": True,
                            "followRedirect": True,
                            "useQuerystring": False,
                            "gzip": True,
                            "useMtls": False,
                            "contentType": "application/json",
                            "data": "",
                            "followAllRedirects": False
                        },
                        "metadata": {
                            "designer": {
                                "x": 8,
                                "y": -158
                            },
                            "restore": {
                                "expect": {
                                    "method": {
                                        "mode": "chose",
                                        "label": method.upper()
                                    },
                                    "headers": {
                                        "mode": "chose"
                                    },
                                    "qs": {
                                        "mode": "chose"
                                    },
                                    "bodyType": {
                                        "label": "Raw"
                                    },
                                    "contentType": {
                                        "label": "JSON (application/json)"
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        ],
        "metadata": {
            "version": 1
        }
    }
    return json.dumps(config, indent=4)

def main():
    print("cURL to Make.com HTTP Module Converter")
    print("--------------------------------------")
    
    print("Enter your cURL command (press Enter twice when finished):")
    curl_command = ""
    while True:
        line = input()
        if line.strip() == "":
            break
        curl_command += line + "\n"
    curl_command = curl_command.strip()
    
    try:
        url, method, qs, headers = parse_curl_command(curl_command)
        make_config = generate_make_config(url, method, qs, headers)
        print("\nGenerated Make.com HTTP module configuration:")
        print(make_config)
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()