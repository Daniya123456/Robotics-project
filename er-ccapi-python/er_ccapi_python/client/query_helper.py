from __future__ import annotations
import json
from datetime import datetime
from time import sleep
from typing import Any, Dict

from gql.dsl import (
    DSLSubscription,
    DSLMutation,
    DSLQuery,
    DSLSchema,
    DSLVariableDefinitions,
    dsl_gql,
)

from ..models.enums import AwakeStatus, MissionStatus
from ..models.robot_exceptions import RobotException, NoMissionRunningException

import pandas as pd


def to_dict(obj):
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__))


def format_reponse(response, return_format):
    try:
        if return_format == "dict":
            return response
        elif return_format == "df":
            df = pd.json_normalize(response)
            return df
        else:
            print(f"return_format {return_format} not supported. Return dict format")
            return response
    except Exception as e:
        print(f"Error while formatting response: {e}. Return the response without formatting")
        return response


def get_site_and_robot(client, robot_number: int) -> dict:
    """
    :param client: GraphqlClient
    :param schema: DSLSchema
    :param robot_number: int
    :return: dict
    """
    variable_definitions_graphql = DSLVariableDefinitions()

    robot_by_number_query = DSLQuery(
        client.schema.Query.robotByNumber.args(number=variable_definitions_graphql.robotNumber).select(
            client.schema.RobotType.id,
            client.schema.RobotType.site.select(client.schema.SiteType.id),
            client.schema.RobotType.site.select(
                client.schema.SiteType.location,
                client.schema.SiteType.pointsOfInterest.select(
                    client.schema.PointOfInterestType.id,
                    client.schema.PointOfInterestType.name,
                    client.schema.PointOfInterestType.customerTag,
                ),
            ),
        )
    )

    robot_by_number_query.variable_definitions = variable_definitions_graphql

    params = {"robotNumber": robot_number}

    response_dict = client.query(dsl_gql(robot_by_number_query), params)
    robot_id: str = response_dict["robotByNumber"]["id"]
    site_id: str = response_dict["robotByNumber"]["site"]["id"]
    site_pois: dict = response_dict["robotByNumber"]["site"]["pointsOfInterest"]

    return {
        "robot_id": robot_id,
        "site_id": site_id,
        "site_pois": site_pois,
    }


def get_point_of_interests(client, robot_number: str = None, site_id: str = None) -> dict:
    """
    Returns the point of interests of a robot or site

    Args:
        robot_number (str): Robot number. Defaults to None.
        site_id (str): Site id. Defaults to None.

    Returns:
        dict: Point of interests of the robot or site.
    """
    variable_definitions_graphql = DSLVariableDefinitions()
    if robot_number is not None:
        point_of_interest_query = DSLQuery(
            client.schema.Query.robotByNumber.args(number=variable_definitions_graphql.robotNumber).select(
                client.schema.RobotType.site.select(
                    client.schema.SiteType.pointsOfInterest.select(
                        client.schema.PointOfInterestType.id,
                        client.schema.PointOfInterestType.name,
                        client.schema.PointOfInterestType.customerTag,
                        client.schema.PointOfInterestType.inspectionParameters,
                    ),
                ),
            )
        )

        point_of_interest_query.variable_definitions = variable_definitions_graphql

        params = {"robotNumber": robot_number}
        response_dict = client.query(dsl_gql(point_of_interest_query), params)

        return response_dict["robotByNumber"]["site"]["pointsOfInterest"]
    elif site_id is not None:
        point_of_interest_query = DSLQuery(
            client.schema.Query.site.args(id=variable_definitions_graphql.id).select(
                client.schema.SiteType.pointsOfInterest.select(
                    client.schema.PointOfInterestType.id,
                    client.schema.PointOfInterestType.name,
                    client.schema.PointOfInterestType.customerTag,
                    client.schema.PointOfInterestType.inspectionParameters,
                ),
            )
        )

        point_of_interest_query.variable_definitions = variable_definitions_graphql

        params = {"id": site_id}
        response_dict = client.query(dsl_gql(point_of_interest_query), params)

        return response_dict["site"]["pointsOfInterest"]


def get_mission_definitions(client, robot_id: str) -> list[dict]:
    """
    :param robot_id: str
    :return: list[dict]
    """
    variable_definitions_graphql = DSLVariableDefinitions()

    mission_definitions_query: DSLQuery = DSLQuery(
        client.schema.Query.missionDefinitions.args(
            input=variable_definitions_graphql.QueryMissionDefinitionInput
        ).select(
            client.schema.MissionDefinitionsType.name,
            client.schema.MissionDefinitionsType.id,
        )
    )

    mission_definitions_query.variable_definitions = variable_definitions_graphql

    params: dict[str, Any] = {"QueryMissionDefinitionInput": {"robotID": robot_id}}

    response_dict = client.query(dsl_gql(mission_definitions_query), params)

    return response_dict["missionDefinitions"]


def get_mission_definition(client, mission_id: str) -> dict:
    variable_definitions_graphql = DSLVariableDefinitions()

    mission_definition_query: DSLQuery = DSLQuery(
        client.schema.Query.missionDefinition.args(id=variable_definitions_graphql.id).select(
            client.schema.MissionDefinitionType.name,
            client.schema.MissionDefinitionType.id,
            client.schema.MissionDefinitionType.tasks.select(
                client.schema.AbstractMissionTaskDefinitionType.id,
                client.schema.AbstractMissionTaskDefinitionType.name,
                client.schema.AbstractMissionTaskDefinitionType.type,
            ),
        )
    )

    mission_definition_query.variable_definitions = variable_definitions_graphql

    params: dict[str, Any] = {"id": mission_id}

    response_dict = client.query(dsl_gql(mission_definition_query), params)

    return response_dict["missionDefinition"]


def get_mission_status(client, robot_id: str) -> MissionStatus:
    variable_definitions_graphql: DSLVariableDefinitions = DSLVariableDefinitions()

    current_mission_execution_query: DSLQuery = DSLQuery(
        client.schema.Query.currentMissionExecution.args(robotID=variable_definitions_graphql.robotID).select(
            client.schema.MissionExecutionType.status
        )
    )
    current_mission_execution_query.variable_definitions = variable_definitions_graphql

    params: dict = {"robotID": robot_id}

    # BUG this should not be needed if the api exposes return the correct MissionExecutionStatus https://developer.energy-robotics.com/api-docs/#definition-MissionExecutionStatusEnum
    # At the moment if the mission is completed for the missionExecution is returning null
    # if not is_mission_running(robot_id):
    #     raise NoMissionRunningException(f"No mission is running for robot " f"with id {robot_id}")

    response_dict: dict[str, Any] = client.query(dsl_gql(current_mission_execution_query), params)
    status = MissionStatus(response_dict["currentMissionExecution"]["status"]).name
    return status


def get_robot_status(client, robot_id: str) -> dict:
    variable_definitions_graphql: DSLVariableDefinitions = DSLVariableDefinitions()

    current_robot_status_query: DSLQuery = DSLQuery(
        client.schema.Query.currentRobotStatus.args(robotID=variable_definitions_graphql.robotID).select(
            client.schema.RobotStatusType.isConnected,
            client.schema.RobotStatusType.awakeStatus,
            client.schema.RobotStatusType.batteryStatus.select(
                client.schema.BatteryStatusType.percentage,
                client.schema.BatteryStatusType.chargingState,
                client.schema.BatteryStatusType.chargingCurrent,
            ),
            client.schema.RobotStatusType.connectionStatus.select(
                client.schema.ConnectionStatusType.type,
                client.schema.ConnectionStatusType.networkName,
                client.schema.ConnectionStatusType.signalStrength,
            ),
            client.schema.RobotStatusType.isEmergencySwitchPressed,
            client.schema.RobotStatusType.isDocking,
        )
    )

    current_robot_status_query.variable_definitions = variable_definitions_graphql

    params: dict = {"robotID": robot_id}

    response_dict: dict[str, Any] = client.query(dsl_gql(current_robot_status_query), params)
    print(response_dict)

    return response_dict["currentRobotStatus"]


def wake_up_robot(client, robot_id: str) -> None:
    params: dict = {"robotID": robot_id}

    variable_definitions_graphql: DSLVariableDefinitions = DSLVariableDefinitions()

    wake_up_robot_mutation: DSLMutation = DSLMutation(
        client.schema.Mutation.executeAwakeCommand.args(
            targetState=AwakeStatus.Awake,
            robotID=variable_definitions_graphql.robotID,
        ).select(
            client.schema.RobotCommandExecutionType.id,
        )
    )

    wake_up_robot_mutation.variable_definitions = variable_definitions_graphql

    try:
        result: Dict[str, Any] = client.query(dsl_gql(wake_up_robot_mutation), params)
    except Exception as e:
        raise RobotException(e)
    return result


def get_current_principal_driver(client, robot_id: str) -> dict:
    variable_definitions_graphql = DSLVariableDefinitions()

    current_principal_driver_query: DSLQuery = DSLQuery(
        client.schema.Query.currentPrincipalDriver.args(robotId=variable_definitions_graphql.robotId).select(
            client.schema.PrincipalDriverType.name,
            client.schema.PrincipalDriverType.email,
        )
    )

    current_principal_driver_query.variable_definitions = variable_definitions_graphql

    params = {"robotId": robot_id}

    response_dict = client.query(dsl_gql(current_principal_driver_query), params)
    return response_dict["currentPrincipalDriver"]


def is_principal_driver(client, robot_id: str) -> bool:
    params: dict = {"robotID": robot_id}

    variable_definitions_graphql: DSLVariableDefinitions = DSLVariableDefinitions()

    check_principal_driver_query: DSLQuery = DSLQuery(
        client.schema.Query.isPrincipalDriver.args(robotId=variable_definitions_graphql.robotId)
    )

    check_principal_driver_query.variable_definitions = variable_definitions_graphql

    params: dict = {"robotId": robot_id}
    response_dict: dict[str, Any] = client.query(dsl_gql(check_principal_driver_query), params)
    return response_dict["isPrincipalDriver"]


def get_principal_driver_by_time(client, robot_id, timestamp) -> str:
    variable_definitions_graphql = DSLVariableDefinitions()

    principal_by_time_query = DSLQuery(
        client.schema.Query.principalDriverAtTimestamp.args(
            robotId=variable_definitions_graphql.robotId,
            timestamp=variable_definitions_graphql.timestamp,
        ).select(
            client.schema.PrincipalDriverType.name,
            client.schema.PrincipalDriverType.email,
        )
    )

    principal_by_time_query.variable_definitions = variable_definitions_graphql

    params = {"robotId": robot_id, "timestamp": timestamp}

    response_dict = client.query(dsl_gql(principal_by_time_query), params)

    try:
        response_dict["principalDriverAtTimestamp"]["name"]
    except:
        return {"name": None, "email": None}
    else:
        name = response_dict["principalDriverAtTimestamp"]["name"]
        email = response_dict["principalDriverAtTimestamp"]["email"]
        return {"name": name, "email": email}


def become_principal_driver(client, robot_id) -> None:
    params: dict = {"robotId": robot_id}

    variable_definitions_graphql: DSLVariableDefinitions = DSLVariableDefinitions()

    become_principal_driver_mutation: DSLMutation = DSLMutation(
        client.schema.Mutation.becomePrincipalDriver.args(
            robotId=variable_definitions_graphql.robotId,
        ).select(client.schema.PrincipalDriverType.name)
    )

    become_principal_driver_mutation.variable_definitions = variable_definitions_graphql

    result: Dict[str, Any] = client.query(dsl_gql(become_principal_driver_mutation), params)

    driver: str = result["becomePrincipalDriver"]["name"]
    return driver


def is_robot_awake(client, robot_id: str) -> bool:
    params: dict = {"robotID": robot_id}

    variable_definitions_graphql: DSLVariableDefinitions = DSLVariableDefinitions()

    check_if_awake_query: DSLQuery = DSLQuery(
        client.schema.Query.currentRobotStatus.args(robotID=variable_definitions_graphql.robotID).select(
            client.schema.RobotStatusType.isConnected,
            client.schema.RobotStatusType.awakeStatus,
        )
    )

    check_if_awake_query.variable_definitions = variable_definitions_graphql

    try:
        result: Dict[str, Any] = client.query(dsl_gql(check_if_awake_query), params)
    except Exception as e:
        raise RobotException(e)

    if not result["currentRobotStatus"]["isConnected"]:
        raise RobotException("Robot is not connected")

    status: AwakeStatus = AwakeStatus(result["currentRobotStatus"]["awakeStatus"])
    success: bool = status in [AwakeStatus.Awake]
    return success


def start_mission_execution(client, mission_definition_id: str, robot_id: str) -> str:
    params: dict[str, Any] = {
        "robotID": robot_id,
        "missionDefinitionID": mission_definition_id,
    }

    variable_definitions_graphql: DSLVariableDefinitions = DSLVariableDefinitions()

    mutation_args: dict[str, Any] = {
        "input": {
            "robotID": variable_definitions_graphql.robotID,
            "missionDefinitionID": variable_definitions_graphql.missionDefinitionID,
        }
    }
    start_mission_execution_mutation: DSLMutation = DSLMutation(
        client.schema.Mutation.startMissionExecution.args(**mutation_args).select(client.schema.MissionExecutionType.id)
    )

    start_mission_execution_mutation.variable_definitions = variable_definitions_graphql

    try:
        response_dict: dict[str, Any] = client.query(dsl_gql(start_mission_execution_mutation), params)
    except Exception as e:
        raise RobotException from e

    mission_execution_id = response_dict["startMissionExecution"]["id"]
    return mission_execution_id


def pause_current_mission(client, robot_id: str) -> None:
    params: dict = {"robotID": robot_id}

    variable_definitions_graphql: DSLVariableDefinitions = DSLVariableDefinitions()

    pause_current_mission_mutation: DSLMutation = DSLMutation(
        client.schema.Mutation.pauseMissionExecution.args(robotID=variable_definitions_graphql.robotID).select(
            client.schema.MissionExecutionType.id,
            client.schema.MissionExecutionType.status,
            client.schema.MissionExecutionType.failures,
        )
    )

    pause_current_mission_mutation.variable_definitions = variable_definitions_graphql

    try:
        result: Dict[str, Any] = client.query(dsl_gql(pause_current_mission_mutation), params)
    except Exception as e:
        raise RobotException(e)

    status: MissionStatus = MissionStatus(result["status"])
    success: bool = status in [
        MissionStatus.Paused,
        MissionStatus.PauseRequested,
    ]
    if not success:
        raise RobotException(f"Invalid status after pausing mission: '{status}'")
    return success


def get_mission_events(client, robot_id: str, start: int, end: int) -> list[dict]:
    variable_definitions_graphql = DSLVariableDefinitions()

    mission_events_query: DSLQuery = DSLQuery(
        client.schema.Query.events.args(
            robotId=variable_definitions_graphql.robotId,
            period=variable_definitions_graphql.PeriodInput,
        ).select(
            client.schema.EventsType.page.select(
                client.schema.EventTypeConnection.edges.select(
                    client.schema.EventTypeEdge.node.select(
                        client.schema.EventType.timestamp,
                        client.schema.EventType.diagnostics.select(
                            client.schema.DiagnosticsType.timestamp,
                            client.schema.DiagnosticsType.type,
                            client.schema.DiagnosticsType.component,
                            client.schema.DiagnosticsType.value,
                        ),
                        client.schema.EventType.customerFlag.select(
                            client.schema.CustomerFlagType.timestamp,
                            client.schema.CustomerFlagType.reason,
                            client.schema.CustomerFlagType.user.select(
                                client.schema.UserType.email,
                                client.schema.UserType.name,
                            ),
                        ),
                    )
                )
            )
        )
    )

    mission_events_query.variable_definitions = variable_definitions_graphql

    params: dict[str, Any] = {
        "robotId": robot_id,
        "PeriodInput": {"start": start, "end": end},
    }
    print(mission_events_query)

    response_dict = client.query(dsl_gql(mission_events_query), params)

    return response_dict["events"]["page"]["edges"]


def get_mission_report(client, mission_report_id: str, payload_filter_types=None) -> list:
    variable_definitions_graphql = DSLVariableDefinitions()

    mission_report_query: DSLQuery = DSLQuery(
        client.schema.Query.missionReport.args(id=variable_definitions_graphql.id).select(
            client.schema.MissionReportType.id,
            client.schema.MissionReportType.startTimestamp,
            client.schema.MissionReportType.endTimestamp,
            client.schema.MissionReportType.distance,
            client.schema.MissionReportType.duration,
            client.schema.MissionReportType.robot.select(client.schema.RobotSnapshotType.name),
            client.schema.MissionReportType.dataPayloads.args(
                payloadFilter=variable_definitions_graphql.payloadFilter
            ).select(
                client.schema.AbstractDataPayloadType.poiName,
                client.schema.AbstractDataPayloadType.dataLabel,
                client.schema.AbstractDataPayloadType.id,
                client.schema.AbstractDataPayloadType.key,
                client.schema.AbstractDataPayloadType.dataType,
                client.schema.AbstractDataPayloadType.parentPayloadKey,
                client.schema.AbstractDataPayloadType.producer.select(
                    client.schema.DataPayloadProducerType.name,
                    client.schema.DataPayloadProducerType.group,
                ),
            ),
        )
    )

    mission_report_query.variable_definitions = variable_definitions_graphql
    include_payload_types = ["PHOTO", "VIDEO", "AUDIO"]
    if payload_filter_types is not None:
        include_payload_types = payload_filter_types
    params: dict[str, Any] = {
        "id": mission_report_id,
        "payloadFilter": {
            "includeSkillData": False,
            "includePayloadTypes": include_payload_types,
        },
    }

    response_dict = client.query(dsl_gql(mission_report_query), params)

    return response_dict["missionReport"]


def get_mission_reports(client, robot_number: int, entries: int, dynamic_pagination: bool = False) -> list:
    variable_definitions_graphql = DSLVariableDefinitions()

    mission_reports_query: DSLQuery = DSLQuery(
        client.schema.Query.missionReports.args(
            input=variable_definitions_graphql.QueryMissionReportsInput,
            filter=variable_definitions_graphql.ConnectionInput,
        ).select(
            client.schema.MissionReportsType.page.select(
                client.schema.MissionReportOverviewTypeConnection.pageInfo.select(
                    client.schema.MissionReportOverviewTypePageInfo.endCursor,
                    client.schema.MissionReportOverviewTypePageInfo.hasNextPage,
                ),
                client.schema.MissionReportOverviewTypeConnection.edges.select(
                    client.schema.MissionReportOverviewTypeEdge.node.select(client.schema.MissionReportOverviewType.id)
                ),
            )
        )
    )

    mission_reports_query.variable_definitions = variable_definitions_graphql
    if entries is None:
        connection_input = {}
    else:
        connection_input = {"first": entries, "after": "none"}

    params: dict[str, Any] = {
        "QueryMissionReportsInput": {"robotNumber": robot_number},
        "ConnectionInput": connection_input,
    }

    response_dict = client.query(dsl_gql(mission_reports_query), params)

    if dynamic_pagination:
        response = []
        while response_dict["missionReports"]["page"]["pageInfo"]["hasNextPage"]:
            response.extend(response_dict["missionReports"]["page"]["edges"])

            cursor = response_dict["missionReports"]["page"]["pageInfo"]["endCursor"]
            params["ConnectionInput"]["after"] = cursor

            response_dict = client.query(dsl_gql(mission_reports_query), params)
        else:
            response.extend(response_dict["missionReports"]["page"]["edges"])
    else:
        response = response_dict["missionReports"]["page"]["edges"]

    return response


def is_mission_running(client, robot_id: str) -> bool:
    variable_definitions_graphql: DSLVariableDefinitions = DSLVariableDefinitions()

    is_mission_running_query: DSLQuery = DSLQuery(
        client.schema.Query.isMissionRunning.args(robotID=variable_definitions_graphql.robotID)
    )

    is_mission_running_query.variable_definitions = variable_definitions_graphql

    params: dict = {"robotID": robot_id}
    response_dict: dict[str, Any] = client.query(dsl_gql(is_mission_running_query), params)

    return response_dict.get("isMissionRunning", None)


def get_mission_reports_by_period(
    client,
    site_id: str,
    robot_number: int = None,
    entries: int = None,
    start: int = None,
    end: int = None,
    dynamic_pagination: bool = True,
) -> list:
    variable_definitions_graphql = DSLVariableDefinitions()

    mission_reports_query: DSLQuery = DSLQuery(
        client.schema.Query.missionReportsByPeriod.args(
            siteId=variable_definitions_graphql.siteId,
            robotFilter=variable_definitions_graphql.RobotFilterInput,
            period=variable_definitions_graphql.PeriodInput,
            connection=variable_definitions_graphql.ConnectionInput,
        ).select(
            client.schema.MissionReportsType.page.select(
                client.schema.MissionReportOverviewTypeConnection.pageInfo.select(
                    client.schema.MissionReportOverviewTypePageInfo.endCursor,
                    client.schema.MissionReportOverviewTypePageInfo.hasNextPage,
                ),
                client.schema.MissionReportOverviewTypeConnection.edges.select(
                    client.schema.MissionReportOverviewTypeEdge.node.select(
                        client.schema.MissionReportOverviewType.id,
                        client.schema.MissionReportOverviewType.startTimestamp,
                        client.schema.MissionReportOverviewType.endTimestamp,
                        client.schema.MissionReportType.distance,
                        client.schema.MissionReportType.duration,
                    )
                ),
            )
        )
    )

    mission_reports_query.variable_definitions = variable_definitions_graphql

    params: dict[str, Any] = {
        "siteId": site_id,
        "RobotFilterInput": {"robotNumber": robot_number},
        "PeriodInput": {"start": start, "end": end},
        "ConnectionInput": {"first": entries, "after": "none"},
    }

    response_dict = client.query(dsl_gql(mission_reports_query), params)

    if dynamic_pagination:
        response = []
        while response_dict["missionReportsByPeriod"]["page"]["pageInfo"]["hasNextPage"]:
            response.extend(response_dict["missionReportsByPeriod"]["page"]["edges"])

            cursor = response_dict["missionReportsByPeriod"]["page"]["pageInfo"]["endCursor"]
            params["ConnectionInput"]["after"] = cursor

            response_dict = client.query(dsl_gql(mission_reports_query), params)
        else:
            response.extend(response_dict["missionReportsByPeriod"]["page"]["edges"])
    else:
        response = response_dict["missionReportsByPeriod"]["page"]["edges"]

    return response


def get_distance_and_duration_by_period(client, site_id: str, robot_number: int, start: int, end: int) -> dict:
    """
    :param client: GraphqlClient
    :param site_id: str
    :param robot_number: int
    :param start: int
    :param end: int
    :return: dict
    """

    mission_reports = get_mission_reports_by_period(client, site_id, robot_number, start=start, end=end)
    meters = sum(mission_report["node"]["distance"] for mission_report in mission_reports)
    duration = sum(mission_report["node"]["duration"] for mission_report in mission_reports)
    return {"meters": meters, "duration": duration}
