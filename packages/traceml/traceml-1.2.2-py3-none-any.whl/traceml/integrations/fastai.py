from polyaxon._client.decorators import client_handler
from traceml import tracking
from traceml.exceptions import TracemlException

try:
    from fastai.basics import *
    from fastai.learner import Callback as baseCallback
    from fastai.vision.all import *
except ImportError:
    raise TracemlException("Fastai is required to use the tracking Callback")


class Callback(baseCallback):
    @client_handler(check_no_op=True)
    def __init__(self, log_model=False, run=None):
        self.log_model = log_model
        self.plx_run = tracking.get_or_create_run(run)
        self._plx_step = 0

    @client_handler(check_no_op=True)
    def before_fit(self):
        if not self.plx_run:
            return
        try:
            self.plx_run.log_inputs(
                n_epoch=str(self.learn.n_epoch),
                model_class=str(type(self.learn.model.__name__)),
            )
        except Exception:  # noqa
            print("Did not log all properties to Polyaxon.")

        try:
            model_summary_path = self.plx_run.get_outputs_path("model_summary.txt")
            with open(model_summary_path, "w") as g:
                g.write(repr(self.learn.model))
            self.plx_run.log_file_ref(
                path=model_summary_path, name="model_summary", is_input=False
            )
        except Exception:  # noqa
            print(
                "Did not log model summary. "
                "Check if your model is PyTorch model and that Polyaxon has correctly initialized "
                "the artifacts/outputs path."
            )

        if self.log_model and not hasattr(self.learn, "save_model"):
            print(
                "Unable to log model to Polyaxon.\n",
                'Use "SaveModelCallback" to save model checkpoints '
                "that will be logged to Polyaxon.",
            )

    @client_handler(check_no_op=True)
    def after_batch(self):
        # log loss and opt.hypers
        if self.training:
            self._plx_step += 1
            metrics = {}
            if hasattr(self, "smooth_loss"):
                metrics["smooth_loss"] = to_detach(self.smooth_loss.clone())
            if hasattr(self, "loss"):
                metrics["raw_loss"] = to_detach(self.loss.clone())
            if hasattr(self, "train_iter"):
                metrics["train_iter"] = self.train_iter
            for i, h in enumerate(self.learn.opt.hypers):
                for k, v in h.items():
                    metrics[f"hypers_{k}"] = v
            self.plx_run.log_metrics(step=self._plx_step, **metrics)

    @client_handler(check_no_op=True)
    def after_epoch(self):
        # log metrics
        self.plx_run.log_metrics(
            step=self._plx_step,
            **{
                n: v
                for n, v in zip(self.recorder.metric_names, self.recorder.log)
                if n not in ["train_loss", "epoch", "time"]
            },
        )

        # log model weights
        if self.log_model and hasattr(self.learn, "save_model"):
            if self.learn.save_model.every_epoch:
                _file = join_path_file(
                    f"{self.learn.save_model.fname}_{self.learn.save_model.epoch}",
                    self.learn.path / self.learn.model_dir,
                    ext=".pth",
                )
                self.plx_run.log_model(
                    _file, framework="fastai", step=self.learn.save_model.epoch
                )
            else:
                _file = join_path_file(
                    self.learn.save_model.fname,
                    self.learn.path / self.learn.model_dir,
                    ext=".pth",
                )
                self.plx_run.log_model(_file, framework="fastai", versioned=False)
