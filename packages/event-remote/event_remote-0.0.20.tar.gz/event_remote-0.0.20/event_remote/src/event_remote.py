import requests
from event_local.events_local import EventsLocal
from event_external_local.event_external_local import EventExternalsLocal
from logger_local.MetaLogger import MetaLogger
from logger_local.LoggerLocal import Logger

from url_remote.action_name_enum import ActionName
from url_remote.component_name_enum import ComponentName
from url_remote.entity_name_enum import EntityName
from url_remote.our_url import OurUrl

from user_context_remote.user_context import UserContext
from python_sdk_remote.http_response import create_authorization_http_headers

from .event_constants import EventRemoteConstants

# TODO Let's use an array per environment_name from url-remote
DEFAULT_EVENT_API_VERSION = 1
external_valid_columns = ["system_id", "subsystem_id", "url", "external_event_identifier", "environment_id", "is_approved"]


class EventRemote(metaclass=MetaLogger, object=EventRemoteConstants.EVENT_REMOTE_CODE_LOGGER_OBJECT):
    def __init__(self, is_test_data: bool = False) -> None:
        self.events_local = EventsLocal(is_test_data=is_test_data)
        self.event_external_local = EventExternalsLocal(is_test_data=is_test_data)

        self.our_url = OurUrl()
        self.user_context = UserContext()

        self.logger = Logger.create_logger(
            object=EventRemoteConstants.EVENT_REMOTE_CODE_LOGGER_OBJECT,
            is_meta_logger=True,
            user_context=self.user_context
        )

        self.brand_name = EventRemoteConstants.BRAND_NAME
        self.environment_name = EventRemoteConstants.ENVIRONMENT_NAME
        self.user_jwt = self.user_context.get_user_jwt()
        self.is_test_data = is_test_data

    def get_url_by_action_name(self, action_name: ActionName, api_version: int = DEFAULT_EVENT_API_VERSION,
                               path_parameters: dict = None, query_parameters: dict = None):
        # optional query_parameters can be added if needed
        url = self.our_url.endpoint_url(
            brand_name=self.brand_name,
            environment_name=self.environment_name,
            component_name=ComponentName.EVENT.value,
            entity_name=EntityName.EVENT.value,
            version=api_version,
            action_name=action_name.value,
            path_parameters=path_parameters,
            query_parameters=query_parameters
        )
        return url

    # TODO: move this to ? and use in all remotes
    def _get_response(self, *, method: str, action: ActionName, path_parameters: dict = None,
                      query_parameters: dict = None, data_dict: dict = None) -> dict:
        try:
            data_dict = (data_dict or {}).copy()
            # TODO from http import HTTPMethod; HTTPMethod.GET
            if method != 'get':
                data_dict["isTestData"] = self.is_test_data
            else:
                query_parameters = query_parameters or {}
                query_parameters["isTestData"] = self.is_test_data
            data_dict = data_dict or None
            url = self.get_url_by_action_name(
                action, api_version=EventRemoteConstants.EVENT_API_VERSION,
                path_parameters=path_parameters,
                query_parameters=query_parameters)

            headers = create_authorization_http_headers(self.user_jwt)
            self.logger.info(object={"url": url, "data_dict": data_dict, "method": method})
            response = requests.request(method=method, url=url, json=data_dict, headers=headers)
            if response.status_code >= 400:
                self.logger.info(object={"url": url, "data_dict": data_dict, "method": method})
                self.logger.error(object={"response_status_code": response.status_code, "response_text": response.text})
                raise Exception(f"Error in response: {response.status_code} - {response.text}")

            self.logger.info(object={"response_status_code": response.status_code, "response_text": response.text})
            response_dict = response.json()
            if "error" in response_dict:
                raise Exception(response_dict)
            return response_dict

        except Exception as exception:
            raise exception

    def create_event(self, event_dict: dict) -> dict:
        response_dict = self._get_response(method='post', action=ActionName.CREATE_EVENT, data_dict=event_dict)
        return response_dict

    @staticmethod
    def _fix_event_external_dict(event_external_dict: dict) -> dict:
        url = event_external_dict.get("url", event_external_dict.get("website_url"))
        event_external_dict = {key: event_external_dict[key] for key in external_valid_columns if key in event_external_dict}
        event_external_dict["url"] = url
        return event_external_dict

    def create_event_external(self, event_external_dict: dict) -> dict[str, int]:
        event_dict = self.create_event(event_dict=event_external_dict)  # {'event_id': XXX, 'message': 'Event created successfully'}
        event_id = event_dict.get('event_id')

        event_external_dict = self._fix_event_external_dict(event_external_dict)
        event_external_id = self.event_external_local.insert(event_external_dict=event_external_dict)

        # TODO after creating event-event-external-local insert the mapping here

        event_ids = {
            'event_id': event_id,
            'event_external_id': event_external_id
        }
        return event_ids

    def get_event_by_event_id(self, event_id: int) -> dict:
        path_parameters = {'eventId': event_id}
        response_dict = self._get_response(method='get', action=ActionName.GET_EVENT_BY_ID, path_parameters=path_parameters)

        return response_dict

    def delete_event_by_id(self, event_id: int):
        path_parameters = {'eventId': event_id}
        response_dict = self._get_response(method='delete', action=ActionName.DELETE_EVENT_BY_ID,
                                           path_parameters=path_parameters)

        return response_dict

    def update_event_by_id(self, event_id: int, event_dict: dict):
        path_parameters = {'eventId': event_id}
        response_dict = self._get_response(method='put', action=ActionName.UPDATE_EVENT_BY_ID,
                                           path_parameters=path_parameters, data_dict=event_dict)

        return response_dict

    def update_event_external_by_id(self, event_external_id: int, event_external_dict: dict) -> None:
        event_external_dict = self._fix_event_external_dict(event_external_dict)
        self.event_external_local.update_by_event_external_id(
            event_external_id=event_external_id,
            event_external_dict=event_external_dict)

    def delete_event_external_by_id(self, event_external_id: int) -> None:
        self.event_external_local.delete_by_event_external_id(event_external_id=event_external_id)

    def get_event_by_event_external_id(self, event_external_id: int) -> dict:
        event_external_dict = self.event_external_local.select_by_event_external_id(event_external_id=event_external_id)
        return event_external_dict

    def get_test_event_id(self) -> int:
        test_id = self.events_local.get_test_event_id()
        return test_id
