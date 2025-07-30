from torch import Tensor

try:
    from mmcv.utils import Config  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:
    from mmengine import Config

from mono.model.model_pipelines.__base_model__ import (
    _Metric3DDepthModelInput,
    _Metric3DDepthModelOutput,
    BaseDepthModel,
)

class DepthModel(BaseDepthModel):
    def inference(self, data: _Metric3DDepthModelInput) -> tuple[Tensor, Tensor, _Metric3DDepthModelOutput]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Run the Metric3D depth inference.

        Args:
            data:
                Dictionary containing the RGB image(s).
                The image(s) should have been preprocessed into a channels first, normalized, batched (4D) float tensor.

        Returns:
            A tuple with:
            - Predicted depth.
            - Confidence.
            - Output dict containing extra data.
        """

def get_configured_monodepth_model(cfg: Config) -> BaseDepthModel: ...
