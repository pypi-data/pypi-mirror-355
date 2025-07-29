import atexit
import os
import sys
import tempfile
import time

from datetime import datetime
from typing import Dict, List, Optional

from clipped.utils.env import get_run_env
from clipped.utils.hashing import hash_value
from clipped.utils.json import orjson_dumps
from clipped.utils.paths import (
    check_or_create_path,
    copy_file_or_dir_path,
    get_base_filename,
    get_path_extension,
    set_permissions,
)

from polyaxon import settings
from polyaxon._client.decorators import client_handler
from polyaxon._connections import CONNECTION_CONFIG, V1Connection
from polyaxon._constants.globals import UNKNOWN
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.getters import (
    get_artifacts_store_name,
    get_collect_artifacts,
    get_collect_resources,
    get_log_level,
)
from polyaxon._env_vars.keys import ENV_KEYS_HAS_PROCESS_SIDECAR
from polyaxon._sidecar.processor import SidecarThread
from polyaxon._utils.fqn_utils import to_fqn_name
from polyaxon.client import PolyaxonClient, RunClient
from polyaxon.schemas import LifeCycle, V1ProjectFeature, V1Statuses
from traceml.artifacts import V1ArtifactKind
from traceml.events import LoggedEventSpec, V1Event, V1EventSpan, get_asset_path
from traceml.logger import logger
from traceml.processors import events_processors
from traceml.processors.logs_processor import end_log_processor, start_log_processor
from traceml.serialization.writer import (
    EventFileWriter,
    ResourceFileWriter,
    LogsFileWriter,
)


class Run(RunClient):
    """Run tracking is client to instrument your machine learning model and track experiments.

    If no values are passed to this class,
    Polyaxon will try to resolve the owner, project, and run uuid from the environment:
     * If you have a configured CLI, Polyaxon will use the configuration of the cli.
     * If you have a cached run using the CLI, the client will default to that cached run
       unless you override the values.
     * If you use this client in the context of a job or a service managed by Polyaxon,
       a configuration will be available to resolve the values based on that run.

    You can always access the `self.client` to execute more APIs.

    Properties:
        project: str.
        owner: str.
        run_uuid: str.
        run_data: V1Run.
        status: str.
        namespace: str.
        client: [PolyaxonClient](/docs/core/python-library/polyaxon-client/)

    Args:
        owner: str, optional,
             the owner is the username or the organization name owning this project.
        project: str, optional, project name owning the run(s).
        run_uuid: str, optional, run uuid.
        client: [PolyaxonClient](/docs/core/python-library/polyaxon-client/), optional,
             an instance of a configured client, if not passed,
             a new instance will be created based on the available environment.
        track_code: bool, optional, default True, to track code version.
             Polyaxon will try to track information about any repo
             configured in the context where this client is instantiated.
        track_env: bool, optional, default True, to track information about the environment.
        track_logs: bool, optional, default True, to track logs for manually managed runs.
        refresh_data: bool, optional, default False, to refresh the run data at instantiation.
        artifacts_path: str, optional, for in-cluster runs it will be set automatically.
        collect_artifacts: bool, optional,
             similar to the env var flag `POLYAXON_COLLECT_ARTIFACTS`, this env var is `True`
             by default for managed runs and is controlled by the plugins section.
        collect_resources: bool, optional,
             similar to the env var flag `POLYAXON_COLLECT_RESOURCES`, this env var is `True`
             by default for managed runs and is controlled by the plugins section.
        is_new: bool, optional,
             Force the creation of a new run instead of trying to discover a cached run or
             refreshing an instance from the env var
        is_offline: bool, optional,
             To trigger the offline mode manually instead of depending on `POLYAXON_IS_OFFLINE`.
        no_op: bool, optional,
             To set the NO_OP mode manually instead of depending on `POLYAXON_NO_OP`.
        name: str, optional,
             When `is_new` or `is_offline` is set to true, a new instance is created and
             you can initialize that new run with a name.
        description: str, optional,
             When `is_new` or `is_offline` is set to true, a new instance is created and
             you can initialize that new run with a description.
        tags: str or List[str], optional,
             When `is_new` or `is_offline` is set to true, a new instance is created and
             you can initialize that new run with tags.

    Raises:
        PolyaxonClientException: If no owner and/or project are passed and Polyaxon cannot
             resolve the values from the environment.
    """

    @client_handler(check_no_op=True)
    def __init__(
        self,
        owner: Optional[str] = None,
        project: Optional[str] = None,
        run_uuid: Optional[str] = None,
        client: Optional[PolyaxonClient] = None,
        track_code: bool = True,
        track_env: bool = True,
        track_logs: bool = True,
        refresh_data: bool = False,
        artifacts_path: Optional[str] = None,
        collect_artifacts: Optional[bool] = None,
        collect_resources: Optional[bool] = None,
        is_new: Optional[bool] = None,
        is_offline: Optional[bool] = None,
        no_op: Optional[bool] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_create: bool = True,
    ):
        super().__init__(
            owner=owner,
            project=project,
            run_uuid=run_uuid,
            client=client,
            is_offline=is_offline,
            no_op=no_op,
        )
        track_logs = track_logs if track_logs is not None else self._is_offline
        self._artifacts_path = None
        self._outputs_path = None
        self._event_logger = None
        self._resource_logger = None
        self._logs_logger = None
        self._sidecar = None
        self._exit_handler = None
        self._store_path = None

        is_new = is_new or (
            self._run_uuid is None and not settings.CLIENT_CONFIG.is_managed
        )
        has_process_sidecar = os.environ.get(ENV_KEYS_HAS_PROCESS_SIDECAR, False)

        if auto_create and (is_new or self._is_offline):
            super().create(name=name, description=description, tags=tags)

        if (
            not is_new
            and self._run_uuid
            and (refresh_data or settings.CLIENT_CONFIG.is_managed)
        ):
            self.refresh_data()

        self._init_artifacts_tracking(
            artifacts_path=artifacts_path,
            collect_artifacts=collect_artifacts,
            collect_resources=collect_resources,
            is_new=is_new,
            has_process_sidecar=has_process_sidecar,
        )

        # Track run env
        if self._artifacts_path and track_env:
            self.log_env()

        # Track code
        if (is_new or has_process_sidecar) and track_code:
            self.log_code_ref()

        if (is_new or has_process_sidecar) and self._artifacts_path and track_logs:
            self.set_run_logs_logger()
            start_log_processor(add_logs=self._logs_logger.add_event)

        self._set_exit_handler(force=is_new or has_process_sidecar)

    def _init_artifacts_tracking(
        self,
        artifacts_path: Optional[str] = None,
        collect_artifacts: Optional[bool] = None,
        collect_resources: Optional[bool] = None,
        is_new: Optional[bool] = None,
        has_process_sidecar: Optional[bool] = None,
    ):
        if (settings.CLIENT_CONFIG.is_managed and self.run_uuid) or artifacts_path:
            self.set_artifacts_path(artifacts_path, is_related=is_new)
        if not self._artifacts_path and self._is_offline:
            self.set_artifacts_path(artifacts_path)

        # no artifacts path is set, we use the temp path
        if not self._artifacts_path:
            artifacts_path = ctx_paths.CONTEXT_ARTIFACTS_FORMAT.format(self.run_uuid)
            self.set_artifacts_path(artifacts_path)

        if self._artifacts_path and get_collect_artifacts(
            arg=collect_artifacts,
            default=self._is_offline or is_new or has_process_sidecar,
        ):
            self.set_run_event_logger()
            if get_collect_resources(
                arg=collect_resources,
                default=self._is_offline or is_new or has_process_sidecar,
            ):
                self.set_run_resource_logger()
            if has_process_sidecar or (
                not self._is_offline and not settings.CLIENT_CONFIG.is_managed
            ):
                self.set_run_process_sidecar()

    def _add_event(self, event: LoggedEventSpec):
        if self._event_logger:
            self._event_logger.add_event(event)
        else:
            logger.warning(
                "Could not log event {}, "
                "the event logger was not configured properly".format(event.name)
            )

    def _add_events(self, events: List[LoggedEventSpec]):
        if self._event_logger:
            self._event_logger.add_events(events)
        else:
            logger.warning(
                "Could not log events {}, "
                "the event logger was not configured properly".format(len(events))
            )

    def create(self, **kwargs):
        raise NotImplementedError(
            "The tracking `Run` subclass does not allow to call "
            "`create` method manually, please create a new instance of `Run` with `is_new=True`"
        )

    def get_connections_catalog(self) -> Optional[List[V1Connection]]:
        """Returns the current connections catalog requested by this run."""
        catalog = CONNECTION_CONFIG.catalog
        if catalog:
            return catalog.connections

    def get_artifacts_store_connection(self) -> Optional[V1Connection]:
        """Returns the current artifacts store connection used by this run."""
        return CONNECTION_CONFIG.get_connection_for(get_artifacts_store_name())

    def _get_store_path(self):
        if self._store_path:
            return self._store_path
        connection = self.get_artifacts_store_connection()
        if not connection:
            logger.warning("Artifacts store connection not detected.")
            return None
        self._store_path = os.path.join(connection.store_path, self.run_uuid)
        return self._store_path

    @client_handler(check_no_op=True)
    def get_artifacts_path(
        self,
        rel_path: Optional[str] = None,
        ensure_path: bool = False,
        is_dir: bool = False,
        use_store_path: bool = False,
    ):
        """Get the absolute path of the specified artifact in the currently active run.

        If `rel_path` is specified, the artifact root path of the currently active
        run will be returned: `root_run_artifacts_path/rel_path`.
        If `rel_path` is not specified, the current root artifacts path configured
        for this instance will be returned: `root_run_artifacts_path`.

        If `ensure_path` is provided, the path will be created. By default the path will
        be created until the last part of the `rel_path` argument,
        if `is_dir` is True, the complete `rel_path` is created.

        If `use_store_path` is enabled, the path returned will be relative to the artifacts
        store path and not Polyaxon's context. Please note that,
        the library will not ensure that the path exists when this flag is set to true.

        Args:
            rel_path: str, optional.
            ensure_path: bool, optional, default True.
            is_dir: bool, optional, default False.
            use_store_path: bool, default False.
        Returns:
            str, artifacts_path
        """
        artifacts_path = (
            self._get_store_path() if use_store_path else self._artifacts_path
        )
        artifacts_path = artifacts_path or self._artifacts_path
        if rel_path:
            path = os.path.join(artifacts_path, rel_path)
            if ensure_path and not use_store_path:
                try:
                    check_or_create_path(path, is_dir=is_dir)
                except Exception as e:  # noqa
                    logger.debug("Failed ensuring paths {}. Error {}", path, e)
            return path
        return artifacts_path

    @client_handler(check_no_op=True)
    def get_outputs_path(
        self,
        rel_path: Optional[str] = None,
        ensure_path: bool = True,
        is_dir: bool = False,
        use_store_path: bool = False,
    ):
        """Get the absolute outputs path of the specified artifact in the currently active run.

        If `rel_path` is specified, the outputs artifact root path of the currently active
        run will be returned: `root_run_artifacts_path/outputs/rel_path`.
        If `rel_path` is not specified, the current root artifacts path configured
        for this instance will be returned: `root_run_artifacts_path/outputs`.

        If `ensure_path` is provided, the path will be created. By default the path will
        be created until the last part of the `rel_path` argument,
        if `is_dir` is True, the complete `rel_path` is created.


        If `use_store_path` is enabled, the path returned will be relative to the artifacts
        store path and not Polyaxon's context. Please note that,
        the library will not ensure that the path exists when this flag is set to true.

        Args:
            rel_path: str, optional.
            ensure_path: bool, optional, default True.
            is_dir: bool, optional, default False.
            use_store_path: bool, default False.
        Returns:
            str, outputs_path
        """
        if use_store_path:
            artifacts_path = self._get_store_path()
            if artifacts_path:
                outputs_path = ctx_paths.CONTEXTS_OUTPUTS_SUBPATH_FORMAT.format(
                    artifacts_path
                )
            else:
                outputs_path = self._outputs_path
        else:
            outputs_path = self._outputs_path

        if rel_path:
            path = os.path.join(outputs_path, rel_path)
            if ensure_path:
                check_or_create_path(path, is_dir=is_dir)
            return path
        return outputs_path

    @client_handler(check_no_op=True, can_log_outputs=True)
    def get_tensorboard_path(
        self, rel_path: str = "tensorboard", use_store_path: bool = False
    ):
        """Returns a tensorboard path for this run relative to the outputs path.

        If `use_store_path` is enabled, the path returned will be relative to the artifacts
        store path and not Polyaxon's context. Please note that,
        the library will not ensure that the path exists when this flag is set to true.

        Args:
            rel_path: str, optional, default "tensorboard",
                 the relative path to the `outputs` context.
            use_store_path: bool, default False.
        Returns:
            str, outputs_path/rel_path
        """
        path = self.get_outputs_path(rel_path, use_store_path=use_store_path)
        self.log_tensorboard_ref(path)
        return path

    @client_handler(check_no_op=True)
    def set_artifacts_path(
        self, artifacts_path: Optional[str] = None, is_related: bool = False
    ):
        """Sets the root artifacts_path.

        > **Note**: Both `in-cluster` and `offline` modes will call this method automatically.
        > Be careful, this method is called automatically. Polyaxon has some processes
        > to automatically sync your run's artifacts and outputs.

        Args:
            artifacts_path: str, optional
            is_related: bool, optional,
                 To create multiple runs in-cluster in a notebook or a vscode session.
        """
        if artifacts_path:
            _artifacts_path = artifacts_path
        elif self._is_offline:
            _artifacts_path = ctx_paths.get_offline_path(
                entity_value=self.run_uuid, entity_kind=V1ProjectFeature.RUNTIME
            )
        elif is_related:
            _artifacts_path = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_RELATED_FORMAT.format(
                self.run_uuid
            )
        else:
            _artifacts_path = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(
                self.run_uuid
            )

        _outputs_path = ctx_paths.CONTEXTS_OUTPUTS_SUBPATH_FORMAT.format(
            _artifacts_path
        )
        try:
            check_or_create_path(_artifacts_path, is_dir=True)
            check_or_create_path(_outputs_path, is_dir=True)
        except Exception as e:  # noqa
            logger.debug("Failed ensuring outputs/artifacts paths {}", e)
        self._artifacts_path = _artifacts_path
        self._outputs_path = _outputs_path

    @client_handler(check_no_op=True)
    def set_run_event_logger(self):
        """Sets an event logger.

        > **Note**: Both `in-cluster` and `offline` modes will call this method automatically.
        > Be careful, this method is called automatically. Polyaxon has some processes
        > to automatically sync your run's artifacts and outputs.
        """
        self._event_logger = EventFileWriter(run_path=self._artifacts_path)

    @client_handler(check_no_op=True)
    def set_run_resource_logger(self):
        """Sets an resources logger.

        > **Note**: Both `in-cluster` and `offline` modes will call this method automatically.
        > Be careful, this method is called automatically. Polyaxon has some processes
        > to automatically sync your run's artifacts and outputs.
        """
        self._resource_logger = ResourceFileWriter(run_path=self._artifacts_path)

    @client_handler(check_no_op=True)
    def set_run_logs_logger(self):
        """Sets a logs logger.

        > **Note**: This is only used during manual tracking, and it's not used by the `
        > in-cluster` runs.
        """
        self._logs_logger = LogsFileWriter(run_path=self._artifacts_path)

    @client_handler(check_no_op=True)
    def set_run_process_sidecar(self):
        """Sets a sidecar process to sync artifacts.

        > **Note**: Both `in-cluster` and `offline` modes will call this method automatically.
        > Be careful, this method is called automatically. Polyaxon has some processes
        > to automatically sync your run's artifacts and outputs.
        """
        self._sidecar = SidecarThread(client=self, run_path=self._artifacts_path)
        self._sidecar.start()

    def _set_exit_handler(self, force: bool = False):
        if self._is_offline or force:
            self._start()
        elif settings.CLIENT_CONFIG.is_managed:
            self._register_exit_handler(self._wait)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_metric(
        self,
        name: str,
        value: float,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a metric datapoint.

        ```python
        >>> log_metric(name="loss", value=0.01, step=10)
        ```

        > **Note**: It's very important to log `step` as one of your metrics
        > if you want to compare experiments on the dashboard
        > and use the steps in x-axis instead of timestamps.

        > **Note**: To log multiple metrics at once you can use `log_metrics`.

        Args:
            name: str, metric name
            value: float, metric value
            step: int, optional
            timestamp: datetime, optional
        """
        name = to_fqn_name(name)
        self._log_has_metrics()

        events = []
        event_value = events_processors.metric(value)
        if isinstance(event_value, str) and event_value == UNKNOWN:
            return
        events.append(
            LoggedEventSpec(
                name=name,
                kind=V1ArtifactKind.METRIC,
                event=V1Event.make(timestamp=timestamp, step=step, metric=event_value),
            )
        )
        if events:
            self._add_events(events)
            self._results[name] = event_value

    @client_handler(check_no_op=True, can_log_events=True)
    def log_metrics(
        self,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        **metrics,
    ):
        """Logs multiple metrics.

        ```python
        >>> log_metrics(step=123, loss=0.023, accuracy=0.91)
        ```

        > **Note**: It's very important to log `step` as one of your metrics
        > if you want to compare experiments on the dashboard
        > and use the steps in x-axis instead of timestamps.

        Args:
            step: int, optional
            timestamp: datetime, optional
            metrics: kwargs, key=value
        """
        self._log_has_metrics()

        events = []
        for metric in metrics:
            metric_name = to_fqn_name(metric)
            event_value = events_processors.metric(metrics[metric])
            if isinstance(event_value, str) and event_value == UNKNOWN:
                continue
            events.append(
                LoggedEventSpec(
                    name=metric_name,
                    kind=V1ArtifactKind.METRIC,
                    event=V1Event.make(
                        timestamp=timestamp, step=step, metric=event_value
                    ),
                )
            )
        if events:
            self._add_events(events)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_roc_auc_curve(
        self,
        name: str,
        fpr,
        tpr,
        auc=None,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs ROC/AUC curve. This method expects an already processed values.

        ```python
        >>> log_roc_auc_curve("roc_value", fpr, tpr, auc=0.6, step=1)
        ```
        Args:
            name: str, name of the curve
            fpr: List[float] or numpy.array, false positive rate
            tpr: List[float] or numpy.array, true positive rate
            auc: float, optional, calculated area under curve
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        event_value = events_processors.roc_auc_curve(
            fpr=fpr,
            tpr=tpr,
            auc=auc,
        )
        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.CURVE,
            event=V1Event.make(timestamp=timestamp, step=step, curve=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_sklearn_roc_auc_curve(
        self,
        name: str,
        y_preds,
        y_targets,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        is_multi_class: bool = False,
    ):
        """Calculates and logs ROC/AUC curve using sklearn.

        ```python
        >>> log_sklearn_roc_auc_curve("roc_value", y_preds, y_targets, step=10)
        ```

        If you are logging a multi-class roc curve, you should set
        `is_multi_class=True` to allow persisting curves for all classes.

        Args:
            name: str, name of the curve
            y_preds: List[float] or numpy.array
            y_targets: List[float] or numpy.array
            step: int, optional
            timestamp: datetime, optional
            is_multi_class: bool, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        def create_event(chart_name, y_p, y_t, pos_label=None):
            event_value = events_processors.sklearn_roc_auc_curve(
                y_preds=y_p,
                y_targets=y_t,
                pos_label=pos_label,
            )
            logged_event = LoggedEventSpec(
                name=chart_name,
                kind=V1ArtifactKind.CURVE,
                event=V1Event.make(timestamp=timestamp, step=step, curve=event_value),
            )
            self._add_event(logged_event)

        if is_multi_class:
            import numpy as np

            classes = np.unique(y_targets)
            for i in range(len(classes)):
                create_event(
                    "{}_{}".format(name, i), y_preds[:, i], y_targets, classes[i]
                )
        else:
            create_event(name, y_preds, y_targets)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_pr_curve(
        self,
        name: str,
        precision,
        recall,
        average_precision=None,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs PR curve. This method expects an already processed values.

        ```python
        >>> log_pr_curve("pr_value", precision, recall, step=10)
        ```

        Args:
            name: str, name of the curve
            y_preds: List[float] or numpy.array
            y_targets: List[float] or numpy.array
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        event_value = events_processors.pr_curve(
            precision=precision,
            recall=recall,
            average_precision=average_precision,
        )
        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.CURVE,
            event=V1Event.make(timestamp=timestamp, step=step, curve=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_sklearn_pr_curve(
        self,
        name: str,
        y_preds,
        y_targets,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        is_multi_class: bool = False,
    ):
        """Calculates and logs PR curve using sklearn.

        ```python
        >>> log_sklearn_pr_curve("pr_value", y_preds, y_targets, step=10)
        ```

        If you are logging a multi-class roc curve, you should set
        `is_multi_class=True` to allow persisting curves for all classes.

        Args:
            name: str, name of the event
            y_preds: List[float] or numpy.array
            y_targets: List[float] or numpy.array
            step: int, optional
            timestamp: datetime, optional
            is_multi_class: bool, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        def create_event(chart_name, y_p, y_t, pos_label=None):
            event_value = events_processors.sklearn_pr_curve(
                y_preds=y_p,
                y_targets=y_t,
                pos_label=pos_label,
            )
            logged_event = LoggedEventSpec(
                name=chart_name,
                kind=V1ArtifactKind.CURVE,
                event=V1Event.make(timestamp=timestamp, step=step, curve=event_value),
            )
            self._add_event(logged_event)

        if is_multi_class:
            import numpy as np

            classes = np.unique(y_targets)
            for i in range(len(classes)):
                create_event(
                    "{}_{}".format(name, i), y_preds[:, i], y_targets, classes[i]
                )
        else:
            create_event(name, y_preds, y_targets)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_curve(
        self,
        name: str,
        x,
        y,
        annotation=None,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a custom curve.

        ```python
        >>> log_curve("pr_value", x, y, annotation="more=info", step=10)
        ```

        Args:
            name: str, name of the curve
            x: List[float] or numpy.array
            y: List[float] or numpy.array
            annotation: str, optional
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        event_value = events_processors.curve(
            x=x,
            y=y,
            annotation=annotation,
        )
        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.CURVE,
            event=V1Event.make(timestamp=timestamp, step=step, curve=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_confusion_matrix(
        self,
        name: str,
        x,
        y,
        z,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a custom curve.

        ```python
        >>> z = [[0.1, 0.3, 0.5, 0.2],
        >>>      [1.0, 0.8, 0.6, 0.1],
        >>>      [0.1, 0.3, 0.6, 0.9],
        >>>      [0.6, 0.4, 0.2, 0.2]]
        >>>
        >>> x = ['healthy', 'multiple diseases', 'rust', 'scab']
        >>> y = ['healthy', 'multiple diseases', 'rust', 'scab']
        >>> log_confusion_matrix("confusion_test", x, y, z, step=11)
        ```

        Args:
            name: str, name of the curve
            x: List[float] or List[str] or numpy.array
            x: List[float] or List[str] or numpy.array
            z: List[List[float]] or List[List[str]] or numpy.array
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        try:
            event_value = events_processors.confusion_matrix(
                x=x,
                y=y,
                z=z,
            )
        except ValueError as e:
            logger.warning(
                "Confusion matrix %s could not be logged, "
                "please make sure you are passing 3 lists/arrays "
                "with the same length. "
                "Error %s",
                name,
                e,
            )
            return
        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.CONFUSION,
            event=V1Event.make(timestamp=timestamp, step=step, confusion=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_image(
        self,
        data,
        name: Optional[str] = None,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        rescale: int = 1,
        dataformats: str = "CHW",
        ext: Optional[str] = None,
    ):
        """Logs an image.

        ```python
        >>> log_image(data="path/to/image.png", step=10)
        >>> log_image(data=np_array, name="generated_image", step=10)
        ```

        Args:
            data: str or numpy.array, a file path or numpy array
            name: str,
                 name of the image, if a path is passed this can be optional
                 and the name of the file will be used
            step: int, optional
            timestamp: datetime, optional
            rescale: int, optional
            dataformats: str, optional
            ext: str, optional, default extension to use, note that if you pass a
                 file polyaxon will automatically guess the extension
        """
        self._log_has_events()

        is_file = isinstance(data, str) and os.path.exists(data)
        ext = ext or "png"
        if is_file:
            name = name or get_base_filename(data)
            ext = get_path_extension(filepath=data) or ext
        else:
            name = name or "image"
        name = self._sanitize_filename(name)

        asset_path = get_asset_path(
            run_path=self._artifacts_path,
            kind=V1ArtifactKind.IMAGE,
            name=name,
            step=step,
            ext=ext,
        )
        asset_rel_path = os.path.relpath(asset_path, self._artifacts_path)
        if is_file:
            event_value = events_processors.image_path(
                from_path=data,
                asset_path=asset_path,
                asset_rel_path=asset_rel_path,
            )
        elif hasattr(data, "encoded_image_string"):
            event_value = events_processors.encoded_image(
                asset_path=asset_path,
                data=data,
                asset_rel_path=asset_rel_path,
            )
        else:
            event_value = events_processors.image(
                asset_path=asset_path,
                data=data,
                rescale=rescale,
                dataformats=dataformats,
                asset_rel_path=asset_rel_path,
            )

        if isinstance(event_value, str) and event_value == UNKNOWN:
            return

        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.IMAGE,
            event=V1Event.make(timestamp=timestamp, step=step, image=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_image_with_boxes(
        self,
        tensor_image,
        tensor_boxes,
        name: Optional[str] = None,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        rescale: int = 1,
        dataformats: str = "CHW",
    ):
        """Logs an image with bounding boxes.

        ```python
        >>> log_image_with_boxes(
        >>>     name="my_image",
        >>>     tensor_image=np.arange(np.prod((3, 32, 32)), dtype=float).reshape((3, 32, 32)),
        >>>     tensor_boxes=np.array([[10, 10, 40, 40]]),
        >>> )
        ```

        Args:
            tensor_image: numpy.array or str: Image data or file name
            tensor_boxes: numpy.array or str:
                 Box data (for detected objects) box should be represented as [x1, y1, x2, y2]
            name: str, name of the image
            step: int, optional
            timestamp: datetime, optional
            rescale: int, optional
            dataformats: str, optional
        """
        self._log_has_events()

        name = name or "figure"
        name = self._sanitize_filename(name)
        asset_path = get_asset_path(
            run_path=self._artifacts_path,
            kind=V1ArtifactKind.IMAGE,
            name=name,
            step=step,
            ext="png",
        )
        asset_rel_path = os.path.relpath(asset_path, self._artifacts_path)
        event_value = events_processors.image_boxes(
            asset_path=asset_path,
            tensor_image=tensor_image,
            tensor_boxes=tensor_boxes,
            rescale=rescale,
            dataformats=dataformats,
            asset_rel_path=asset_rel_path,
        )
        if isinstance(event_value, str) and event_value == UNKNOWN:
            return
        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.IMAGE,
            event=V1Event.make(timestamp=timestamp, step=step, image=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_mpl_image(
        self,
        data,
        name: Optional[str] = None,
        close: bool = True,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a matplotlib image.

        ```python
        >>> log_mpl_image(name="figure", data=figure, step=1, close=False)
        ```

        Args:
            data: matplotlib.pyplot.figure or List[matplotlib.pyplot.figure]
            name: sre, optional, name
            close: bool, optional, default True
            step: int, optional
            timestamp: datetime, optional
        """
        name = name or "figure"
        name = self._sanitize_filename(name)
        if isinstance(data, list):
            event_value = events_processors.figures_to_images(figures=data, close=close)

            if isinstance(event_value, str) and event_value == UNKNOWN:
                return

            self.log_image(
                name=name,
                data=event_value,
                step=step,
                timestamp=timestamp,
                dataformats="NCHW",
            )
        else:
            event_value = events_processors.figure_to_image(figure=data, close=close)
            self.log_image(
                name=name,
                data=event_value,
                step=step,
                timestamp=timestamp,
                dataformats="CHW",
            )

    @client_handler(check_no_op=True, can_log_events=True)
    def log_video(
        self,
        data,
        name: Optional[str] = None,
        fps: int = 4,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        content_type: Optional[str] = None,
    ):
        """Logs a video.

        ```python
        >>> log_video("path/to/my_video1"),
        >>> log_video(
        >>>     name="my_vide2",
        >>>     data=np.arange(np.prod((4, 3, 1, 8, 8)), dtype=float).reshape((4, 3, 1, 8, 8))
        >>> )
        ```

        Args:
            data: video data or str.
            name: str, optional, if data is a filepath the name will be the name of the file
            fps: int, optional, frames per second
            step: int, optional
            timestamp: datetime, optional
            content_type: str, optional, default "gif"
        """
        self._log_has_events()

        is_file = isinstance(data, str) and os.path.exists(data)
        content_type = content_type or "gif"
        if is_file:
            name = name or get_base_filename(data)
            content_type = get_path_extension(filepath=data) or content_type
        else:
            name = name or "video"
        name = self._sanitize_filename(name)

        asset_path = get_asset_path(
            run_path=self._artifacts_path,
            kind=V1ArtifactKind.VIDEO,
            name=name,
            step=step,
            ext=content_type,
        )
        asset_rel_path = os.path.relpath(asset_path, self._artifacts_path)
        if is_file:
            event_value = events_processors.video_path(
                from_path=data,
                asset_path=asset_path,
                content_type=content_type,
                asset_rel_path=asset_rel_path,
            )
        else:
            event_value = events_processors.video(
                asset_path=asset_path,
                tensor=data,
                fps=fps,
                content_type=content_type,
                asset_rel_path=asset_rel_path,
            )

        if isinstance(event_value, str) and event_value == UNKNOWN:
            return

        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.VIDEO,
            event=V1Event.make(timestamp=timestamp, step=step, video=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_audio(
        self,
        data,
        name: Optional[str] = None,
        sample_rate: int = 44100,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        content_type: Optional[str] = None,
    ):
        """Logs a audio.

        ```python
        >>> log_audio("path/to/my_audio1"),
        >>> log_audio(name="my_audio2", data=np.arange(np.prod((42,)), dtype=float).reshape((42,)))
        ```

        Args:
            data: str or audio data
            name: str, optional, if data is a filepath the name will be the name of the file
            sample_rate: int, optional, sample rate in Hz
            step: int, optional
            timestamp: datetime, optional
            content_type: str, optional, default "wav"
        """
        self._log_has_events()

        is_file = isinstance(data, str) and os.path.exists(data)
        ext = content_type or "wav"
        if is_file:
            name = name or get_base_filename(data)
            ext = get_path_extension(filepath=data) or ext
        else:
            name = name or "audio"
        name = self._sanitize_filename(name)

        asset_path = get_asset_path(
            run_path=self._artifacts_path,
            kind=V1ArtifactKind.AUDIO,
            name=name,
            step=step,
            ext=ext,
        )
        asset_rel_path = os.path.relpath(asset_path, self._artifacts_path)

        if is_file:
            event_value = events_processors.audio_path(
                from_path=data,
                asset_path=asset_path,
                content_type=content_type,
                asset_rel_path=asset_rel_path,
            )
        else:
            event_value = events_processors.audio(
                asset_path=asset_path,
                tensor=data,
                sample_rate=sample_rate,
                asset_rel_path=asset_rel_path,
            )

        if isinstance(event_value, str) and event_value == UNKNOWN:
            return

        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.AUDIO,
            event=V1Event.make(timestamp=timestamp, step=step, audio=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_text(
        self,
        name: str,
        text: str,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a text.

        ```python
        >>> log_text(name="text", text="value")
        ```

        Args:
            name: str, name
            text: str, text value
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.TEXT,
            event=V1Event.make(timestamp=timestamp, step=step, text=text),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_html(
        self,
        name: str,
        html: str,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs an html.

        ```python
        >>> log_html(name="text", html="<p>value</p>")
        ```

        Args:
            name: str, name
            html: str, text value
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.HTML,
            event=V1Event.make(timestamp=timestamp, step=step, html=html),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_np_histogram(
        self,
        name: str,
        values,
        counts,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a numpy histogram.

        ```python
        >>> values, counts = np.histogram(np.random.randint(255, size=(1000,)))
        >>> log_np_histogram(name="histo1", values=values, counts=counts, step=1)
        ```

        Args:
            name: str, name
            values: np.array
            counts: np.array
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        event_value = events_processors.np_histogram(values=values, counts=counts)

        if isinstance(event_value, str) and event_value == UNKNOWN:
            return

        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.HISTOGRAM,
            event=V1Event.make(timestamp=timestamp, step=step, histogram=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_histogram(
        self,
        name: str,
        values,
        bins,
        max_bins=None,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a histogram.

        ```python
        >>> log_histogram(
        >>>     name="histo",
        >>>     values=np.arange(np.prod((1024,)), dtype=float).reshape((1024,)),
        >>>     bins="auto",
        >>>     step=1
        >>> )
        ```

        Args:
            name: str, name
            values: np.array
            bins: int or str
            max_bins: int, optional
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        event_value = events_processors.histogram(
            values=values, bins=bins, max_bins=max_bins
        )

        if isinstance(event_value, str) and event_value == UNKNOWN:
            return

        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.HISTOGRAM,
            event=V1Event.make(timestamp=timestamp, step=step, histogram=event_value),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_model(
        self,
        path: str,
        name: Optional[str] = None,
        framework: Optional[str] = None,
        summary: Optional[Dict] = None,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        rel_path: Optional[str] = None,
        skip_hash_calculation: bool = False,
        **kwargs,
    ):
        """Logs a model or a versioned model if a step value is provided.

        This method will:
         * save the model
         * several versions of the model and create an event file if the step is provided.

        > **Note 1**: This method does a couple of things:
        >  * It moves the model under the outputs or the assets directory if the step is provided
        >  * If the step is provided it creates an event file
        >  * It creates a lineage reference to the model or to the event file if the step is provided

        > **Note 2**: If you need to have more control over where the model should be saved and
        > only record a lineage information of that path you can use `log_model_ref`.

        Args:
            path: str, path to the model to log.
            name: str, name to give to the model.
            framework: str, optional ,name of the framework.
            summary: Dict, optional, key, value information about the model.
            step: int, optional
            timestamp: datetime, optional
            rel_path: str, relative path where to store the model.
            skip_hash_calculation: optional, flag to instruct the client to skip hash calculation.
        """
        if kwargs:
            logger.warning(
                "`log_model` received a deprecated or an unexpected parameters"
            )
        name = name or get_base_filename(path)
        name = self._sanitize_filename(name)
        ext = None
        if os.path.isfile(path):
            ext = get_path_extension(filepath=path)

        if step is not None:
            self._log_has_model()
            asset_path = get_asset_path(
                run_path=self._artifacts_path,
                kind=V1ArtifactKind.MODEL,
                name=name,
                step=step,
                ext=ext,
            )
            asset_rel_path = os.path.relpath(asset_path, self._artifacts_path)
            model = events_processors.model_path(
                from_path=path,
                asset_path=asset_path,
                framework=framework,
                spec=summary,
                asset_rel_path=asset_rel_path,
            )
            logged_event = LoggedEventSpec(
                name=name,
                kind=V1ArtifactKind.MODEL,
                event=V1Event.make(timestamp=timestamp, step=step, model=model),
            )
            self._add_event(logged_event)
        else:
            asset_path = self.get_outputs_path(rel_path, is_dir=True)
            asset_path = copy_file_or_dir_path(path, asset_path, True)
            asset_rel_path = os.path.relpath(asset_path, self._artifacts_path)
            self.log_model_ref(
                path=asset_path,
                name=name,
                framework=framework,
                summary=summary,
                rel_path=asset_rel_path,
                skip_hash_calculation=skip_hash_calculation,
            )

    @client_handler(check_no_op=True, can_log_events=True)
    def log_artifact(
        self,
        path: str,
        name: Optional[str] = None,
        kind: Optional[str] = None,
        summary: Optional[Dict] = None,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        rel_path: Optional[str] = None,
        skip_hash_calculation: bool = False,
        **kwargs,
    ):
        """Logs a generic artifact or a versioned generic artifact if a step value is provided.

        This method will:
         * save the artifact
         * several versions of the artifact and create an event file if the step is provided.

        > **Note 1**: This method does a couple things:
        >  * It moves the artifact under the outputs or the assets directory if the step is provided
        >  * If the step is provided it creates an event file
        >  * It creates a lineage reference to the artifact or to the event file if the step is provided

        > **Note 2**: If you need to have more control over where the artifact should be saved and
        > only record a lineage information of that path you can use `log_artifact_ref`.

        Args:
            path: str, path to the artifact.
            name: str, optional, if not provided the name of the file will be used.
            kind: optional, str
            summary: Dict, optional,
                 additional summary information to log about data in the lineage table.
            step: int, optional
            timestamp: datetime, optional
            rel_path: str, relative path where to store the artifacts.
            skip_hash_calculation: optional, flag to instruct the client to skip hash calculation
        """
        if kwargs:
            logger.warning(
                "`log_artifact` received a deprecated or an unexpected parameters"
            )
        name = name or get_base_filename(path)
        name = self._sanitize_filename(name)
        ext = get_path_extension(filepath=path)
        kind = kind or kwargs.get("artifact_kind")  # Backwards compatibility
        kind = kind or V1ArtifactKind.FILE

        if step is not None:
            self._log_has_events()
            asset_path = get_asset_path(
                run_path=self._artifacts_path,
                kind=kind,
                name=name,
                step=step,
                ext=ext,
            )
            asset_rel_path = os.path.relpath(asset_path, self._artifacts_path)

            artifact = events_processors.artifact_path(
                from_path=path,
                asset_path=asset_path,
                kind=kind,
                asset_rel_path=asset_rel_path,
            )
            logged_event = LoggedEventSpec(
                name=name,
                kind=kind,
                event=V1Event.make(timestamp=timestamp, step=step, artifact=artifact),
            )
            self._add_event(logged_event)
        else:
            asset_path = self.get_outputs_path(rel_path, is_dir=True)
            asset_path = copy_file_or_dir_path(path, asset_path, True)
            asset_rel_path = os.path.relpath(asset_path, self._artifacts_path)
            self.log_artifact_ref(
                path=asset_path,
                name=name,
                kind=kind,
                summary=summary,
                rel_path=asset_rel_path,
                skip_hash_calculation=skip_hash_calculation,
            )

    @client_handler(check_no_op=True, can_log_events=True)
    def log_dataframe(
        self,
        df,
        name: str,
        content_type: str = V1ArtifactKind.CSV,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a dataframe.

        Args:
            df: the dataframe to save
            name: str, optional, if not provided the name of the file will be used.
            content_type: str, optional, csv or html.
            step: int, optional
            timestamp: datetime, optional
        """
        self._log_has_events()

        name = self._sanitize_filename(name)
        asset_path = get_asset_path(
            run_path=self._artifacts_path,
            kind=V1ArtifactKind.DATAFRAME,
            name=name,
            step=step,
            ext=content_type,
        )
        asset_rel_path = os.path.relpath(asset_path, self._artifacts_path)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, name)
            path = "{}.{}".format(path, content_type)
            if content_type == V1ArtifactKind.CSV:
                df.to_csv(path)
            elif content_type == V1ArtifactKind.HTML:
                df.to_html(path)
            else:
                raise ValueError(
                    "The content_type `{}` is not supported "
                    "by the method log_dataframe. "
                    "This method supports `csv` or `html`.".format(content_type)
                )
            df = events_processors.dataframe_path(
                from_path=path,
                asset_path=asset_path,
                content_type=content_type,
                asset_rel_path=asset_rel_path,
            )
        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.DATAFRAME,
            event=V1Event.make(timestamp=timestamp, step=step, dataframe=df),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_plotly_chart(
        self,
        name: str,
        figure,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a plotly chart/figure.

        Args:
            name: str, name of the figure
            figure: plotly.figure
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        chart = events_processors.plotly_chart(figure=figure)
        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.CHART,
            event=V1Event.make(timestamp=timestamp, step=step, chart=chart),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_bokeh_chart(
        self,
        name: str,
        figure,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a bokeh chart/figure.

        Args:
            name: str, name of the figure
            figure: bokeh.figure
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        chart = events_processors.bokeh_chart(figure=figure)
        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.CHART,
            event=V1Event.make(timestamp=timestamp, step=step, chart=chart),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_altair_chart(
        self,
        name: str,
        figure,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Logs a vega/altair chart/figure.

        Args:
            name: str, name of the figure
            figure: figure
            step: int, optional
            timestamp: datetime, optional
        """
        name = self._sanitize_filename(name)
        self._log_has_events()

        chart = events_processors.altair_chart(figure=figure)
        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.CHART,
            event=V1Event.make(timestamp=timestamp, step=step, chart=chart),
        )
        self._add_event(logged_event)

    @client_handler(check_no_op=True, can_log_events=True)
    def log_mpl_plotly_chart(
        self,
        name: str,
        figure,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        close: bool = True,
        fallback_to_image: bool = True,
    ):
        """Logs a matplotlib figure to plotly figure.

        Args:
            name: str, name of the figure
            figure: figure
            step: int, optional
            timestamp: datetime, optional
            close: bool, optional, default True
            fallback_to_image: bool, optional, default True
        """

        def log_figure():
            self._log_has_events()

            chart = events_processors.mpl_plotly_chart(figure=figure, close=close)
            logged_event = LoggedEventSpec(
                name=self._sanitize_filename(name),
                kind=V1ArtifactKind.CHART,
                event=V1Event.make(timestamp=timestamp, step=step, chart=chart),
            )
            self._add_event(logged_event)

        try:
            log_figure()
        except Exception as e:
            if fallback_to_image:
                logger.warning("Could not convert figure to plotly. Error %s", e)
                self.log_mpl_image(
                    data=figure, name=name, step=step, timestamp=timestamp, close=close
                )
            else:
                raise e

    @client_handler(check_no_op=True, can_log_events=True)
    def log_trace(
        self,
        span: V1EventSpan,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        if not span:
            return
        name = span.name or "trace"
        name = self._sanitize_filename(name)
        self._log_has_traces()

        logged_event = LoggedEventSpec(
            name=name,
            kind=V1ArtifactKind.SPAN,
            event=V1Event.make(timestamp=timestamp, step=step, span=span),
        )
        self._add_event(logged_event)
        if span.inputs:
            self.log_inputs(**span.inputs)
        if span.outputs:
            self.log_outputs(**span.outputs)

    @client_handler(check_no_op=True)
    def get_log_level(self):
        return get_log_level()

    def end(self):
        """Manually end a run and trigger post done logic (artifacts and lineage collection)."""
        if self._exit_handler:
            atexit.unregister(self._exit_handler)
            self._exit_handler()

    def _register_exit_handler(self, func):
        self._exit_handler = func
        atexit.register(self._exit_handler)

    def _start(self):
        if self._is_offline:
            self.load_offline_run(path=self._artifacts_path, run_client=self)
            if self.run_data.status:
                logger.info(f"An offline run was found: {self._artifacts_path}")
            else:
                self.log_status(
                    V1Statuses.CREATED,
                    reason="OfflineOperation",
                    message="Operation is starting",
                )
                logger.info(f"A new offline run started: {self._artifacts_path}")
        if LifeCycle.is_pending(self.status):
            self.start()
        self._register_exit_handler(self._end)

        def excepthook(exception, value, tb):
            self.log_failed(
                reason="ExitHandler",
                message="An exception was raised during the run. "
                "Type: {}, Value: {}".format(exception, value),
            )
            # Resume normal work
            sys.__excepthook__(exception, value, tb)

        sys.excepthook = excepthook

    def _end(self):
        self.log_succeeded()
        end_log_processor()
        self._wait(sync_artifacts=True)
        if self._is_offline:
            self.persist_run(path=self._artifacts_path)

    def sync_artifacts_and_summaries(self):
        self.sync_events_summaries(
            last_check=None,
            events_path=ctx_paths.CONTEXTS_EVENTS_SUBPATH_FORMAT.format(
                self._artifacts_path
            ),
        )
        self.sync_system_events_summaries(
            last_check=None,
            events_path=ctx_paths.CONTEXTS_SYSTEM_RESOURCES_EVENTS_SUBPATH_FORMAT.format(
                self._artifacts_path
            ),
        )

    def _wait(self, sync_artifacts: bool = False):
        if self._event_logger:
            self._event_logger.close()
        if self._resource_logger:
            self._resource_logger.close()
        if self._logs_logger:
            self._logs_logger.close()
        if self._sidecar:
            self._sidecar.close()
        if self._results:
            self.log_outputs(**self._results)
        if sync_artifacts:
            self.sync_artifacts_and_summaries()

        time.sleep(settings.CLIENT_CONFIG.tracking_timeout)

    @client_handler(check_no_op=True, can_log_outputs=True)
    def log_env(self, rel_path: Optional[str] = None, content: Optional[Dict] = None):
        """Logs information about the environment.

        Called automatically if track_env is set to True.

        Can be called manually, and can accept a custom content as a form of a dictionary.

        Args:
            rel_path: str, optional, default "env.json".
            content: Dict, optional, default to current system information.
        """
        if not os.path.exists(self._outputs_path):
            return
        if not content:
            content = get_run_env(["polyaxon", "traceml"])

        rel_path = rel_path or "env.json"
        path = self._outputs_path
        if rel_path:
            path = os.path.join(path, rel_path)

        with open(os.path.join(path), "w") as env_file:
            env_file.write(orjson_dumps(content))
        set_permissions(path)

        self.log_artifact_ref(
            path=path,
            name="env",
            kind=V1ArtifactKind.ENV,
            summary={"path": path, "hash": hash_value(content)},
            is_input=False,
        )
