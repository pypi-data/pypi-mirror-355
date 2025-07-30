import logging

from easyaudit.models import CRUDEvent, LoginEvent

logger = logging.getLogger(__name__)


class ModelBackend:
    def request(self, request_info):
        return request_info

    def crud(self, crud_info):
        return CRUDEvent.objects.create(**crud_info)

    def login(self, login_info):
        return LoginEvent.objects.create(**login_info)
