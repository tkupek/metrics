# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any, Dict, List, Optional

import torch
from torch import Tensor

from torchmetrics.functional.regression.cosine_similarity import _cosine_similarity_compute, _cosine_similarity_update
from torchmetrics.metric import Metric
from torchmetrics.utilities.data import dim_zero_cat


class CosineSimilarity(Metric):
    r"""
    Computes the `Cosine Similarity`_
    between targets and predictions:

    .. math::
        cos_{sim}(x,y) = \frac{x \cdot y}{||x|| \cdot ||y||} =
        \frac{\sum_{i=1}^n x_i y_i}{\sqrt{\sum_{i=1}^n x_i^2}\sqrt{\sum_{i=1}^n y_i^2}}

    where :math:`y` is a tensor of target values, and :math:`x` is a tensor of predictions.

    Forward accepts

    - ``preds`` (float tensor): ``(N,d)``
    - ``target`` (float tensor): ``(N,d)``

    Args:
        reduction: how to reduce over the batch dimension using 'sum', 'mean' or 'none'
                    (taking the individual scores)
        compute_on_step:
            Forward only calls ``update()`` and returns None if this is set to False.

            .. deprecated:: v0.8
                Argument has no use anymore and will be removed v0.9.

        kwargs:
            Additional keyword arguments, see :ref:`Metric kwargs` for more info.

    Example:
        >>> from torchmetrics import CosineSimilarity
        >>> target = torch.tensor([[0, 1], [1, 1]])
        >>> preds = torch.tensor([[0, 1], [0, 1]])
        >>> cosine_similarity = CosineSimilarity(reduction = 'mean')
        >>> cosine_similarity(preds, target)
        tensor(0.8536)

    """
    is_differentiable = True
    higher_is_better = True
    preds: List[Tensor]
    target: List[Tensor]

    def __init__(
        self,
        reduction: str = "sum",
        compute_on_step: Optional[bool] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        super().__init__(compute_on_step=compute_on_step, **kwargs)
        allowed_reduction = ("sum", "mean", "none", None)
        if reduction not in allowed_reduction:
            raise ValueError(f"Expected argument `reduction` to be one of {allowed_reduction} but got {reduction}")
        self.reduction = reduction

        self.add_state("preds", [], dist_reduce_fx="cat")
        self.add_state("target", [], dist_reduce_fx="cat")

    def _update(self, preds: Tensor, target: Tensor) -> None:  # type: ignore
        """Update metric states with predictions and targets.

        Args:
            preds: Predicted tensor with shape ``(N,d)``
            target: Ground truth tensor with shape ``(N,d)``
        """
        preds, target = _cosine_similarity_update(preds, target)

        self.preds.append(preds)
        self.target.append(target)

    def _compute(self) -> Tensor:
        preds = dim_zero_cat(self.preds)
        target = dim_zero_cat(self.target)
        return _cosine_similarity_compute(preds, target, self.reduction)
