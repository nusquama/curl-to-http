import json
import re
import shlex
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS  # Add this import

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>cURL to Make.com Converter</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        textarea { width: 100%; height: 100px; margin-bottom: 10px; }
        #result { white-space: pre-wrap; background-color: #f0f0f0; padding: 10px; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>cURL to Make.com Converter</h1>
    <form id="curlForm">
        <textarea id="curlCommand" placeholder="Enter your cURL command here"></textarea>
        <br>
        <button type="submit">Convert</button>
    </form>
    <div id="result"></div>

    <script>
        document.getElementById('curlForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const curlCommand = document.getElementById('curlCommand').value;
            console.log('Sending curl command:', curlCommand);  // Log the command being sent
            fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ curl_command: curlCommand }),
            })
            .then(response => {
                console.log('Response status:', response.status);  // Log the response status
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data);  // Log the received data
                document.getElementById('result').innerText = JSON.stringify(data, null, 2);
            })
            .catch((error) => {
                console.error('Error:', error);
                document.getElementById('result').innerText = 'Error: ' + error.message;
            });
        });
    </script>
</body>
</html>
"""

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
    return config

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/convert', methods=['POST'])
def convert_curl_to_make():
    data = request.json
    app.logger.info(f"Received data: {data}")  # Log the received data
    curl_command = data.get('curl_command')
    
    app.logger.info(f"Received curl command: {curl_command}")  # Log the received command
    
    if not curl_command:
        app.logger.error("No cURL command provided")
        return jsonify({"error": "No cURL command provided"}), 400
    
    try:
        url, method, qs, headers = parse_curl_command(curl_command)
        make_config = generate_make_config(url, method, qs, headers)
        app.logger.info(f"Generated config: {make_config}")  # Log the generated config
        return jsonify(make_config)
    except ValueError as e:
        app.logger.error(f"ValueError: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=3000)
