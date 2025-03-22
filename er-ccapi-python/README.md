# ER CCAPI Python Package
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)

## Introduction
The ER CCAPI Python Package is a Python library that provides a convenient way to interact with the ER CCAPI (Energy Robotics Cloud Core API) services. It allows developers to easily integrate their Python applications with the ER CCAPI platform.

## Installation
To install the ER CCAPI Python Package, you can use pip3 or pip:

`pip3 install git+ssh://git@gitlab.cicd.energy-robotics.com:8086/er_dev/er-ccapi-python.git`


## Usage

If you want to use the er-ccapi-python package, you need to provide the following information, which is stored in a yaml file in the directory in which you run your script:

```yaml
auth_service:
  endpoint: "https://login.energy-robotics.com/api/loginApi"
  user_email: "<add your email here>"
  user_api_key_file: "<add the name of your key file here>"
  refresh_interval: 300

api:
  production_deployment: False
  dev_url: "https://ccapi-development.devtest.energy-robotics.com/graphql"
  prod_url: "https://api.graphql.energy-robotics.com/graphql"

```
Save this file and use the filename to initialize a client. For example if your config file is named `config.yml`.
```python
import yaml
from er_ccapi_python.client import GraphqlClient
# load the config.yml
config = yaml.safe_load(open("test_config.yml"))

er_client = GraphqlClient(config)

```

For security reasons, your API key should be placed in a separate file containing only your key in the same folder. Add the filename to your `config.yml` as shown above. The name of the file could be `key-file`.


### Classes
You can use most of the queries provided in the `from er_ccapi_python.client.query_helper` directly by providing the necessary information such as a client and sometimes a robot number, id or site id. There are also classes to help you use these queries, for example the Robot and Site classes.

#### Robot 
Simple robot initialization:

```python 
import yaml
from er_ccapi_python.client import GraphqlClient
from er_ccapi_python.classes import Robot


config = yaml.safe_load(open("test_config.yml"))
er_client = GraphqlClient(config)
robot = Robot(er_client, 600, safemode=True)

```

Only set safemode to False if you want to actively control the robot via mutations.



# Examples
see example folder

