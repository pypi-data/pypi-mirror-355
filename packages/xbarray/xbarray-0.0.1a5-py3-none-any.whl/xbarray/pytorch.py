from xbarray.cls_impl.cls_base import ComputeBackendImplCls
from ._src.implementations import pytorch as pytorch_impl

class PytorchComputeBackend(metaclass=ComputeBackendImplCls):
    pass

for name in dir(pytorch_impl):
    if not name.startswith('_'):
        setattr(PytorchComputeBackend, name, getattr(pytorch_impl, name))

__all__ = [
    'PytorchComputeBackend',
]