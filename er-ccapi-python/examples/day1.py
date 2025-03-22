import yaml
import random
import time
import datetime

# import gql to make queries
from er_ccapi_python.client import GraphqlClient, GraphqlClientWss
from er_ccapi_python.classes import Site

from er_ccapi_python.client.query_helper import get_point_of_interests

import logging
from gql.transport.requests import log as requests_logger

requests_logger.setLevel(logging.WARNING)


def read_out_all_point_of_interests(site: Site):
    pois = site.get_point_of_interest(return_format="dict")
    print(f"Number of point of interests: {len(pois)}")
    print(", ".join([f"{row['name']}" for row in pois]))


def main():
    """
    simple example on how to initialize the client
    """

    # load the config for testing from conifg.yml
    config = yaml.safe_load(open("config.yml"))

    er_client = GraphqlClient(config)
    site = Site(er_client, "652fa1f6530ca5d633caf463")
    read_out_all_point_of_interests(site)


if __name__ == "__main__":
    main()
import yaml
import random
import time
import datetime

#import gql to make queries

from er_ccapi_python.client import GraphqlClient, GraphqlClientWss
from er_ccapi_python.classes import Site

from er_ccapi_python.client.query_helper import get_point_of_interests

import logging
from gql.transport.requests import log as requests_logger

requests_logger.setLevel(logging.WARNING)
