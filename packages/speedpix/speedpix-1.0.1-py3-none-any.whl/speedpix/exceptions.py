from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from speedpix.prediction import Prediction


class SpeedPixException(Exception):
    """SpeedPix 的基础异常类"""


class PredictionError(SpeedPixException):
    """预测任务执行错误"""

    def __init__(self, prediction: Union["Prediction", str]) -> None:
        if isinstance(prediction, str):
            error_message = prediction
            self.prediction = None
        else:
            self.prediction = prediction
            error_message = prediction.error or "Prediction execution failed"
        super().__init__(error_message)

