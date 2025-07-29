from pai_ml.evaluate import load
from pai_ml.evaluate.utils import launch_gradio_widget

module = load("pai/first_relevant_rank")
launch_gradio_widget(module)
