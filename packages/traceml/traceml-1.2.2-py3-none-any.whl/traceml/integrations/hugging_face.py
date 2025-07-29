from polyaxon._client.decorators import client_handler
from traceml import tracking
from traceml.exceptions import TracemlException
from traceml.logger import logger
from traceml.processors import events_processors

try:
    from transformers.trainer_callback import TrainerCallback
except ImportError:
    raise TracemlException("transformers is required to use the tracking Callback")


class Callback(TrainerCallback):
    def __init__(
        self,
        run=None,
    ):
        super().__init__()
        self.run = run

    def _log_model_summary(self, model):
        summary, filetype = events_processors.model_to_str(model)
        if not summary:
            return
        rel_path = self.run.get_outputs_path("model_summary.{}".format(filetype))
        with open(rel_path, "w") as f:
            f.write(summary)
        self.run.log_file_ref(path=rel_path, name="model_summary", is_input=False)

    @client_handler(check_no_op=True)
    def setup(self, args, state, model, **kwargs):
        self.run = tracking.get_or_create_run(kwargs.get("run"))
        if state.is_world_process_zero:
            self._log_model_summary(model)
            self.run.log_inputs(**args.to_sanitized_dict())

    @client_handler(check_no_op=True)
    def on_train_begin(self, args, state, control, model=None, **kwargs):
        if not self.run:
            self.setup(args, state, model)

    @client_handler(check_no_op=True)
    def on_log(self, args, state, control, logs, model=None, **kwargs):
        if not self.run:
            self.setup(args, state, model)
        if state.is_world_process_zero:
            metrics = {}
            for k, v in logs.items():
                if isinstance(v, (int, float)):
                    metrics[k] = v
                else:
                    logger.warning(
                        f"Trainer is attempting to log a value of "
                        f'"{v}" of type {type(v)} for key "{k}" as a metric. '
                        f"Polyaxon's log_metrics() only accepts float and "
                        f"int types so we dropped this attribute."
                    )
            self.run.log_metrics(**metrics, step=state.global_step)
