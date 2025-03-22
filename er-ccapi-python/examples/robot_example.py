import yaml
import random
import time
import datetime

# import gql to make queries
from er_ccapi_python.client import GraphqlClient, GraphqlClientWss
from er_ccapi_python.classes import Robot
from er_ccapi_python.models.robot_exceptions import RobotException

from er_ccapi_python.client.query_helper import get_point_of_interests

import logging
from gql.transport.requests import log as requests_logger

requests_logger.setLevel(logging.WARNING)


def get_basic_robot_information(robot: Robot):
    """
    prints out the basic robot information
    :param robot: Robot
    :return: None
    """
    try:
        print(f"Robot #{robot.robot_number} has the following information:")
        print(f"Robot ID: {robot.robot_id}")
        print(f"Site ID: {robot.site_id}")
        # check if I am the principal driver
        print(f"Am I the principal driver? {robot.is_principal_driver()}")
        # current principal driver
        print(f"Current principal driver: {robot.get_current_principal_driver()}")
        # is the robot awake?
        print(f"Is the robot awake? {robot.is_robot_awake()}")
    except RobotException as e:
        print(f"Error while getting robot information: {e}")


def read_out_all_mission_report_ids(robot: Robot) -> dict:
    """
    prints out all mission report ids
    :param robot: Robot
    :return: None
    """
    mission_report_ids = robot.get_mission_reports()
    print(f"Number of mission reports: {len(mission_report_ids)}")
    print("Mission reports:")
    print(", ".join([f"{row['node']['id']}" for row in mission_report_ids]))
    return mission_report_ids


def read_out_all_point_of_interests(robot: Robot):
    pois = robot.get_point_of_interest()
    print(f"Number of point of interests: {len(pois)}")
    print(", ".join([f"{row['name']}" for row in pois]))


def get_missions(robot: Robot):
    """
    prints out all mission names
    :param robot: Robot
    :return: None
    """
    missions = robot.get_missions()
    print("Missions:")
    print("Number of missions: ", len(missions))
    # print mission name (task numbers) in one line
    print(", ".join([f"{row['mission_name']} ({len(row['tasks'])} tasks)" for index, row in missions.iterrows()]))


def loop_forever_robot_status(robot: Robot):
    # and the robot status
    startime = time.time()
    while True:
        try:
            print(f"Robot awake status: {robot.get_robot_status()}")
            print(f"Time from start: {time.time() - startime}")
            time.sleep(60)
        except Exception as e:
            print(f"Error while getting robot status: {e}")
            time.sleep(10)
            pass


def get_mission_reports_for_last_two_days(robot: Robot):
    """
    prints out all mission report ids
    :param robot: Robot
    :return: None
    """
    print("Mission reports for the last two days:")
    start = datetime.datetime.now() - datetime.timedelta(days=2)
    end = datetime.datetime.now()
    print(f"Start: {start}")
    print(f"End: {end}")
    mission_report_ids = robot.get_mission_reports_by_period(start_time=start, end_time=end)
    print(f"Number of mission reports: {len(mission_report_ids)}")
    print("Mission reports:")
    print(", ".join([f"{row['node']['id']}" for row in mission_report_ids]))


def main():
    """
    simple example on how to initialize the client for the robot class
    """

    # load the config for testing from conifg.yml
    config = yaml.safe_load(open("config.yml"))

    er_client = GraphqlClient(config)

    # print(get_point_of_interests(er_client, 600))

    robot = Robot(er_client, 600, safemode=True)

    get_basic_robot_information(robot)
    read_out_all_point_of_interests(robot)
    get_missions(robot)

    mission_report_ids = read_out_all_mission_report_ids(robot)
    # get a mission report for a random mission out of the missions
    random_id_index = random.randint(0, len(mission_report_ids))
    mission_report = robot.get_mission_report(mission_report_ids[random_id_index]["node"]["id"])
    print(f"Mission report for mission {mission_report_ids[random_id_index]['node']['id']}: {mission_report}")
    get_mission_reports_for_last_two_days(robot)

    # loop_forever_robot_status(robot)



if __name__ == "__main__":
    main()
