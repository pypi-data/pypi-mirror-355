# pylint: disable=too-many-locals
""" "Adapter to interact with the DAPI Server."""
from __future__ import annotations

import concurrent.futures
import functools
import io
import threading
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from importlib.metadata import version
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar
from urllib.parse import urljoin

import requests

from opendapi.adapters.git import ChangeTriggerEvent
from opendapi.cli.common import OpenDAPIEntity
from opendapi.config import OpenDAPIConfig
from opendapi.defs import HTTPMethod
from opendapi.logging import LogDistKey, Timer, logger, sentry_sdk
from opendapi.utils import (
    create_session_with_retries,
    dump_dict_to_yaml_str,
    has_dapi_file_materially_changed,
    has_underlying_model_changed,
    make_api_w_query_and_body,
)
from opendapi.validators.defs import CollectedFile

TOTAL_RETRIES = 5
RETRY_BACKOFF_FACTOR = 10

CICD_PERSISTED_FILE_SUFFIX = ".cicd.yaml"
OPENDAPI_FILEPATHS_RUNTIME_BLUEPRINT = "{runtime}/opendapi_filepaths.yaml"

T = TypeVar("T")

thread_local = threading.local()


def _create_configured_session() -> requests.Session:
    """Create a session with retries."""
    return create_session_with_retries(
        total_retries=TOTAL_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"],
    )


def _get_session() -> requests.Session:
    """Get a session with retries."""
    if not hasattr(thread_local, "session"):
        thread_local.session = _create_configured_session()
    return thread_local.session


@dataclass
class DAPIServerConfig:
    """Configuration for the DAPI Server."""

    server_host: str
    api_key: str
    mainline_branch_name: str
    register_on_merge_to_mainline: bool = True
    woven_integration_mode: str = None
    woven_configuration: str = None
    s3_persist_threadpool_size: int = 8

    @property
    def repo_being_configured(self) -> bool:
        """Check if the repo is configured."""
        return self.woven_configuration == "in_progress"


class CICDIntegration(Enum):
    """Enum for CICD integrations."""

    GITHUB_BUILDKITE = "github_buildkite"
    GITHUB_GITHUB = "github_github"


class DAPIServerRequestType(Enum):
    """Enum for DAPI Server Request Types."""

    CLIENT_CONFIG = "/v1/config/client/opendapi"
    CLIENT_FEATURE_FLAGS = "/v1/config/client/opendapi/feature_flags"
    GITHUB_BUILDKITE_CICD_START = "/v1/cicd/start/github_buildkite"
    GITHUB_GITHUB_CICD_START = "/v1/cicd/start/github_github"
    CICD_COMPLETE_BLUEPRINT = "/v1/cicd/complete/{integration}"
    CICD_GET_PRESIGNED_LINK_BLUEPRINT = "/v1/cicd/files/persist/{integration}/presigned"


@dataclass
class OpenDAPIEntityCICDMetadata:
    """Metadata for OpenDAPI entities"""

    entity: OpenDAPIEntity
    # NOTE: make sure this is formatted for the server!
    filepath: str
    # NOTE: decide if here post init we make sure that
    # head cannot be skipped generate if base wasnt?
    # I think that makes sense...
    base_collect: CollectedFile | None
    head_collect: CollectedFile | None
    integration_mode: str

    @functools.cached_property
    def entity_changed_from_base(self) -> bool:
        """Check if the model is changed from the model state at base."""
        # for a non-dapi file, any change to the **file** state from base
        # is considered a change
        if self.entity is not OpenDAPIEntity.DAPI:
            return (self.base_collect and self.base_collect.original) != (
                self.head_collect and self.head_collect.merged
            )

        # we note that the file can remain after the entity is deleted
        # in that case any file differences arent actual entity changes
        base_generated = self.base_collect.generated if self.base_collect else None
        head_generated = self.head_collect.generated if self.head_collect else None
        if not base_generated and not head_generated:
            return False

        # if it exists in one but not the other, then surely it was changed
        if bool(base_generated) != bool(head_generated):
            return True

        # entity exists at both, so we compare if there were any meaningful changes.
        # note that we compare merged - but prune it - so that nullability
        # changes are considered changes
        base_merged = self.base_collect.merged if self.base_collect else None
        head_merged = self.head_collect.merged if self.head_collect else None

        return has_underlying_model_changed(base_merged, head_merged)

    @property
    def entity_is_new(self) -> bool:
        """Check if the model is new"""
        # we do these gymnastics since the dapi file can remain after the entity
        # is deleted
        base_generated = self.base_collect.generated if self.base_collect else None
        return self.entity_changed_from_base and not base_generated

    @property
    def entity_is_deprecated(self) -> bool:
        """Check if the model is deprecated"""
        head_generated = self.head_collect.generated if self.head_collect else None
        return self.entity_changed_from_base and not head_generated

    # NOTE: entity cannot be changed from head, since we do not
    #       ever change anything at the ORM level

    @property
    def file_git_tracked(self) -> bool:
        """
        Check if the file is tracked by git
        determined if the file ever existed
        """
        return (
            self.head_collect is not None and self.head_collect.original is not None
        ) or (self.base_collect is not None and self.base_collect.original is not None)

    @functools.cached_property
    def _should_be_processed(self) -> Tuple[bool, str]:
        """Check if the entity should be processed"""
        # in shadow mode, we only run CICD if the dapi was onboarded
        # or is being onboarded
        # note about possibly doing something else for enrich
        # during shadow for a diff experience
        in_shadow_mode = self.integration_mode == "shadow"
        if in_shadow_mode and not self.file_git_tracked:
            return False, "SHADOW_MODE_AND_FILE_NOT_TRACKED"

        # the entity and file are not at head (therefore at least one is at base).
        # this is because either the model was just deleted, or both
        # the model and the dapi were just deleted. regardless,
        # there is nothing to check
        if not self.head_collect:
            return False, "ENTITY_AND_FILE_NOT_AT_HEAD"

        # first we handle non DAPI cases
        # any file changes from be processed
        if self.entity is not OpenDAPIEntity.DAPI:
            # if the **file** didnt exist and now exists in any capacity,
            # we need to process.
            # note that we consider file changes, since we **always** generate
            # a single opendapi file if there arent any for non dapis
            if (
                not (self.base_collect and self.base_collect.original)
                and self.head_collect.merged
            ):
                return True, "NON_DAPI_FILE_CREATED"

            # if the file changed from base, we need to process
            if (
                self.base_collect and self.base_collect.original
            ) != self.head_collect.merged:
                return True, "NON_DAPI_FILE_CHANGED_FROM_BASE"

            # if the file changed from head, we need to process
            if self.head_collect.merged != self.head_collect.original:
                return True, "NON_DAPI_FILE_CHANGED_FROM_HEAD"

            return False, "NON_DAPI_FILE_NO_CHANGE"

        # we consider if the model itself still exists
        if self.head_collect.generated:
            # there was a meaningful change to the model.
            # we need to process
            if self.entity_changed_from_base:
                return True, "MODEL_EXISTS_AND_ENTITY_CHANGED"

            # there was no meaningful change to the model, but
            # there is no dapi. we need to create one.
            if not self.head_collect.original:
                return True, "MODEL_EXISTS_AND_NO_FILE"

            # there was no meaningful change to the model, the dapi exists,
            # but the dapi materially differs from the model, meaning it is out of sync.
            # note that this only applies to actual models.
            # we need to process
            # note that we compare against merged, since we want to respect nullability changes
            if has_underlying_model_changed(
                self.head_collect.merged,
                self.head_collect.original,
            ):
                return True, "MODEL_EXISTS_AND_FILE_OUT_OF_SYNC"

            # no meaningful change to the model and the dapi is synced.
            # in this scenario, we just need to make sure that manual
            # changes are sane.
            # either the file was just added - which is the case above - or
            # the file was manually changed, in both cases we need to process
            if self.head_collect.original != (
                self.base_collect and self.base_collect.original
            ):
                return True, "MODEL_EXISTS_AND_FILE_CHANGE"

            return False, "MODEL_EXISTS_AND_NO_CHANGE"

        # now we consider the file existing but the model not existing.
        # if there were any changes to the file, we need to process
        # either the entity was just deleted but not the file, the file is a vestige and changed,
        # or the file was manually added
        if has_dapi_file_materially_changed(
            self.head_collect.original,
            self.base_collect and self.base_collect.original,
        ):
            return True, "MODEL_DOESNT_EXIST_FILE_EXISTS_AND_CHANGED"

        return False, "MODEL_DOESNT_EXIST_FILE_EXISTS_AND_NO_CHANGE"

    @functools.cached_property
    def should_be_processed(self) -> Tuple[bool, str]:
        """Check if the entity should be processed"""
        result, _ = self._should_be_processed
        return result

    @property
    def should_be_processed_reason(self) -> str:
        """Get the reason for processing the entity."""
        _, reason = self._should_be_processed
        return reason

    @functools.cached_property
    def orm_unsynced_at_base(self) -> bool:
        """
        Check if the ORM is unsynced at base.

        Can be due to the model not yet being onboarded,
        or if the metadata suggestions were not applied.
        """
        return (
            self.entity is OpenDAPIEntity.DAPI
            and bool(self.base_collect)
            and has_underlying_model_changed(
                self.base_collect.merged,
                self.base_collect.original,
            )
        )

    @property
    def for_server(self) -> dict:
        """Convert to dict."""
        return {
            "entity": self.entity.value,
            "filepath": self.filepath,
            "base_collect": self.base_collect.for_server if self.base_collect else None,
            "head_collect": self.head_collect.for_server if self.head_collect else None,
            "entity_changed_from_base": self.entity_changed_from_base,
            "entity_is_new": self.entity_is_new,
            "entity_is_deprecated": self.entity_is_deprecated,
            "file_git_tracked": self.file_git_tracked,
            "integration_mode": self.integration_mode,
            "should_be_processed": self.should_be_processed,
            "should_be_processed_reason": self.should_be_processed_reason,
            "orm_unsynced_at_base": self.orm_unsynced_at_base,
        }


class DAPIRequests:
    """Class to handle requests to the DAPI Server."""

    def __init__(
        self,
        dapi_server_config: DAPIServerConfig,
        trigger_event: ChangeTriggerEvent,
        opendapi_config: Optional[OpenDAPIConfig] = None,
        error_msg_handler: Optional[Callable[[str], None]] = None,
        error_exception_cls: Optional[Type[Exception]] = None,
        txt_msg_handler: Optional[Callable[[str], None]] = None,
        markdown_msg_handler: Optional[Callable[[str], None]] = None,
    ):  # pylint: disable=too-many-arguments
        self.dapi_server_config = dapi_server_config
        self.opendapi_config = opendapi_config
        self.trigger_event = trigger_event
        self.error_msg_handler = error_msg_handler
        self.error_exception_cls = error_exception_cls or Exception
        self.txt_msg_handler = txt_msg_handler
        self.markdown_msg_handler = markdown_msg_handler

        self.session = _get_session()

    def get_client_config_from_server(self) -> dict:
        """Get the config from the DAPI Server."""
        response, _ = self.raw_send_request_to_dapi_server(
            request_path=DAPIServerRequestType.CLIENT_CONFIG.value,
            method=HTTPMethod.GET,
        )
        response.raise_for_status()
        return response.json()

    def get_client_feature_flags_from_server(
        self,
        feature_flag_names: List[str],
    ) -> dict:
        """Get the feature flags from the DAPI Server."""
        response, _ = self.raw_send_request_to_dapi_server(
            request_path=DAPIServerRequestType.CLIENT_FEATURE_FLAGS.value,
            method=HTTPMethod.POST,
            query_params=None,
            body_json={
                "feature_flag_names": feature_flag_names,
                "client_context": self.build_client_context(
                    self.dapi_server_config, self.trigger_event
                ),
            },
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def build_client_context(
        dapi_server_config: DAPIServerConfig,
        trigger_event: ChangeTriggerEvent,
    ) -> dict:
        """Build the client context."""
        return {
            "meta": {
                "type": "opendapi",
                "version": f"opendapi-{version('opendapi')}",
                "integration_mode": dapi_server_config.woven_integration_mode,
                "repo_being_configured": dapi_server_config.repo_being_configured,
            },
            "change_trigger_event": {
                "source": trigger_event.integration_type,
                "repository": trigger_event.repo_full_name,
                "where": trigger_event.where,
                "event_type": trigger_event.event_type,
                "before_change_sha": trigger_event.before_change_sha,
                "after_change_sha": trigger_event.after_change_sha,
                "repo_html_url": trigger_event.repo_html_url,
                "pull_request_number": trigger_event.pull_request_number,
                "pull_request_link": trigger_event.pull_request_link,
                "branch": trigger_event.branch,
            },
        }

    def raw_send_request_to_dapi_server(
        self,
        request_path: str,
        method: HTTPMethod,
        query_params: Optional[dict] = None,
        body_json: Optional[dict] = None,
    ) -> Tuple[requests.Response, Dict]:
        """Send a request to the DAPI Server."""
        headers = {
            "Content-Type": "application/json",
            "X-DAPI-Server-API-Key": self.dapi_server_config.api_key,
        }
        # measure the time it takes to get a response from the server in milliseconds
        metrics_tags = {
            "request_path": request_path,
            "org_name": self.opendapi_config
            and self.opendapi_config.org_name_snakecase,
        }

        with Timer(LogDistKey.ASK_DAPI_SERVER) as _timer:
            response, _ = make_api_w_query_and_body(
                urljoin(self.dapi_server_config.server_host, request_path),
                headers=headers,
                query_params=query_params,
                body_json=body_json,
                method=method,
                timeout=60,
                req_session=self.session,
            )
            metrics_tags["status_code"] = response.status_code
            _timer.set_tags(metrics_tags)

        return response, metrics_tags

    def _handle_api_error(self, request_path: str, status_code: int) -> None:
        """Handle an error message."""
        msg = f"Something went wrong! API failure with {status_code} for {request_path}"
        if self.error_msg_handler:
            self.error_msg_handler(msg)
        raise self.error_exception_cls(msg)

    def _github_repo_cicd_init(
        self,
        request_path: str,
        runner_params: Dict[str, Any],
    ) -> Tuple[str, dict]:
        """
        Returns a common payload for all github repo operations
        """

        response, _ = self.raw_send_request_to_dapi_server(
            request_path=request_path,
            query_params={
                "repo_name": self.trigger_event.repo_full_name,
            },
            body_json={
                "event": self.trigger_event.event_type,
                "branch": self.trigger_event.branch,
                "base_commit_sha": self.trigger_event.before_change_sha,
                "head_commit_sha": self.trigger_event.after_change_sha,
                "head_commit_sha_timestamp": self.trigger_event.after_change_sha_timestamp,
                "pr_link": self.trigger_event.pull_request_link,
                "version": f"opendapi-{version('opendapi')}",
                **runner_params,
            },
            method=HTTPMethod.POST,
        )

        if response.status_code >= 400:
            self._handle_api_error(
                request_path,
                response.status_code,
            )

        response_json = response.json()
        return response_json["woven_cicd_id"], response_json["s3_upload_data"]

    def cicd_init_github_buildkite(
        self,
        job_id: str,
        job_started_at: datetime,
        build_id: str,
        retry_count: Optional[int] = None,
    ) -> Tuple[str, dict]:
        """Notify the DAPI Server that the GitHub CI/CD has started."""
        return self._github_repo_cicd_init(
            DAPIServerRequestType.GITHUB_BUILDKITE_CICD_START.value,
            {
                "job_id": job_id,
                "job_started_at": job_started_at.isoformat(),
                "build_id": build_id,
                "retry_count": retry_count,
            },
        )

    def cicd_init_github_github(
        self,
        run_id: str,
        run_attempt: int,
        run_number: int,
    ) -> Tuple[str, dict]:
        """Notify the DAPI Server that the GitHub CI/CD has started."""
        return self._github_repo_cicd_init(
            DAPIServerRequestType.GITHUB_GITHUB_CICD_START.value,
            {
                "run_id": run_id,
                "run_attempt": run_attempt,
                "run_number": run_number,
            },
        )

    def __upload_to_s3(
        self,
        filename: str,
        file_obj: io.BytesIO,
        s3_upload_data: Dict[str, str],
        notify_function: Optional[Callable[[int], None]] = lambda _: None,
    ) -> None:

        files = {"file": (filename, file_obj, s3_upload_data["fields"]["Content-Type"])}
        s3_upload_data["fields"]["key"] = s3_upload_data["fields"]["key"].replace(
            "${filename}", filename
        )
        response = _get_session().post(
            s3_upload_data["url"], data=s3_upload_data["fields"], files=files
        )
        notify_function(1)

        if response.status_code != 204:
            raise self.error_exception_cls(
                f"Failed to upload to S3: {response.status_code} - {response.text}"
            )

    def _cicd_upload_to_s3(
        self,
        runtime: str,
        s3_upload_data: Dict[str, str],
        cicd_metadata: OpenDAPIEntityCICDMetadata,
        notify_function: Optional[Callable[[int], None]] = lambda _: None,
    ) -> None:
        """Upload the CI/CD files to S3."""

        s3_upload_data = deepcopy(s3_upload_data)

        filename = (
            f"{runtime}/{cicd_metadata.entity.value}/"
            f"{cicd_metadata.filepath}{CICD_PERSISTED_FILE_SUFFIX}"
        )
        file_obj = io.BytesIO(
            dump_dict_to_yaml_str(cicd_metadata.for_server).encode("utf-8")
        )
        return self.__upload_to_s3(filename, file_obj, s3_upload_data, notify_function)

    def cicd_persist_files(
        self,
        s3_upload_data: Dict[str, str],
        base_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]],
        head_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]],
        runtime: str,
        notify_function: Optional[Callable[[int], None]] = None,
    ) -> Dict[OpenDAPIEntity, List[str]]:
        """Persist the CI/CD files with the DAPI Server."""
        # first, create the CICDMetadata objects
        total_entities = base_collected_files.keys() | head_collected_files.keys()
        opendapi_file_metadata: List[OpenDAPIEntityCICDMetadata] = []
        for entity in total_entities:
            bc_raw = base_collected_files.get(entity, {})
            bc = {
                collected_file.server_filepath: collected_file
                for collected_file in bc_raw.values()
            }
            hc_raw = head_collected_files.get(entity, {})
            hc = {
                collected_file.server_filepath: collected_file
                for collected_file in hc_raw.values()
            }
            total_filepaths = bc.keys() | hc.keys()
            for filepath in total_filepaths:
                opendapi_file_metadata.append(
                    OpenDAPIEntityCICDMetadata(
                        entity=entity,
                        filepath=filepath,
                        base_collect=bc.get(filepath),
                        head_collect=hc.get(filepath),
                        integration_mode=self.dapi_server_config.woven_integration_mode,
                    )
                )

        # then, upload the CICD files to S3 in parallel
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.dapi_server_config.s3_persist_threadpool_size
        ) as executor:
            futures = [
                executor.submit(
                    self._cicd_upload_to_s3,
                    runtime,
                    s3_upload_data,
                    cicd_metadata,
                    notify_function,
                )
                for cicd_metadata in opendapi_file_metadata
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:  # pylint: disable=broad-except
                    sentry_sdk.capture_exception(e)
                    # python 3.8 compatible way to cancel all futures
                    for f in futures:
                        f.cancel()
                    executor.shutdown(wait=False)
                    raise self.error_exception_cls(
                        "There was an error persisted files for CICD. "
                        "Please rerun the workflow to try again."
                    )

        filepath_by_entity = defaultdict(list)
        for cicd_metadata in opendapi_file_metadata:
            filepath_by_entity[cicd_metadata.entity].append(cicd_metadata.filepath)

        filename = OPENDAPI_FILEPATHS_RUNTIME_BLUEPRINT.format(runtime=runtime)
        file_obj = io.BytesIO(
            dump_dict_to_yaml_str(
                {
                    entity.value: filepaths
                    for entity, filepaths in filepath_by_entity.items()
                }
            ).encode("utf-8")
        )
        self.__upload_to_s3(filename, file_obj, s3_upload_data)

        return filepath_by_entity

    def cicd_start(
        self,
        integration: CICDIntegration,
        metadata_file: Dict[str, Any],
        woven_cicd_id: str,
    ) -> None:
        """Notify the DAPI Server that the CI/CD has completed."""
        request_path = DAPIServerRequestType.CICD_COMPLETE_BLUEPRINT.value.format(
            integration=integration.value
        )
        response, _ = self.raw_send_request_to_dapi_server(
            request_path=request_path,
            query_params={
                "woven_cicd_id": woven_cicd_id,
            },
            body_json={
                "metadata": metadata_file,
                "logs": logger.get_logs(),
            },
            method=HTTPMethod.POST,
        )
        if response.status_code >= 400:
            self._handle_api_error(request_path, response.status_code)

    def cicd_get_s3_upload_data(
        self,
        woven_cicd_id: str,
        integration: CICDIntegration,
    ) -> dict:
        """Get the S3 upload data for the CI/CD."""
        request_path = (
            DAPIServerRequestType.CICD_GET_PRESIGNED_LINK_BLUEPRINT.value.format(
                integration=integration.value
            )
        )
        response, _ = self.raw_send_request_to_dapi_server(
            request_path=request_path,
            query_params={
                "woven_cicd_id": woven_cicd_id,
            },
            method=HTTPMethod.GET,
        )
        if response.status_code >= 400:
            self._handle_api_error(request_path, response.status_code)
        return response.json()["s3_upload_data"]
