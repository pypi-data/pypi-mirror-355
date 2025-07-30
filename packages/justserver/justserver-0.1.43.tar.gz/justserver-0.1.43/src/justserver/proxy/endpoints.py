from abc import ABC, abstractmethod
import os
from kubernetes.config import load_config
from kubernetes.client import AppsV1Api, CoreV1Api

from justserver.logging import logger
from justserver.proxy.settings import settings

LABEL_SELECTOR = 'app.kubernetes.io/component=daemon'


class BaseEndpoints(ABC):
    @abstractmethod
    def get_endoints(self) -> list[str]: ...


class Endpoints(BaseEndpoints):
    def __init__(self):
        load_config()
        self._apps_v1 = AppsV1Api()
        self._core_v1 = CoreV1Api()
        self._namespace = settings.pod_namespace

    def get_endoints(self) -> list[str]:
        endpoints = self._core_v1.list_namespaced_pod(namespace=self._namespace, label_selector=LABEL_SELECTOR)
        return [f'http://{pod.status.pod_ip}:8000' for pod in endpoints.items]


class EnvEndpoints(BaseEndpoints):

    def get_endoints(self) -> list[str]:
        return settings.backend_url or []


def endpoints_collector() -> BaseEndpoints:
    if settings.backend_url is not None:
        logger.info(f'Using env variable endpoints {settings.backend_url}')
        return EnvEndpoints()
    else:
        logger.info(f'Using kubernetes endpoints')
        return Endpoints()
