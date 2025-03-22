from gql import Client
from gql.dsl import DSLSchema
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import WebsocketsTransport
from gql.transport.exceptions import (
    TransportClosed,
    TransportProtocolError,
    TransportQueryError,
    TransportServerError,
)
from graphql import (
    DocumentNode,
    GraphQLError,
    GraphQLSchema,
    build_ast_schema,
    parse,
)
from typing import Any, Dict
from logging import Logger, getLogger
import pathlib
from .auth_service import AuthService

DIR = pathlib.Path(__file__).parent.resolve()


class GraphqlClient:
    def __init__(self, config) -> None:
        # Parameter used for retrying query with new authentication
        # in case of expired token
        self._reauthenticated: bool = False
        self._logger: Logger = getLogger("graphql_client")
        self._config = config
        self._auth_service = None
        self._init_auth_service()
        self._initialize_client()

    def _init_auth_service(self):
        try:
            self._auth_service = AuthService(self._config)
        except Exception as e:
            raise e
        self._logger.debug(AuthService)

    def _initialize_client(self):
        header = self._auth_service.get_auth_header()

        with open(f"{DIR}/schema.graphql", encoding="utf-8") as source:
            document = parse(source.read())

        schema: GraphQLSchema = build_ast_schema(document)

        api_settings = self._config.get("api")
        self._logger.debug(api_settings)

        if api_settings["production_deployment"]:
            api_url = api_settings["prod_url"]
        else:
            api_url = api_settings["dev_url"]

        transport: AIOHTTPTransport = AIOHTTPTransport(url=api_url, headers=header)
        self.client: Client = Client(transport=transport, schema=schema, execute_timeout=900)
        self.schema: DSLSchema = DSLSchema(self.client.schema)
        

    async def query_async(self, query: DocumentNode, query_parameters: dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a GraphQL query to the 'API' endpoint.
        :return: A dictionary of the object returned from the API if success.
        :raises GrahpQLError: Something went related to the query
        :raises TransportError: Something went wrong during transfer or on the API server side
        :raises Exception: Unknown error
        """
        # TODO use of automatic token refresh from the auth_service
        try:
            response: Dict[str, Any] = await self.client.execute_async(query, query_parameters)
            return response
        except GraphQLError as e:
            self._logger.error(f"Something went wrong while sending the GraphQL query: {e.message}")
            self._logger.error(e)
            raise
        except TransportProtocolError as e:
            if self._reauthenticated:
                self._logger.error("Transport protocol error - Error in configuration of GraphQL client")
                raise
            else:
                # The token might have expired, try again with a new token
                self._initialize_client()
                self._reauthenticated = True
                await self.query(query=query, query_parameters=query_parameters)
        except TransportQueryError as e:
            self._logger.error(f"The Energy Robotics server returned an error: {e.errors}")
            self._logger.error(f" query: {query}")
            raise
        except TransportClosed as e:
            self._logger.error("The connection to the GraphQL endpoint is closed")
            raise
        except TransportServerError as e:
            self._logger.error(f"Error in Energy Robotics server: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Unknown error in GraphQL client: {e}")
            raise
        finally:
            self._reauthenticated = False
        return {}

    def query(self, query: DocumentNode, query_parameters: dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a GraphQL query to the 'ROBOT_API_URL' endpoint.
        :return: A dictionary of the object returned from the API if success.
        :raises GrahpQLError: Something went related to the query
        :raises TransportError: Something went wrong during transfer or on the API server side
        :raises Exception: Unknown error
        """
        try:
            response: Dict[str, Any] = self.client.execute(query, query_parameters)
            return response
        except GraphQLError as e:
            self._logger.error(f"Something went wrong while sending the GraphQL query: {e.message}")
            print(e)
            raise
        except TransportProtocolError as e:
            if self._reauthenticated:
                self._logger.error("Transport protocol error - Error in configuration of GraphQL client")
                raise
            else:
                # The token might have expired, try again with a new token
                self._initialize_client()
                self._reauthenticated = True
                self.query(query=query, query_parameters=query_parameters)
        except TransportQueryError as e:
            self._logger.error(f"The Energy Robotics server returned an error: {e.errors}")
            self._logger.error(f" query: {query}")
            raise
        except TransportClosed as e:
            self._logger.error("The connection to the GraphQL endpoint is closed")
            raise
        except TransportServerError as e:
            self._logger.error(f"Error in Energy Robotics server: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Unknown error in GraphQL client: {e}")
            raise
        finally:
            self._reauthenticated = False
        return {}


# create a GraphQL client instance which uses wss protocol
class GraphqlClientWss:
    def __init__(self, config) -> None:
        self._logger: Logger = getLogger("graphql_client_wss")
        self._config = config
        self._auth_service = None
        self._init_auth_service()
        self._initialize_client()

    def _init_auth_service(self):
        # change api_url to wss
        api_settings = self._config.get("api")
        api_settings["dev_url"] = api_settings["dev_url"].replace("http", "ws")
        self._config["api"] = api_settings

        try:
            self._auth_service = AuthService(self._config)
        except Exception as e:
            raise e
        self._logger.debug(AuthService)

    def _initialize_client(self):
        header = self._auth_service.get_auth_header()
        print(header)

        with open(f"{DIR}/schema.graphql", encoding="utf-8") as source:
            document = parse(source.read())

        schema: GraphQLSchema = build_ast_schema(document)

        api_settings = self._config.get("api")
        self._logger.debug(api_settings)

        if api_settings["production_deployment"]:
            api_url = api_settings["prod_url"]
        else:
            api_url = api_settings["dev_url"]
        # get api_url and replace http with ws
        api_url = api_url.replace("http", "ws")
        print(api_url)
        transport = WebsocketsTransport(
            url=api_url,
            init_payload=header,
            headers=header,
            # TODO Check if this helps with breaking connections
            # https://gql.readthedocs.io/en/latest/transports/websockets.html#graphql-ws-protocol
            # ping_interval=60,
            # pong_timeout=10,
        )
        self.client: Client = Client(transport=transport, fetch_schema_from_transport=True)
        #  schema=schema)
        # self.schema: DSLSchema = DSLSchema(self.client.schema)

    def query(self, query: DocumentNode, query_parameters: dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a GraphQL query to the 'API-URL' endpoint.
        :return: A dictionary of the object returned from the API if success.
        :raises GrahpQLError: Something went related to the query
        :raises TransportError: Something went wrong during transfer or on the API server side
        :raises Exception: Unknown error
        """
        try:
            response: Dict[str, Any] = self.client.execute(query, query_parameters)
            return response
        except GraphQLError as e:
            self._logger.error(f"Something went wrong while sending the GraphQL query: {e.message}")
            print(e)
            raise
        except TransportProtocolError as e:
            if self._reauthenticated:
                self._logger.error("Transport protocol error - Error in configuration of GraphQL client")
                raise
            else:
                # The token might have expired, try again with a new token
                # TODO check if there is a better way then restarting the client (maybe only get the new token from the auth_service)
                self._initialize_client()
                self._reauthenticated = True
                self.query(query=query, query_parameters=query_parameters)
        except TransportQueryError as e:
            self._logger.error(f"The Energy Robotics server returned an error: {e.errors}")
            self._logger.error(f" query: {query}")
            raise
        except TransportClosed as e:
            self._logger.error("The connection to the GraphQL endpoint is closed")
            raise
        except TransportServerError as e:
            self._logger.error(f"Error in Energy Robotics server: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Unknown error in GraphQL client: {e}")
            raise
        finally:
            self._reauthenticated = False
        return {}
