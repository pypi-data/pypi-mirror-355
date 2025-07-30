# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import base64
import hashlib
import json
import logging
import re
from asyncio import TaskGroup
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Callable, Awaitable, AsyncIterator
from uuid import UUID

import kr8s
from exceptiongroup import suppress
from httpx import HTTPError, AsyncClient
from kr8s.asyncio.objects import Deployment, Service, Secret, Pod
from pydantic import HttpUrl
from tenacity import AsyncRetrying, stop_after_delay, wait_fixed, retry_if_exception_type

from beeai_server.service_layer.deployment_manager import IProviderDeploymentManager, global_provider_variables
from beeai_server.domain.models.provider import Provider, ProviderDeploymentState
from beeai_server.utils.logs_container import LogsContainer, ProcessLogMessage, ProcessLogType
from beeai_server.utils.utils import extract_messages

logger = logging.getLogger(__name__)


class KubernetesProviderDeploymentManager(IProviderDeploymentManager):
    def __init__(self, api_factory: Callable[[], Awaitable[kr8s.asyncio.Api]]):
        self._api_factory = api_factory

    @asynccontextmanager
    async def api(self) -> AsyncIterator[kr8s.asyncio.Api]:
        client = await self._api_factory()
        yield client

    def _get_k8s_name(self, provider_id: UUID, kind: str | None = None):
        return f"beeai-provider-{provider_id}" + (f"-{kind}" if kind else "")

    def _get_provider_id_from_name(self, name: str, kind: str | None = None) -> UUID:
        pattern = rf"beeai-provider-([0-9a-f-]+)-{kind}$" if kind else r"beeai-provider-([0-9a-f-]+)$"
        if match := re.match(pattern, name):
            [provider_id] = match.groups()
            return UUID(provider_id)
        raise ValueError(f"Invalid provider name format: {name}")

    def _get_env_for_provider(self, provider: Provider, env: dict[str, str | None]):
        return {**provider.extract_env(env), **global_provider_variables()}

    async def create_or_replace(self, *, provider: Provider, env: dict[str, str] | None = None) -> bool:
        if not provider.managed:
            raise ValueError("Attempted to update provider not managed by Kubernetes")

        async with self.api() as api:
            env = env or {}
            label = self._get_k8s_name(provider.id)
            service = Service(
                {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "metadata": {
                        "name": self._get_k8s_name(provider.id, "svc"),
                        "labels": {"app": label},
                    },
                    "spec": {
                        "type": "ClusterIP",
                        "ports": [{"port": 8000, "targetPort": 8000, "protocol": "TCP", "name": "http"}],
                        "selector": {"app": label},
                    },
                },
                api=api,
            )
            env = self._get_env_for_provider(provider, env)
            secret = Secret(
                {
                    "apiVersion": "v1",
                    "kind": "Secret",
                    "metadata": {
                        "name": self._get_k8s_name(provider.id, "secret"),
                        "labels": {"app": label},
                    },
                    "type": "Opaque",
                    "data": {key: base64.b64encode(value.encode()).decode() for key, value in env.items()},
                },
                api=api,
            )

            deployment_manifest = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self._get_k8s_name(provider.id, "deploy"),
                    "labels": {"app": label, "managedBy": "beeai-platform"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": {"app": label},
                    },
                    "template": {
                        "metadata": {"labels": {"app": label}},
                        "spec": {
                            "containers": [
                                {
                                    "name": self._get_k8s_name(provider.id, "container"),
                                    "image": str(provider.source.root),
                                    "imagePullPolicy": "IfNotPresent",
                                    "ports": [{"containerPort": 8000}],
                                    "envFrom": [{"secretRef": {"name": self._get_k8s_name(provider.id, "secret")}}],
                                    "livenessProbe": {
                                        "httpGet": {"path": "/ping", "port": 8000},
                                        "initialDelaySeconds": 1,
                                        "periodSeconds": 3,
                                        "timeoutSeconds": 2,
                                    },
                                    "readinessProbe": {
                                        "httpGet": {"path": "/ping", "port": 8000},
                                        "initialDelaySeconds": 1,
                                        "periodSeconds": 3,
                                        "timeoutSeconds": 2,
                                    },
                                }
                            ]
                        },
                    },
                },
            }
            combined_manifest = json.dumps(
                {"service": service.raw, "secret": secret.raw, "deployment": deployment_manifest}
            )
            deployment_hash = hashlib.sha256(combined_manifest.encode()).hexdigest()[:63]
            deployment_manifest["metadata"]["labels"]["deployment-hash"] = deployment_hash

            deployment = Deployment(deployment_manifest, api=api)
            try:
                existing_deployment = await Deployment.get(deployment.metadata.name, api=api)
                if existing_deployment.metadata.labels["deployment-hash"] == deployment_hash:
                    if existing_deployment.replicas == 0:
                        await deployment.scale(1)
                        return True
                    return False  # Deployment was not modified
                logger.info(f"Recreating deployment {deployment.metadata.name} due to configuration change")
                await self.delete(provider_id=provider.id)
            except kr8s.NotFoundError:
                logger.info(f"Creating new deployment {deployment.metadata.name}")
            try:
                await secret.create()
                await service.create()
                await deployment.create()
                await deployment.adopt(service)
                await deployment.adopt(secret)
            except Exception:
                # Try to revert changes already made
                with suppress(Exception):
                    await secret.delete()
                with suppress(Exception):
                    await service.delete()
                with suppress(Exception):
                    await deployment.delete()
                raise
            return True

    async def delete(self, *, provider_id: UUID) -> None:
        with suppress(kr8s.NotFoundError):
            async with self.api() as api:
                deploy = await Deployment.get(name=self._get_k8s_name(provider_id, "deploy"), api=api)
                await deploy.delete(propagation_policy="Foreground", force=True)
                await deploy.wait({"delete"})

    async def scale_down(self, *, provider_id: UUID) -> None:
        async with self.api() as api:
            deploy = await Deployment.get(name=self._get_k8s_name(provider_id, "deploy"), api=api)
            await deploy.scale(0)

    async def scale_up(self, *, provider_id: UUID) -> None:
        async with self.api() as api:
            deploy = await Deployment.get(name=self._get_k8s_name(provider_id, "deploy"), api=api)
            await deploy.scale(1)

    async def wait_for_startup(self, *, provider_id: UUID, timeout: timedelta) -> None:
        async with self.api() as api:
            deployment = await Deployment.get(name=self._get_k8s_name(provider_id, kind="deploy"), api=api)
            await deployment.wait("condition=Available", timeout=int(timeout.total_seconds()))
            # For some reason the first request sometimes doesn't come through
            # (the service does not route immediately after deploy is available?)
            async for attempt in AsyncRetrying(
                stop=stop_after_delay(timedelta(seconds=10)),
                wait=wait_fixed(timedelta(seconds=0.5)),
                retry=retry_if_exception_type(HTTPError),
                reraise=True,
            ):
                with attempt:
                    async with AsyncClient(
                        base_url=str(await self.get_provider_url(provider_id=provider_id))
                    ) as client:
                        resp = await client.get("ping", timeout=1)
                        resp.raise_for_status()

    async def state(self, *, provider_ids: list[UUID]) -> list[ProviderDeploymentState]:
        async with self.api() as api:
            deployments = {
                self._get_provider_id_from_name(deployment.metadata.name, "deploy"): deployment
                async for deployment in kr8s.asyncio.get(
                    kind="deployment",
                    label_selector={"managedBy": "beeai-platform"},
                    api=api,
                )
            }
            provider_ids_set = set(provider_ids)
            deployments = {provider_id: d for provider_id, d in deployments.items() if provider_id in provider_ids_set}
            states = []
            for provider_id in provider_ids:
                deployment = deployments.get(provider_id)
                if not deployment:
                    state = ProviderDeploymentState.missing
                elif deployment.status.get("availableReplicas", 0) > 0:
                    state = ProviderDeploymentState.running
                elif deployment.status.get("replicas", 0) == 0:
                    state = ProviderDeploymentState.ready
                else:
                    state = ProviderDeploymentState.starting
                states.append(state)
            return states

    async def get_provider_url(self, *, provider_id: UUID) -> HttpUrl:
        return HttpUrl(f"http://{self._get_k8s_name(provider_id, 'svc')}:8000")

    async def stream_logs(self, *, provider_id: UUID, logs_container: LogsContainer):
        try:
            async with self.api() as api:
                missing_logged = False
                while True:
                    try:
                        deploy = await Deployment.get(name=self._get_k8s_name(provider_id, kind="deploy"), api=api)
                        if pods := await deploy.pods():
                            break
                    except kr8s.NotFoundError:
                        ...
                    if not missing_logged:
                        logs_container.add_stdout("Provider is not running, run a query to start it up...")
                    missing_logged = True
                    await asyncio.sleep(1)

                if deploy.status.get("availableReplicas", 0) == 0:
                    async for event_stream_type, event in api.watch(
                        kind="event",
                        # TODO: we select for only one pod, for multi-pod agents this might hold up the logs for a while
                        field_selector=f"involvedObject.name=={pods[0].name},involvedObject.kind==Pod",
                    ):
                        message = event.raw.get("message", "")
                        logs_container.add_stdout(f"{event.raw.reason}: {message}")
                        if event.raw.reason == "Started":
                            break

                for attempt in range(10):
                    try:
                        _ = [log async for log in pods[0].logs(tail_lines=1)]
                        break
                    except kr8s.ServerError:
                        await asyncio.sleep(1)
                else:
                    logs_container.add_stdout("Container crashed or not starting up, attempting to get previous logs:")
                    with suppress(kr8s.ServerError):
                        previous_logs = [log async for log in pods[0].logs(previous=True)]
                        if previous_logs:
                            logs_container.add_stdout("Previous container logs:")
                            for log in previous_logs:
                                logs_container.add_stdout(f"Previous: {log}")
                    return

                # Stream logs from pods
                async def stream_logs(pod: Pod):
                    async for line in pod.logs(follow=True):
                        logs_container.add_stdout(
                            f"{pod.name.replace(self._get_k8s_name(provider_id, 'deploy'), '')}: {line}"
                        )

                async with TaskGroup() as tg:
                    for pod in await deploy.pods():
                        tg.create_task(stream_logs(pod))

        except Exception as ex:
            logs_container.add(
                ProcessLogMessage(stream=ProcessLogType.stderr, message=extract_messages(ex), error=True)
            )
            logger.error(f"Error while streaming logs: {extract_messages(ex)}")
            raise
