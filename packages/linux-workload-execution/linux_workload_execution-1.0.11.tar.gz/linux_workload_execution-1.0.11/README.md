# linux_workload_execution

[![PyPI version](https://pypi.org/project/linux_workload_execution/)]

## Overview

linux_workload_execution is a Python package designed to:
Takes details like, lpar, ipaddress, script directory and script command as the input, and perform below activities

1. To call the zhmclient to activate the lpar, Sleep for 10 minutes
2. ssh to the ipaddress (Linux guest ip address)
3. download the script file to, local machine, from given source path
4. upload the dowloaded script file to the dir(/ffdc/u/eATS_automation) on the ssh session
5. invoke the script command (ex: sh make_loop.sh) on the ssh session
6. collect the output printed on the ssh session and print it


## Installation

You can install the package using pip:

```bash
pip install linux-workload-execution
```
## config JSON format

```bash
config.json

{
    "hmc_host_name": "ip address of host",
    "hmc_userid": "hmc user id",
    "hmc_user_pwd": "hmc user password",    
    "cpc": "cpc details",
    "lpar": "lpar details",
    "linux_system_ip": "ip address of host system",
    "linux_user_name": "user name",
    "linux_pwd": "password",
    "script_details": {
        "token": "",
        "name": "example.sh",
        "url": "path to script file",
        "exec_path": "path to script execution",
        "local_path": "./"
    }
}
```
## Usage example

``` bash
main.py
*******
import os
import sys
from linux_workload_execution.activation import Activation

if __name__ == "__main__":
    
    if (len(sys.argv) == 2 and os.path.exists(sys.argv[1])):
        activation_obj = Activation(sys.argv[1])
        if activation_obj.entry_point():
            print("***********Successfully completed***********")
        else:
            print("***********not successfully completed***********")
    else:
        print("***********JSON file not provided***********")
        print("***********Please provide JSON file***********")
```
## Running the Python code

``` bash

python main.py config.json

```

## Python package creation

[REFERENCE](https://packaging.python.org/en/latest/tutorials/packaging-projects//)
