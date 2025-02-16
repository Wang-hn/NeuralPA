import os
from typing import *

import torch

from typet5.model import ModelWrapper
from typet5.train import PreprocessArgs
from typet5.utils import *
from typet5.function_decoding import (
    RolloutCtx,
    PreprocessArgs,
    DecodingOrders,
    AccuracyMetric,
)
from typet5.static_analysis import PythonProject
import asyncio

os.chdir(proj_root())

# download or load the model
# wrapper = ModelWrapper.load_from_hub("MrVPlusOne/TypeT5-v7")
model_path = "./MrVPlusOne/TypeT5-v7"
absolute_path = Path(model_path).resolve()
wrapper = ModelWrapper.load(absolute_path)
device = torch.device(f"cuda" if torch.cuda.is_available() else "cpu")
wrapper.to(device)
print("model loaded")

# set up the rollout parameters
rctx = RolloutCtx(model=wrapper)
pre_args = PreprocessArgs()
# we use the double-traversal decoding order, where the model can make corrections
# to its previous predictions in the second pass
decode_order = DecodingOrders.DoubleTraversal()

# Use case 1: Run TypeT5 on a given project, taking advantage of existing user
# annotations and only make predictions for missing types.

project = PythonProject.parse_from_root(proj_root() / "data/ex_repo")
# 异步方法的调用方式修改
rollout = asyncio.run(rctx.run_on_project(project, pre_args, decode_order))


# Use case 2: Run TypeT5 on a test project where all user annotations will be treated as
# labels and removed before running the model.

eval_r = asyncio.run(rctx.evaluate_on_projects([project], pre_args, decode_order))
eval_r.print_predictions()

metrics = AccuracyMetric.default_metrics(wrapper.common_type_names)
for metric in metrics:
    accs = eval_r.error_analysis(None, metric).accuracies
    pretty_print_dict({metric.name: accs})