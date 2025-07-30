class GameVisionError(Exception):
    pass

class DatasetError(GameVisionError):
    pass

class ModelExportError(GameVisionError):
    pass

class InferenceError(GameVisionError):
    pass

class ValidationError(GameVisionError):
    pass