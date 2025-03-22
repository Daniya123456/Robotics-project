import logging
import base64
from time import time
import copy

from apscheduler.schedulers.background import BackgroundScheduler

from get_docker_secret import get_docker_secret

import requests


class AuthService(object):
    """
    Service which handles authentication with Energy Robotics API.

    The access token is kept in memory and re-fetched if required.
    """

    def __init__(self, config: dict):
        self._logger = logging.getLogger(__name__)
        self._logger.debug(config)
        # check if config contains auth_service key if not raise error
        if "auth_service" not in config:
            raise ValueError("Config must contain auth_service parameters.")

        endpoint = config["auth_service"]["endpoint"]
        user_email = config["auth_service"]["user_email"]
        user_api_key_file = config["auth_service"]["user_api_key_file"]
        try:
            # TODO remove
            user_api_key = config["auth_service"]["user_api_key"]
        except KeyError:
            user_api_key = None
            pass
        # CHECK is this needed and correct?
        user_api_key = None if user_api_key_file is None else get_docker_secret(user_api_key_file, default=None)
        # load the API key from file if user_api_key_file is provided
        if user_api_key_file is not None:
            user_api_key = open(user_api_key_file).read().strip()
        try:
            refresh_interval = config["auth_service"]["refresh_interval"]
        except KeyError:
            refresh_interval = 300
            self._logger.warning("No refresh interval provided, using default value of 300 seconds.")
            pass

        self.__access_token = None
        self.__auth_scheduler = None

        if not endpoint:
            raise ValueError("Auth service endpoint must be provided.")
        if not user_email:
            raise ValueError("User email must be provided.")
        if not user_api_key:
            raise ValueError("User api key must be provided.")
        if not refresh_interval:
            raise ValueError("Refresh interval must be provided.")

        self._logger.debug(f"Initializing auth service with endpoint: {endpoint}")
        self.__endpoint = endpoint

        # Login credentials from user email and api key encoded in base64
        self.__login_credentials = base64.b64encode(f"{user_email}:{user_api_key}".encode()).decode("utf-8")
        self.__refresh_interval = refresh_interval
        self.__timeout = 5

    def __deepcopy__(self, memo):
        # TODO remove
        """
        Create a deep copy of the object with a new background scheduler and a new authentication loop,
        since a background scheduler cannot be deepcopied.

        In the depencency_injector when creating an instance a deepcopy is created, hence,
        this adapted deepcopy version is required.
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            # Do not copy the auth_scheduler
            if k != "_AuthService__auth_scheduler":
                setattr(result, k, copy.deepcopy(v, memo))

        # Reset auth token and scheduler
        result.__access_token = None
        result.__auth_scheduler = None

        return result

    def __del__(self):
        # Shutting the scheduler is not needed according to the documentation, but should be done if possible.
        if self.__auth_scheduler is not None:
            try:
                self.__auth_scheduler.shutdown()
                self._logger.debug("Shut down auth scheduler")
            except:
                pass

    def _authenticate(self):
        """
        Fetches a new access token and schedules a background job (if not done already) to refresh the toke before it can expire.
        """
        self._handle_access_token(self.__login_credentials, self.__timeout)

        # # Setup scheduler and re-authentication job
        if self.__auth_scheduler is None:
            self.__auth_scheduler = BackgroundScheduler()
            self.__auth_scheduler.start()

            self.__auth_scheduler.add_job(
                lambda: self._handle_access_token(self.__login_credentials, self.__timeout),
                "interval",
                seconds=self.__refresh_interval,
                max_instances=1,
            )

    def _handle_access_token(self, login_credentials: str, timeout: int):
        # TODO add reconnect cascade in case a call fails
        self._logger.debug("Fetching new access token")

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Basic {login_credentials}",
        }
        try:
            response = requests.post(self.__endpoint, json={}, headers=headers, timeout=timeout)
            if 200 <= response.status_code < 300:
                json_response = response.json()
                self.__access_token = json_response["access_token"]
                self._logger.info("Successfully fetched new access token")
            else:
                self._logger.error(f"Failed to fetch new access token: {response.status_code} {response.text}")
                self.__access_token = None
        except requests.exceptions.Timeout:
            self._logger.error(f"Failed to fetch new access token: Timeout.")
            self.__access_token = None
        except requests.exceptions.RequestException as e:
            self._logger.error(f"Failed to fetch new access token: Error when requesting: {e}.")
            self.__access_token = None

    def get_bearer_token(self):
        """
        Returns the current access token.
        :return: The current access token with Bearer prefix.
        """

        if not self.__access_token or self.__auth_scheduler is None:
            self._authenticate()

        if not self.__access_token:
            return None
        else:
            return f"Bearer {self.__access_token}"

    def get_auth_header(self):
        # Note: It is important to have a lower case "a" in "authorization".
        #   Some libraries convert that, but some don't and then the connection cannot be established properly!
        bearer = self.get_bearer_token()
        if not bearer:
            return None
        else:
            return {"authorization": bearer}
