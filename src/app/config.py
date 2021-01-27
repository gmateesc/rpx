#!/usr/bin/env python3

from pathlib import Path
import yaml

# Location of config file
config_file = {
   #
   # description of this dict object
   #
   'description': 'Reverse proxy config',
   #
   # system level config file
   #
   'system_file_path': '/etc/rpx/reverse_proxy.yaml',
   #
   # default config file: its path is relative
   # to the directory where the package is installed
   #
   'default_file_path': 'config/reverse_proxy.yaml'
}


#
# Extract config from the reverse proxy config file
#
def get_config( conf_file ):

  if Path(conf_file['system_file_path']).is_file():
    file_name = conf_file['system_file_path']
  else:
    file_name = Path(__file__).resolve().parent.parent / conf_file['default_file_path']

  with open(file_name) as file:

    config = yaml.load(file, Loader=yaml.FullLoader)

    proxy = config.get('proxy', {})
    #print(f'proxy = {proxy}')
    
    listen = proxy.get('listen', {})
    #print(f'listen = {listen}')

    services = proxy.get('services', {})
    #print(f'services = {services}')

    load_balancing = proxy.get('load_balancing', {})
    #print(f'load_balancing = {load_balancing}')

  return (listen, services, load_balancing)



#
# Main function
#
def main():

  (listen, services, load_balancing) = get_config(config_file)
  return (listen, services, load_balancing)



#
# Entry point
#

if __name__ == '__main__':
  (listen, services, load_balancing) = main()
  print(config_file['description'])
  print(f'listen = {listen}')
  print(f'services = {services}')
  print(f'load_balancing = {load_balancing}')
