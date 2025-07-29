import os

from typing import TYPE_CHECKING, Any, Optional

from traceml import tracking
from traceml.exceptions import TracemlException
from traceml.logger import logger

summary_pb2 = None

try:
    from tensorflow.core.framework import summary_pb2  # noqa
except ImportError:
    pass
try:
    from tensorboardX.proto import summary_pb2  # noqa
except ImportError:
    pass

try:
    from tensorboard.compat.proto import summary_pb2  # noqa
except ImportError:
    pass

if not summary_pb2:
    raise TracemlException(
        "tensorflow/tensorboard/tensorboardx is required to use the tracking Logger"
    )


if TYPE_CHECKING:
    from traceml.tracking import Run


class Logger:
    @classmethod
    def process_summary(
        cls,
        summary: Any,
        global_step: Optional[int] = None,
        run: "Run" = None,
        log_image: bool = False,
        log_histo: bool = False,
        log_tensor: bool = False,
    ):
        run = tracking.get_or_create_run(run)
        if not run:
            return

        if isinstance(summary, bytes):
            summary_proto = summary_pb2.Summary()
            summary_proto.ParseFromString(summary)
            summary = summary_proto

        step = cls._process_step(global_step)
        for value in summary.value:
            try:
                cls.add_value(
                    run=run,
                    step=step,
                    value=value,
                    log_image=log_image,
                    log_histo=log_histo,
                    log_tensor=log_tensor,
                )
            except TracemlException("Polyaxon failed processing tensorboard summary."):
                pass

    @classmethod
    def add_value(
        cls,
        run,
        step,
        value,
        log_image: bool = False,
        log_histo: bool = False,
        log_tensor: bool = False,
    ):
        field = value.WhichOneof("value")

        if field == "simple_value":
            run.log_metric(name=value.tag, step=step, value=value.simple_value)
            return

        if field == "image" and log_image:
            run.log_image(name=value.tag, step=step, data=value.image)
            return

        if (
            field == "tensor"
            and log_tensor
            and value.tensor.string_val
            and len(value.tensor.string_val)
        ):
            string_values = []
            for _ in range(0, len(value.tensor.string_val)):
                string_value = value.tensor.string_val.pop()
                string_values.append(string_value.decode("utf-8"))

                run.log_text(name=value.tag, step=step, text=", ".join(string_values))
            return

        elif field == "histo" and log_histo:
            if len(value.histo.bucket_limit) >= 3:
                first = (
                    value.histo.bucket_limit[0]
                    + value.histo.bucket_limit[0]
                    - value.histo.bucket_limit[1]
                )
                last = (
                    value.histo.bucket_limit[-2]
                    + value.histo.bucket_limit[-2]
                    - value.histo.bucket_limit[-3]
                )
                values, counts = (
                    list(value.histo.bucket),
                    [first] + value.histo.bucket_limit[:-1] + [last],
                )
                try:
                    run.log_np_histogram(
                        name=value.tag, values=values, counts=counts, step=step
                    )
                    return
                except ValueError:
                    logger.warning(
                        "Ignoring histogram for tag `{}`, "
                        "Histograms must have few bins".format(value.tag)
                    )
            else:
                logger.warning(
                    "Ignoring histogram for tag `{}`, "
                    "Found a histogram with only 2 bins.".format(value.tag)
                )

    @staticmethod
    def get_writer_name(log_dir):
        return os.path.basename(os.path.normpath(log_dir))

    @staticmethod
    def _process_step(global_step):
        return int(global_step) if global_step is not None else None
