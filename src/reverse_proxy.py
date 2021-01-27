#!/usr/bin/env python3

from flask import Flask
from flask import request,redirect,Response
from werkzeug.serving import WSGIRequestHandler
from werkzeug.exceptions import HTTPException, BadRequest, NotFound

import requests
import json

# From this package import these modules
from app import config
from app import util

# Assume http
orig_protocol = "http"

# Default load balancing algorithm, if
# not specified in the configuration file
load_balancing_algorithm_default = 'round-robin'


#
# Create app object
#
app = Flask(__name__)


# Use HTTP/1.1
WSGIRequestHandler.protocol_version = "HTTP/1.1"


#
# Routes
#

#
# Match root directory and set the default value for the path argument
#
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])

#
# The default converter captures a single string, but stops
# we need at slashes, so need to use the path converter to
# capture arbitrary length path and pass it to the path argument.
#
@app.route('/<path:path>', methods=['GET', 'POST'])
def reverse_proxy(path):

  print(f'#> reverse_proxy function')

  print(f'## request = {request}')

  algorithm = load_balancing.get('algorithm', load_balancing_algorithm_default)
  print(f'## load balancing algorithm = {algorithm}')

  service_domain = util.get_servicedomain_from_header(request)
  print(f'## service_domain = {service_domain}')

  content_type = util.get_contenttype_from_header(request)
  print(f'## content_type = {content_type}')

  #
  # Set headers to pass to origin
  #
  headers = {
    'Content-Type': content_type,
    'Host': service_domain
  }
  print(f'## headers sent to origin = {headers}')


  #
  # Look up service domain in services
  # and pick a backend
  #
  print(f'## look up service_domain in services and find an origin server')
  #print(f'services = {services}')


  #
  # Process the request
  #
  try:

    #
    # Find the configured service matching the host passed in
    # the Host header, and then select an origin host in that
    # service and get its IP address and port
    #
    orig_ep = ''
    candidates = []
    for service in services:
      candidates.append(service['domain'])
      if service['domain'] == service_domain:
        print(f'##   found service = {service}')
        orig_ep = util.select_origin(service, algorithm)
    if orig_ep == '':
      print(f'##   there is no configured service for service_domain {service_domain}')
      raise BadRequest(f"There is no service domain {service_domain}. Select one of {candidates}")

    #
    # Origin URL to which to send the request
    #
    url = f'{orig_protocol}://{orig_ep}/{path}'
    print(f'## origin_url = {url}')


    #
    # Send request to origin URL and get response
    #

    # Send request to origin
    if request.method == "GET":
      resp = requests.get(url, headers=headers)
    elif request.method == "POST":
      if content_type.lower() != 'application/json':
        raise BadRequest("POST method supports only JSON payload")
      else:
        # request JSON is a dict, not a JSON string, need JSON.
        data = json.dumps(request.json)
        print(f'## payload sent to origin = {data}')
        resp = requests.post(url, headers=headers, data=data)

    # Extract response from origin
    status = resp.status_code
    res = resp.content
    headers = util.filter_headers(resp.headers)

  except Exception as ex:
    print(f'## exception = \n##   {ex}')
    status = 404
    headers = {}
    res = f"ERROR: {str(ex)}\n"


  # Show status and result
  print(f'## status from origin = {status} for path {path}')
  print(f'## headers sent to client = {headers}')
  print(f'## result sent to client = \n##   {res}')

  
  #
  # Send the response to the client
  #
  #  response = result + status + headers
  #
  response = Response(res, status)
  if headers is not None:
    for name in headers.keys():
      value = headers[name]
      response.headers[name] = value

  print(f'#< reverse_proxy function')

  return response




#
# Main
#

if __name__ == '__main__':

  # Get listen and services
  (listen, services, load_balancing) = config.main()


  # Optional: add debug=True
  app.run(
    host=listen.get('address', '0.0.0.0'),
    port=listen.get('port', 8888)
  )
