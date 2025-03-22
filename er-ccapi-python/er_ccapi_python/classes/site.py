from __future__ import annotations
from typing import Any, Dict
from gql.dsl import DSLSchema

from ..client import query_helper


class Site:
    def __init__(self, client, id: str):
        """
        Initializes a Site object.

        Args:
            client (GraphqlClient): Client which will be used to communicate with the Energy Robotics GraphQL API.
            id (str): Site id.
        """
        self.client = client
        self.schema: DSLSchema = self.client.schema
        self.site_id = id

    def get_point_of_interest(self, return_format: str = "dict") -> dict:
        """
        Returns the point of interests of a robot

        Args:
            return_format (str): Return format. Can be either 'dict' or 'df' (pandas DataFrame). Defaults to 'dict'.

        Returns:
            dict or pd.DataFrame: Point of interests of the robot.
        """
        response = query_helper.get_point_of_interests(self.client, site_id=self.site_id)
        return query_helper.format_reponse(response, return_format)

