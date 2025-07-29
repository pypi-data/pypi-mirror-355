import operator

from typing import List, Optional

from clipped.utils.np import sanitize_np_types

from polyaxon._client.decorators import client_handler
from traceml import tracking
from traceml.exceptions import TracemlException
from traceml.logger import logger

try:
    from tensorflow import keras
except ImportError:
    try:
        import keras
    except ImportError:
        raise TracemlException("Keras is required to use the tracking Callback")


class Callback(keras.callbacks.Callback):
    @client_handler(check_no_op=True)
    def __init__(
        self,
        run=None,
        metrics: Optional[List[str]] = None,
        log_model: bool = True,
        save_weights_only: bool = False,
        log_best_prefix="best",
        mode: str = "auto",
        monitor: str = "val_loss",
        use_store_path: bool = False,
        model_ext: str = "",
    ):
        self.run = tracking.get_or_create_run(run)
        self.metrics = metrics
        self.log_model = log_model
        self.filepath = self.run.get_outputs_path(
            "model{}".format(model_ext), use_store_path=use_store_path
        )
        self.log_best_prefix = log_best_prefix
        self.best = None
        self.current = None
        self.monitor = monitor
        self.save_weights_only = save_weights_only

        # From Keras
        if mode not in ["auto", "min", "max"]:
            print(
                "PolyaxonCallback mode %s is unknown, " "fallback to auto mode." % mode
            )
            mode = "auto"

        if mode == "min":
            self.monitor_op = operator.lt
            self.best = float("inf")
        elif mode == "max":
            self.monitor_op = operator.gt
            self.best = float("-inf")
        else:
            if "acc" in self.monitor or self.monitor.startswith("fmeasure"):
                self.monitor_op = operator.gt
                self.best = float("-inf")
            else:
                self.monitor_op = operator.lt
                self.best = float("inf")
        # Get the previous best metric for resumed runs
        previous_best = (self.run.get_inputs() or {}).get(
            "{}_{}".format(self.log_best_prefix, self.monitor)
        )
        if previous_best is not None:
            self.best = previous_best

    @client_handler(check_no_op=True)
    def on_train_begin(self, logs=None):  # pylint: disable=unused-argument
        if not self.run:
            return

        params = {}

        try:
            params["num_layers"] = len(self.model.layers)
        except Exception:  # noqa
            pass

        try:
            params["optimizer_name"] = type(self.model.optimizer).__name__
        except Exception:  # noqa
            pass

        try:
            if hasattr(self.model.optimizer, "lr"):
                params["optimizer_lr"] = sanitize_np_types(
                    self.model.optimizer.lr
                    if type(self.model.optimizer.lr) is float
                    else keras.backend.eval(self.model.optimizer.lr)
                )
        except Exception:  # noqa
            pass

        try:
            if hasattr(self.model.optimizer, "epsilon"):
                params["optimizer_epsilon"] = sanitize_np_types(
                    self.model.optimizer.epsilon
                    if type(self.model.optimizer.epsilon) is float
                    else keras.backend.eval(self.model.optimizer.epsilon)
                )
        except Exception:  # noqa
            pass

        if params:
            self.run.log_inputs(**params)

        try:
            sum_list = []
            self.model.summary(print_fn=sum_list.append)
            summary = "\n".join(sum_list)
            rel_path = self.run.get_outputs_path("model_summary.txt")
            with open(rel_path, "w") as f:
                f.write(summary)
            self.run.log_file_ref(path=rel_path, name="model_summary", is_input=False)
        except Exception:  # noqa
            pass

    @client_handler(check_no_op=True)
    def on_epoch_end(self, epoch, logs=None):
        if not logs or not self.run:
            return

        if self.metrics:
            metrics = {
                metric: logs[metric] for metric in self.metrics if metric in logs
            }
        else:
            metrics = logs  # Log all metrics

        self.current = logs.get(self.monitor)
        if self.current and self.monitor_op(self.current, self.best):
            if self.log_best_prefix:
                metrics[f"{self.log_best_prefix}_{self.monitor}"] = self.current
                metrics[f"{self.log_best_prefix}_epoch"] = epoch
            if self.log_model:
                self._log_model()
            self.best = self.current

        self.run.log_metrics(step=epoch, **metrics)

    @client_handler(check_no_op=True)
    def on_train_end(self, logs=None):  # pylint: disable=unused-argument
        if not self.log_model:
            return

        if self.run._has_meta_key("has_model"):  # noqa
            # Best model was already saved
            return

        self._log_model()

    @client_handler(check_no_op=True)
    def _log_model(self):
        try:
            if self.save_weights_only:
                self.model.save_weights(self.filepath, overwrite=True)
            else:
                self.model.save(self.filepath, overwrite=True)
            if not self.run._has_meta_key("has_model"):  # noqa
                self.run.log_model_ref(self.filepath, name="model", framework="keras")
        # `RuntimeError: Unable to create link` in TF 1.13.1
        # also saw `TypeError: can't pickle _thread.RLock objects`
        except (ImportError, RuntimeError, TypeError) as e:
            logger.warning("Can't save model, h5py returned error: %s" % e)
            self.log_model = False
