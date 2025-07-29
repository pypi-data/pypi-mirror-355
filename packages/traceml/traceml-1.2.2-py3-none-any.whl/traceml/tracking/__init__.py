from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Union

from polyaxon._client.run import RunClient
from polyaxon._sdk.schemas import V1Run
from traceml.artifacts import V1ArtifactKind, V1RunArtifact
from traceml.tracking.run import Run

TRACKING_RUN: Run = None


def init(
    owner: Optional[str] = None,
    project: Optional[str] = None,
    run_uuid: Optional[str] = None,
    client: RunClient = None,
    track_code: bool = True,
    track_env: bool = True,
    track_logs: bool = True,
    refresh_data: bool = False,
    artifacts_path: Optional[str] = None,
    collect_artifacts: Optional[str] = None,
    collect_resources: Optional[str] = None,
    is_offline: Optional[bool] = None,
    is_new: Optional[bool] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[Run]:
    """Tracking module is similar to the tracking client without the need to create a run instance.

    The tracking module allows you to call all tracking methods directly from the top level module.

    This could be very convenient especially if you are running in-cluster experiments:

    ```python
    from polyaxon import tracking

    tracking.init()
    ...
    tracking.log_metrics(step=1, loss=0.09, accuracy=0.75)
    ...
    tracking.log_metrics(step=1, loss=0.02, accuracy=0.85)
    ...
    ```

    > A global `TRACKING_RUN` will be set on the module.


        Args:
            owner: str, optional, the owner is the username or
                 the organization name owning this project.
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
            refresh_data: bool, optional, default False, to instruct the run to resume,
                 only useful when the run is not managed by Polyaxon.
            artifacts_path: str, optional, for in-cluster runs it will be set automatically.
            collect_artifacts: bool, optional,
                 similar to the env var flag `POLYAXON_COLLECT_ARTIFACTS`, this env var is `True`
                 by default for managed runs and is controlled by the plugins section.
            collect_resources: bool, optional,
                 similar to the env var flag `POLYAXON_COLLECT_RESOURCES`, this env var is `True`
                 by default for managed runs and is controlled by the plugins section.
            is_offline: bool, optional,
                 To trigger the offline mode manually instead of depending on `POLYAXON_IS_OFFLINE`.
            is_new: bool, optional,
                 Force the creation of a new run instead of trying to discover a cached run or
                 refreshing an instance from the env var
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
    global TRACKING_RUN

    TRACKING_RUN = Run(
        owner=owner,
        project=project,
        run_uuid=run_uuid,
        client=client,
        track_code=track_code,
        refresh_data=refresh_data,
        track_env=track_env,
        track_logs=track_logs,
        artifacts_path=artifacts_path,
        collect_artifacts=collect_artifacts,
        collect_resources=collect_resources,
        is_offline=is_offline,
        is_new=is_new,
        name=name,
        description=description,
        tags=tags,
    )
    return TRACKING_RUN


def get_or_create_run(tracking_run: Run = None) -> Optional[Run]:
    """Get or create a new tracking run.

    It tries to create a new instance, for in-cluster runs, this will work automatically.

    This is used inside some Polyaxon callbacks, you should use `init` instead.
    """
    global TRACKING_RUN

    if tracking_run:
        return tracking_run
    if TRACKING_RUN:
        return TRACKING_RUN

    init()
    return TRACKING_RUN


def update(data: Union[Dict, V1Run], async_req: bool = False):
    global TRACKING_RUN
    TRACKING_RUN.update(data=data, async_req=async_req)


update.__doc__ = Run.update.__doc__


def get_connections_catalog():
    global TRACKING_RUN
    return TRACKING_RUN.get_connections_catalog()


get_connections_catalog.__doc__ = Run.get_connections_catalog.__doc__


def get_artifacts_store_connection():
    global TRACKING_RUN
    return TRACKING_RUN.get_artifacts_store_connection()


get_artifacts_store_connection.__doc__ = Run.get_artifacts_store_connection.__doc__


def get_artifacts_path(
    rel_path: Optional[str] = None,
    ensure_path: bool = False,
    is_dir: bool = False,
    use_store_path: bool = False,
):
    global TRACKING_RUN
    return TRACKING_RUN.get_artifacts_path(
        rel_path=rel_path,
        ensure_path=ensure_path,
        is_dir=is_dir,
        use_store_path=use_store_path,
    )


get_artifacts_path.__doc__ = Run.get_artifacts_path.__doc__


def get_outputs_path(
    rel_path: Optional[str] = None,
    ensure_path: bool = True,
    is_dir: bool = False,
    use_store_path: bool = False,
):
    global TRACKING_RUN
    return TRACKING_RUN.get_outputs_path(
        rel_path=rel_path,
        ensure_path=ensure_path,
        is_dir=is_dir,
        use_store_path=use_store_path,
    )


get_outputs_path.__doc__ = Run.get_outputs_path.__doc__


def get_tensorboard_path(
    rel_path: str = "tensorboard",
    use_store_path: bool = False,
):
    global TRACKING_RUN
    return TRACKING_RUN.get_tensorboard_path(
        rel_path=rel_path, use_store_path=use_store_path
    )


get_tensorboard_path.__doc__ = Run.get_tensorboard_path.__doc__


def set_artifacts_path(artifacts_path: str, is_related: bool = False):
    global TRACKING_RUN
    TRACKING_RUN.set_artifacts_path(artifacts_path, is_related)


set_artifacts_path.__doc__ = Run.set_artifacts_path.__doc__


def set_run_event_logger():
    global TRACKING_RUN
    TRACKING_RUN.set_run_event_logger()


set_run_event_logger.__doc__ = Run.set_run_event_logger.__doc__


def set_run_resource_logger():
    global TRACKING_RUN
    TRACKING_RUN.set_run_resource_logger()


set_run_resource_logger.__doc__ = Run.set_run_resource_logger.__doc__


def set_run_process_sidecar():
    global TRACKING_RUN
    TRACKING_RUN.set_run_process_sidecar()


set_run_process_sidecar.__doc__ = Run.set_run_process_sidecar.__doc__


def log_metric(
    name: str,
    value: float,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_metric(
        name=name,
        value=value,
        step=step,
        timestamp=timestamp,
    )


log_metric.__doc__ = Run.log_metric.__doc__


def log_metrics(
    step: Optional[int] = None, timestamp: Optional[datetime] = None, **metrics
):
    global TRACKING_RUN
    TRACKING_RUN.log_metrics(step=step, timestamp=timestamp, **metrics)


log_metrics.__doc__ = Run.log_metrics.__doc__


def log_roc_auc_curve(
    name: str,
    fpr,
    tpr,
    auc: float = None,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_roc_auc_curve(
        name=name,
        fpr=fpr,
        tpr=tpr,
        auc=auc,
        step=step,
        timestamp=timestamp,
    )


log_roc_auc_curve.__doc__ = Run.log_roc_auc_curve.__doc__


def log_sklearn_roc_auc_curve(
    name: str,
    y_preds,
    y_targets,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    is_multi_class: bool = False,
):
    global TRACKING_RUN
    TRACKING_RUN.log_sklearn_roc_auc_curve(
        name=name,
        y_preds=y_preds,
        y_targets=y_targets,
        step=step,
        timestamp=timestamp,
        is_multi_class=is_multi_class,
    )


log_sklearn_roc_auc_curve.__doc__ = Run.log_sklearn_roc_auc_curve.__doc__


def log_pr_curve(
    name: str,
    precision,
    recall,
    average_precision=None,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_pr_curve(
        name=name,
        precision=precision,
        recall=recall,
        average_precision=average_precision,
        step=step,
        timestamp=timestamp,
    )


log_pr_curve.__doc__ = Run.log_pr_curve.__doc__


def log_sklearn_pr_curve(
    name: str,
    y_preds,
    y_targets,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    is_multi_class: bool = False,
):
    global TRACKING_RUN
    TRACKING_RUN.log_sklearn_pr_curve(
        name=name,
        y_preds=y_preds,
        y_targets=y_targets,
        step=step,
        timestamp=timestamp,
        is_multi_class=is_multi_class,
    )


log_sklearn_pr_curve.__doc__ = Run.log_sklearn_pr_curve.__doc__


def log_curve(
    name: str,
    x,
    y,
    annotation: Optional[str] = None,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_curve(
        name=name,
        x=x,
        y=y,
        annotation=annotation,
        step=step,
        timestamp=timestamp,
    )


log_curve.__doc__ = Run.log_curve.__doc__


def log_confusion_matrix(
    name: str,
    x,
    y,
    z=None,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_confusion_matrix(
        name=name,
        x=x,
        y=y,
        z=z,
        step=step,
        timestamp=timestamp,
    )


log_confusion_matrix.__doc__ = Run.log_confusion_matrix.__doc__


def log_image(
    data: Any,
    name: Optional[str] = None,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    rescale=1,
    dataformats: str = "CHW",
    ext: Optional[str] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_image(
        data=data,
        name=name,
        step=step,
        timestamp=timestamp,
        rescale=rescale,
        dataformats=dataformats,
        ext=ext,
    )


log_image.__doc__ = Run.log_image.__doc__


def log_image_with_boxes(
    tensor_image,
    tensor_boxes,
    name: Optional[str] = None,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    rescale: int = 1,
    dataformats: str = "CHW",
):
    global TRACKING_RUN
    TRACKING_RUN.log_image_with_boxes(
        tensor_image=tensor_image,
        tensor_boxes=tensor_boxes,
        name=name,
        step=step,
        timestamp=timestamp,
        rescale=rescale,
        dataformats=dataformats,
    )


log_image_with_boxes.__doc__ = Run.log_image_with_boxes.__doc__


def log_mpl_image(
    data,
    name: Optional[str] = None,
    close: bool = True,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_mpl_image(
        data=data,
        name=name,
        close=close,
        step=step,
        timestamp=timestamp,
    )


log_mpl_image.__doc__ = Run.log_mpl_image.__doc__


def log_video(
    data,
    name: Optional[str] = None,
    fps: int = 4,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    content_type: Optional[str] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_video(
        data=data,
        name=name,
        fps=fps,
        step=step,
        timestamp=timestamp,
        content_type=content_type,
    )


log_video.__doc__ = Run.log_video.__doc__


def log_audio(
    data,
    name: Optional[str] = None,
    sample_rate: int = 44100,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    content_type: Optional[str] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_audio(
        data=data,
        name=name,
        sample_rate=sample_rate,
        step=step,
        timestamp=timestamp,
        content_type=content_type,
    )


log_audio.__doc__ = Run.log_audio.__doc__


def log_text(
    name: str,
    text: str,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_text(
        name=name,
        text=text,
        step=step,
        timestamp=timestamp,
    )


log_text.__doc__ = Run.log_text.__doc__


def log_html(
    name: str,
    html: str,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_html(
        name=name,
        html=html,
        step=step,
        timestamp=timestamp,
    )


log_html.__doc__ = Run.log_html.__doc__


def log_np_histogram(
    name: str,
    values,
    counts,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_np_histogram(
        name=name,
        values=values,
        counts=counts,
        step=step,
        timestamp=timestamp,
    )


log_np_histogram.__doc__ = Run.log_np_histogram.__doc__


def log_histogram(
    name: str,
    values,
    bins,
    max_bins=None,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_histogram(
        name=name,
        values=values,
        bins=bins,
        max_bins=max_bins,
        step=step,
        timestamp=timestamp,
    )


log_histogram.__doc__ = Run.log_histogram.__doc__


def log_model(
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
    global TRACKING_RUN
    TRACKING_RUN.log_model(
        path=path,
        name=name,
        framework=framework,
        summary=summary,
        step=step,
        timestamp=timestamp,
        rel_path=rel_path,
        skip_hash_calculation=skip_hash_calculation,
        **kwargs,
    )


log_model.__doc__ = Run.log_model.__doc__


def log_artifact(
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
    global TRACKING_RUN
    TRACKING_RUN.log_artifact(
        path=path,
        name=name,
        kind=kind,
        summary=summary,
        step=step,
        timestamp=timestamp,
        rel_path=rel_path,
        skip_hash_calculation=skip_hash_calculation,
        **kwargs,
    )


log_artifact.__doc__ = Run.log_artifact.__doc__


def log_dataframe(
    df,
    name: str,
    content_type: str = V1ArtifactKind.CSV,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_dataframe(
        df=df,
        name=name,
        content_type=content_type,
        step=step,
        timestamp=timestamp,
    )


log_dataframe.__doc__ = Run.log_dataframe.__doc__


def log_plotly_chart(
    name: str, figure, step: Optional[int] = None, timestamp: Optional[datetime] = None
):
    global TRACKING_RUN
    TRACKING_RUN.log_plotly_chart(
        name=name,
        figure=figure,
        step=step,
        timestamp=timestamp,
    )


log_plotly_chart.__doc__ = Run.log_plotly_chart.__doc__


def log_bokeh_chart(
    name: str, figure, step: Optional[int] = None, timestamp: Optional[datetime] = None
):
    global TRACKING_RUN
    TRACKING_RUN.log_bokeh_chart(
        name=name,
        figure=figure,
        step=step,
        timestamp=timestamp,
    )


log_bokeh_chart.__doc__ = Run.log_bokeh_chart.__doc__


def log_altair_chart(
    name: str, figure, step: Optional[int] = None, timestamp: Optional[datetime] = None
):
    global TRACKING_RUN
    TRACKING_RUN.log_altair_chart(
        name=name,
        figure=figure,
        step=step,
        timestamp=timestamp,
    )


log_altair_chart.__doc__ = Run.log_altair_chart.__doc__


def log_mpl_plotly_chart(
    name: str,
    figure,
    step: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    close: bool = True,
    fallback_to_image: bool = True,
):
    global TRACKING_RUN
    TRACKING_RUN.log_mpl_plotly_chart(
        name=name,
        figure=figure,
        step=step,
        timestamp=timestamp,
        close=close,
        fallback_to_image=fallback_to_image,
    )


log_mpl_plotly_chart.__doc__ = Run.log_mpl_plotly_chart.__doc__


def get_log_level():
    global TRACKING_RUN
    return TRACKING_RUN.get_log_level()


get_log_level.__doc__ = Run.get_log_level.__doc__


def set_readme(readme: str, async_req: bool = True):
    global TRACKING_RUN
    TRACKING_RUN.set_readme(readme=readme, async_req=async_req)


set_readme.__doc__ = Run.set_readme.__doc__


def set_description(description: str, async_req: bool = True):
    global TRACKING_RUN
    TRACKING_RUN.set_description(description=description, async_req=async_req)


set_description.__doc__ = Run.set_description.__doc__


def set_name(name: str, async_req: bool = True):
    global TRACKING_RUN
    TRACKING_RUN.set_name(name=name, async_req=async_req)


set_name.__doc__ = Run.set_name.__doc__


def end():
    global TRACKING_RUN
    TRACKING_RUN.end()


end.__doc__ = Run.end.__doc__


def log_status(
    status: str,
    reason: Optional[str] = None,
    message: Optional[str] = None,
    last_transition_time: Optional[datetime] = None,
    last_update_time: Optional[datetime] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_status(
        status=status,
        reason=reason,
        message=message,
        last_transition_time=last_transition_time,
        last_update_time=last_update_time,
    )


log_status.__doc__ = Run.log_status.__doc__


def log_inputs(reset: bool = False, async_req: bool = True, **inputs):
    global TRACKING_RUN
    TRACKING_RUN.log_inputs(reset=reset, async_req=async_req, **inputs)


log_inputs.__doc__ = Run.log_inputs.__doc__


def log_outputs(reset: bool = False, async_req: bool = True, **outputs):
    global TRACKING_RUN
    TRACKING_RUN.log_outputs(reset=reset, async_req=async_req, **outputs)


log_outputs.__doc__ = Run.log_outputs.__doc__


def log_tags(
    tags: Union[str, Sequence[str]],
    reset: bool = False,
    async_req: bool = True,
):
    global TRACKING_RUN
    TRACKING_RUN.log_tags(tags=tags, reset=reset, async_req=async_req)


log_tags.__doc__ = Run.log_tags.__doc__


def log_meta(reset: bool = False, async_req: bool = True, **meta):
    global TRACKING_RUN
    TRACKING_RUN.log_meta(reset=reset, async_req=async_req, **meta)


log_meta.__doc__ = Run.log_meta.__doc__


def log_progress(value: float):
    global TRACKING_RUN
    TRACKING_RUN.log_progress(value=value)


log_progress.__doc__ = Run.log_progress.__doc__


def log_succeeded(
    reason: Optional[str] = None,
    message: Optional[str] = "Operation has succeeded",
):
    global TRACKING_RUN
    TRACKING_RUN.log_succeeded(
        reason=reason,
        message=message,
    )


log_succeeded.__doc__ = Run.log_succeeded.__doc__


def log_stopped(
    reason: Optional[str] = None,
    message: Optional[str] = "Operation is stopped",
):
    global TRACKING_RUN
    TRACKING_RUN.log_stopped(
        reason=reason,
        message=message,
    )


log_stopped.__doc__ = Run.log_stopped.__doc__


def log_failed(reason: Optional[str] = None, message: Optional[str] = None):
    global TRACKING_RUN
    TRACKING_RUN.log_failed(reason=reason, message=message)


log_failed.__doc__ = Run.log_failed.__doc__


def log_artifact_ref(
    path: str,
    kind: V1ArtifactKind,
    name: Optional[str] = None,
    hash: Optional[str] = None,
    content=None,
    summary: Optional[Dict] = None,
    is_input: bool = False,
    rel_path: Optional[str] = None,
    skip_hash_calculation: bool = False,
):
    global TRACKING_RUN
    TRACKING_RUN.log_artifact_ref(
        path=path,
        kind=kind,
        name=name,
        hash=hash,
        content=content,
        summary=summary,
        is_input=is_input,
        rel_path=rel_path,
        skip_hash_calculation=skip_hash_calculation,
    )


log_artifact_ref.__doc__ = Run.log_artifact_ref.__doc__


def log_tensorboard_ref(
    path: str,
    name: str = "tensorboard",
    is_input: bool = False,
    rel_path: Optional[str] = None,
):
    global TRACKING_RUN
    TRACKING_RUN.log_tensorboard_ref(
        path=path,
        name=name,
        is_input=is_input,
        rel_path=rel_path,
    )


log_tensorboard_ref.__doc__ = Run.log_tensorboard_ref.__doc__


def log_model_ref(
    path: str,
    name: Optional[str] = None,
    framework: Optional[str] = None,
    summary: Optional[Dict] = None,
    is_input: bool = False,
    rel_path: Optional[str] = None,
    skip_hash_calculation: bool = False,
):
    global TRACKING_RUN
    TRACKING_RUN.log_model_ref(
        path=path,
        name=name,
        framework=framework,
        summary=summary,
        is_input=is_input,
        rel_path=rel_path,
        skip_hash_calculation=skip_hash_calculation,
    )


log_model_ref.__doc__ = Run.log_model_ref.__doc__


def log_code_ref(code_ref: Optional[Dict] = None, is_input: bool = True):
    global TRACKING_RUN
    TRACKING_RUN.log_code_ref(code_ref=code_ref, is_input=is_input)


log_code_ref.__doc__ = Run.log_code_ref.__doc__


def log_data_ref(
    name: str,
    hash: Optional[str] = None,
    path: Optional[str] = None,
    content=None,
    summary: Optional[Dict] = None,
    is_input: bool = True,
    skip_hash_calculation: bool = False,
):
    global TRACKING_RUN
    TRACKING_RUN.log_data_ref(
        name=name,
        content=content,
        hash=hash,
        path=path,
        summary=summary,
        is_input=is_input,
        skip_hash_calculation=skip_hash_calculation,
    )


log_data_ref.__doc__ = Run.log_data_ref.__doc__


def log_file_ref(
    path: str,
    name: Optional[str] = None,
    hash: Optional[str] = None,
    content=None,
    summary: Optional[Dict] = None,
    is_input: bool = False,
    rel_path: Optional[str] = None,
    skip_hash_calculation: bool = False,
):
    global TRACKING_RUN
    TRACKING_RUN.log_file_ref(
        path=path,
        name=name,
        hash=hash,
        content=content,
        summary=summary,
        is_input=is_input,
        rel_path=rel_path,
        skip_hash_calculation=skip_hash_calculation,
    )


log_file_ref.__doc__ = Run.log_file_ref.__doc__


def log_dir_ref(
    path: str,
    name: Optional[str] = None,
    hash: Optional[str] = None,
    summary: Optional[Dict] = None,
    is_input: bool = False,
    rel_path: Optional[str] = None,
    skip_hash_calculation: bool = False,
):
    global TRACKING_RUN
    TRACKING_RUN.log_dir_ref(
        path=path,
        name=name,
        hash=hash,
        summary=summary,
        is_input=is_input,
        rel_path=rel_path,
        skip_hash_calculation=skip_hash_calculation,
    )


log_dir_ref.__doc__ = Run.log_dir_ref.__doc__


def log_artifact_lineage(body: List[V1RunArtifact]):
    global TRACKING_RUN
    TRACKING_RUN.log_artifact_lineage(body)


log_artifact_lineage.__doc__ = Run.log_artifact_lineage.__doc__


def log_env(rel_path: Optional[str] = None, content: Optional[Dict] = None):
    global TRACKING_RUN
    return TRACKING_RUN.log_env(rel_path=rel_path, content=content)


log_env.__doc__ = Run.log_env.__doc__


def sync_events_summaries(last_check: Optional[datetime], events_path: str):
    global TRACKING_RUN
    TRACKING_RUN.sync_events_summaries(last_check=last_check, events_path=events_path)


sync_events_summaries.__doc__ = Run.sync_events_summaries.__doc__


def sync_system_events_summaries(last_check: Optional[datetime], events_path: str):
    global TRACKING_RUN
    TRACKING_RUN.sync_system_events_summaries(
        last_check=last_check, events_path=events_path
    )


sync_system_events_summaries.__doc__ = Run.sync_system_events_summaries.__doc__


def pull_remote_run(
    path: Optional[str] = None,
    download_artifacts: bool = True,
):
    global TRACKING_RUN
    return TRACKING_RUN.pull_remote_run(
        path=path,
        download_artifacts=download_artifacts,
    )


pull_remote_run.__doc__ = Run.pull_remote_run.__doc__


def push_offline_run(
    path: str,
    upload_artifacts: bool = True,
    clean: bool = False,
):
    global TRACKING_RUN
    TRACKING_RUN.push_offline_run(
        path=path,
        upload_artifacts=upload_artifacts,
        clean=clean,
    )


push_offline_run.__doc__ = Run.push_offline_run.__doc__


def promote_to_model_version(
    version: str,
    description: Optional[str] = None,
    tags: Optional[Union[str, List[str]]] = None,
    content: Optional[Union[str, Dict]] = None,
    connection: Optional[str] = None,
    artifacts: Optional[List[str]] = None,
    force: bool = False,
):
    global TRACKING_RUN
    return TRACKING_RUN.promote_to_model_version(
        version=version,
        description=description,
        tags=tags,
        content=content,
        connection=connection,
        artifacts=artifacts,
        force=force,
    )


promote_to_model_version.__doc__ = Run.promote_to_model_version.__doc__


def promote_to_artifact_version(
    version: str,
    description: Optional[str] = None,
    tags: Optional[Union[str, List[str]]] = None,
    content: Optional[Union[str, Dict]] = None,
    connection: Optional[str] = None,
    artifacts: Optional[List[str]] = None,
    force: bool = False,
):
    global TRACKING_RUN
    return TRACKING_RUN.promote_to_artifact_version(
        version=version,
        description=description,
        tags=tags,
        content=content,
        connection=connection,
        artifacts=artifacts,
        force=force,
    )


promote_to_artifact_version.__doc__ = Run.promote_to_artifact_version.__doc__


__all__ = [
    "V1ArtifactKind",
    "V1RunArtifact",
    "Run",
    "init",
    "get_or_create_run",
    "update",
    "get_artifacts_path",
    "get_outputs_path",
    "get_tensorboard_path",
    "set_artifacts_path",
    "set_run_event_logger",
    "set_run_resource_logger",
    "set_run_process_sidecar",
    "log_metric",
    "log_metrics",
    "log_roc_auc_curve",
    "log_sklearn_roc_auc_curve",
    "log_pr_curve",
    "log_sklearn_pr_curve",
    "log_curve",
    "log_confusion_matrix",
    "log_image",
    "log_image_with_boxes",
    "log_mpl_image",
    "log_video",
    "log_audio",
    "log_text",
    "log_html",
    "log_np_histogram",
    "log_histogram",
    "log_model",
    "log_artifact",
    "log_dataframe",
    "log_plotly_chart",
    "log_bokeh_chart",
    "log_altair_chart",
    "log_mpl_plotly_chart",
    "get_log_level",
    "set_readme",
    "set_description",
    "set_name",
    "end",
    "log_status",
    "log_inputs",
    "log_outputs",
    "log_tags",
    "log_meta",
    "log_progress",
    "log_succeeded",
    "log_stopped",
    "log_failed",
    "log_artifact_ref",
    "log_tensorboard_ref",
    "log_model_ref",
    "log_code_ref",
    "log_data_ref",
    "log_file_ref",
    "log_dir_ref",
    "log_artifact_lineage",
    "log_env",
    "sync_events_summaries",
    "sync_system_events_summaries",
    "pull_remote_run",
    "push_offline_run",
    "promote_to_model_version",
    "promote_to_artifact_version",
]
