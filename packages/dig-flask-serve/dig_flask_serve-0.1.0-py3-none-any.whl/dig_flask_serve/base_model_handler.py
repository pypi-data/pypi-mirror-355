# base_model_handler.py
class BaseModelHandler:
    def __init__(self):
        self.model = None

    def init_model(self):
        """模型初始化逻辑"""
        raise NotImplementedError

    def predict(self, input_data):
        """预测逻辑"""
        raise NotImplementedError
