
from flask import Flask, request, jsonify, render_template_string
import json
import re
import shlex
import os

app = Flask(__name__)

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

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    if request.method == 'POST':
        curl_command = request.form['curl_command']
        try:
            url, method, qs, headers = parse_curl_command(curl_command)
            result = generate_make_config(url, method, qs, headers)
        except Exception as e:
            result = f"Error: {str(e)}"

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>cURL to Make.com HTTP Module Converter</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
                h1 { color: #333; }
                form { margin-bottom: 20px; }
                textarea { width: 100%; height: 150px; }
                pre { background-color: #f4f4f4; padding: 10px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>cURL to Make.com HTTP Module Converter</h1>
            <form method="post">
                <textarea name="curl_command" placeholder="Enter your cURL command here">{{ request.form['curl_command'] }}</textarea>
                <br><br>
                <input type="submit" value="Convert">
            </form>
            {% if result %}
                <h2>Result:</h2>
                <pre>{{ result }}</pre>
            {% endif %}
        </body>
        </html>
    ''', result=result)

@app.route('/api/convert', methods=['POST'])
def api_convert():
    data = request.json
    if not data or 'curl_command' not in data:
        return jsonify({"error": "No cURL command provided"}), 400

    try:
        url, method, qs, headers = parse_curl_command(data['curl_command'])
        result = generate_make_config(url, method, qs, headers)
        return jsonify({"result": json.loads(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
