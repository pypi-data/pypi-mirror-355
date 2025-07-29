from pai_ml.evaluate import load
from pai_ml.evaluate.utils import launch_gradio_widget

module = load("pai/recall_at_k")
launch_gradio_widget(module)
