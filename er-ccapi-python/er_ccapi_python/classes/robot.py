from __future__ import annotations
from typing import Any, Dict
from ..models.enums import MissionStatus
import logging

import pandas as pd
from gql.dsl import DSLSchema

from ..client import query_helper
from datetime import datetime


class Robot:
    def __init__(self, client, number: int, safemode: bool = True):
        """
        Initializes a Robot object.

        Args:
            client (GraphqlClient): Client which will be used to communicate with the Energy Robotics GraphQL API.
            number (int): Robot number.
            safemode (bool): If True, you will not be able to execute commands (mutations) to control the robot.
        """
        logging.basicConfig(level=logging.WARNING)
        self.client = client
        self.schema: DSLSchema = self.client.schema
        self.safemode = safemode

        self.robot_number = number
        try:
            robot_and_site = query_helper.get_site_and_robot(self.client, self.robot_number)

            self.robot_id = robot_and_site["robot_id"]
            self.site_id = robot_and_site["site_id"]
            if not self.site_id:
                print(f"Robot #{self.robot_number} has no siteId")
        except Exception as e:
            print(
                f"Error while initializing robot #{self.robot_number}: {e}. Please check if you have access to this robot."
            )

    def get_point_of_interest(self, return_format: str = "dict") -> dict:
        """
        Returns the point of interests of a robot
        
        Args:
            return_format (str): Return format. Can be either 'dict' or 'df' (pandas DataFrame). Defaults to 'dict'.

        Returns:
            dict or pd.DataFrame: Point of interests of the robot.
        """
        response = query_helper.get_point_of_interests(self.client, robot_number=self.robot_number)
        return query_helper.format_reponse(response, return_format)

    # missions
    def get_missions(self) -> pd.DataFrame:
        """
        Returns the missions of a robot

        Returns:
            pd.DataFrame: Missions of the robot.
        """
        response = query_helper.get_mission_definitions(self.client, self.robot_id)
        df = pd.json_normalize(response)
        if df.empty:
            return df
        df.rename(columns={"name": "mission_name", "id": "mission_id"}, inplace=True)
        tasks = []
        tasks = [self.get_mission_tasks(i) for i in df["mission_id"]]
        df["tasks"] = tasks
        return df

    def get_mission_tasks(self, mission_id: str, return_format: str = "dict") -> dict:
        """
        Returns the tasks of a mission

        Args:
            mission_id (str): Mission id.
            return_format (str): Return format. Can be either 'dict' or 'df' (pandas DataFrame). Defaults to 'dict'.

        Returns:
            dict or pd.DataFrame: Tasks of the mission.
        
        """
        response = query_helper.get_mission_definition(self.client, mission_id)
        return query_helper.format_reponse(response, return_format)

    def is_mission_running(self) -> bool:
        """
        Returns True if a mission is running on the robot

        Returns:
            bool: True if a mission is running on the robot.
        """
        reponse = query_helper.is_mission_running(self.client, self.robot_id)
        return reponse.get("isMissionRunning", None)

    def get_mission_status(self) -> MissionStatus:
        """
        Returns the status of the current mission
        :return: MissionStatus
        """
        # only do this if mission is running
        if not self.is_mission_running():
            return MissionStatus.NOT_RUNNING
        response = query_helper.get_mission_status(self.client, self.robot_id)
        return response["mission_status"]

    # Robot status
    def get_robot_status(self) -> dict:
        """
        Returns the status of the robot
       
        Returns:
            dict: Status of the robot.
        """
        response = query_helper.get_robot_status(self.client, self.robot_id)
        return response

    def is_robot_awake(self) -> bool:
        """
        Returns True if the robot is awake

        Returns:
            bool: True if the robot is awake.
        """
        return query_helper.is_robot_awake(self.client, self.robot_id)

    def get_current_principal_driver(self) -> dict:
        """
        Returns the principal driver of the robot

        Returns:
            dict: Principal driver of the robot.
        """
        response = query_helper.get_current_principal_driver(self.client, self.robot_id)
        return response

    def is_principal_driver(self) -> bool:
        """
        Returns True if the current user is the principal driver of the robot

        Returns:
            bool: True if the current user is the principal driver of the robot.
        """
        return query_helper.is_principal_driver(self.client, self.robot_id)

    # Missions
    def get_mission_report(self, mission_report_id: str) -> dict:
        """
        Returns the report of a mission

        Args:
            mission_report_id (str): Mission report id.

        Returns:
            dict: Report of the mission.
        """
        response = query_helper.get_mission_report(self.client, mission_report_id)
        return response

    def get_mission_reports(self, entries: int = None) -> dict:
        """
        Returns the ids of all mission reports of a robot

        Args:
            entries (int): Number of entries. Defaults to None.

        Returns:
            dict: Ids of all mission reports of a robot.
        """
        response = query_helper.get_mission_reports(self.client, self.robot_number, entries)
        return response

    def get_mission_reports_by_period(self, start_time: datetime, end_time: datetime, entries: int = None) -> dict:
        """
        Returns the mission reports (MissionReportOverviewType) of a robot for a specific time period

        Args:
            start_time (datetime): Start time.
            end_time (datetime): End time.
            entries (int): Number of entries. Defaults to None.
            
        Returns:
            dict: Mission reports of a robot for a specific time period.
        """
        # convert the datetime objects to milliseconds
        start_time = int(start_time.timestamp() * 1000)
        end_time = int(end_time.timestamp() * 1000)

        response = query_helper.get_mission_reports_by_period(
            self.client, self.site_id, self.robot_number, entries=entries, start=start_time, end=end_time
        )
        return response

    def get_distance_and_duration_by_period(self, start_time: datetime, end_time: datetime) -> dict:
        """
        Returns the distance and duration of a robot for a specific time period

        Args:
            start_time (datetime): Start time.
            end_time (datetime): End time.

        Returns:
            dict: Distance and duration of a robot for a specific time period.
        """
        # convert the datetime objects to milliseconds
        start_time = int(start_time.timestamp() * 1000)
        end_time = int(end_time.timestamp() * 1000)

        response = query_helper.get_distance_and_duration_by_period(
            self.client, self.site_id, self.robot_number, start=start_time, end=end_time
        )
        return response

    # manipulations
    def wake_up_robot(self) -> None:
        """
        Wakes up the robot.
        This only works if the robot is initialized with `safemode=False`.

        Returns:
            None
        """
        if self.safemode:
            raise Exception("Robot control is in safe mode")
        if not self.is_robot_awake():
            query_helper.wake_up_robot(self.client, self.robot_id, self.site_id)
        else:
            print("Robot is already awake")
        # TODO retrun something

    def become_principal_driver(self) -> str:
        """
        Makes the current user the principal driver of the robot.
        This only works if the robot is initialized with `safemode=False`.

        Returns:
            str: Principal driver of the robot. 
        """
        if self.safemode:
            raise Exception("Robot control is in safe mode")

        return query_helper.become_principal_driver(self.client, self.robot_id)

    def start_mission_execution(self, mission_definition_id: str) -> str:
        """
        Starts the execution of a mission.
        This only works if the robot is initialized with `safemode=False`.

        Args:
            mission_definition_id (str): Mission definition id.

        Returns:
            str: Mission id.
        """
        if self.safemode:
            raise Exception("Robot control is in safe mode")
        return query_helper.start_mission_execution(self.client, mission_definition_id, self.robot_id)

    def pause_current_mission(self) -> None:
        """
        Pauses the current mission.
        This only works if the robot is initialized with `safemode=False`.

        Returns:
            None
        """
        if self.safemode:
            raise Exception("Robot control is in safe mode")
        success = query_helper.pause_current_mission(self.client, self.robot_id)
        if success:
            print("Mission paused")
        else:
            print("Mission could not be paused")

    # BUG does not work at the moment
    def get_mission_events(self, start_time: float, end_time: float) -> dict:
        """
        Returns the mission events of a robot

        Args:
            start_time (float): Start time as unix timestamp.
            end_time (float): End time as unix timestamp.

        Returns:
            dict: Mission events of a robot.
        """
        events = query_helper.get_mission_events(self.client, self.robot_id, start_time, end_time)
        print(type(events))
        print(events)
        return events
