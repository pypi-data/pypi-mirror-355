from logger_local.LoggerComponentEnum import LoggerComponentEnum
from python_sdk_remote.utilities import get_brand_name, get_environment_name
from url_remote.api_version_dicts import EVENT_API_VERSION_DICT


class EventRemoteConstants:
    DEVELOPER_EMAIL = 'gil.a@circ.zone'
    EVENT_REMOTE_COMPONENT_ID = 248
    EVENT_REMOTE_PYHTON_COMPONENT_NAME = 'event-remote-restapi-python-package'
    EVENT_REMOTE_CODE_LOGGER_OBJECT = {
        'component_id': EVENT_REMOTE_COMPONENT_ID,
        'component_name': EVENT_REMOTE_PYHTON_COMPONENT_NAME,
        'component_category': LoggerComponentEnum.ComponentCategory.Code.value,
        'developer_email': DEVELOPER_EMAIL
    }

    BRAND_NAME = get_brand_name()
    ENVIRONMENT_NAME = get_environment_name()
    EVENT_API_VERSION = EVENT_API_VERSION_DICT[ENVIRONMENT_NAME]
    SYSTEM_ID = 10

    EXTERNAL_EVENT_TABLE_NAME = 'event_external_table'

    EXTERNAL_EVENT_SCHEMA_NAME = 'event_external'

    EXTERNAL_EVENT_ID_COLUMN_NAME = 'event_external_id'

    EXTERNAL_EVENT_VIEW_NAME = 'event_external_view'
