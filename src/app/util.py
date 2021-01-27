#
# Utility functions in the app package
#
import random


#
# Get the service domain-name from the header
#
def get_servicedomain_from_header(request):

  h_name = request.headers.get('Host')
  if h_name is None:
    h_name = ''
  else:
    h_name = h_name.split(':')[0]
  return h_name


#
# Get the content-type from the header
#
def get_contenttype_from_header(request):

  c_type = request.headers.get('Content-Type')
  if c_type is None:
    c_type = 'text/html'
  return c_type


#
# Filter the headers received from origin in order
# to extract the headers to send back to the client
#
def filter_headers(hdrs):

    # Black list of headers to filter out
    stop_headers = ['content-encoding', 'content-length', 'transfer-encoding']

    headers = { k:v for (k, v) in hdrs.items() if k.lower() not in stop_headers}

    return headers


#
# Select one of the origin hosts using the
# specified algorithm (random or round-robin)
#
def select_origin(service, algorithm):

      n_h = len(service['hosts'])
      print(f'### number of origin hosts = {n_h}')

      # Select the index of next host
      if algorithm == 'random':
        # Random selection
        idx = random.randint(0, n_h-1)
        print(f'### randomly select host with index = {idx}')        
      else:
        # Round-robin selection
        idx = next_host(n_h)      
        print(f'### round-robin select host with index = {idx}')

      # Select origin host as host with index idx
      print(f'### selected host index = {idx}')
      selected = service['hosts'][idx]
      print(f'### selected_host = {selected}')

      # Set origin host endpoint
      #   orig_ep = {orig_host_address}:{orig_host_port}
      orig_address = selected['address']
      orig_port = selected['port']
      orig_ep = f'{orig_address}:{orig_port}'
      print(f'### orig_ep = {orig_ep}')

      return orig_ep


#
# Find next selected host for round-robin
#
def next_host(num_hosts):

  if next_host.value is None:
    next_host.value = 0
  else:
    next_host.value = (next_host.value + 1) % num_hosts

  return next_host.value


#
# Variable used by the next_host function
#
next_host.value = None

