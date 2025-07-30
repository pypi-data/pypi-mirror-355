from typing import TypedDict

from torch import nn, Tensor

class _Metric3DDepthModelInput(TypedDict):
    input: Tensor

class _Metric3DDepthModelOutput(TypedDict):
    prediction: Tensor
    predictions_list: list[Tensor]
    confidence: Tensor
    confidence_list: list[Tensor]
    pred_logit: None
    prediction_normal: Tensor
    normal_out_list: list[Tensor]
    low_resolution_init: list

class BaseDepthModel(nn.Module):
    def __init__(self, cfg: dict, **kwargs: object) -> None: ...
    def forward(self, data: _Metric3DDepthModelInput) -> tuple[Tensor, Tensor, _Metric3DDepthModelOutput]: ...
    def inference(self, data: _Metric3DDepthModelInput) -> tuple[Tensor, Tensor]: ...
