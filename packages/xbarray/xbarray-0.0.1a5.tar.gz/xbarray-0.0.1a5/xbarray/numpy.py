from xbarray.cls_impl.cls_base import ComputeBackendImplCls
from ._src.implementations import numpy as numpy_impl

class NumpyComputeBackend(metaclass=ComputeBackendImplCls):
    pass

for name in dir(numpy_impl):
    if not name.startswith('_'):
        setattr(NumpyComputeBackend, name, getattr(numpy_impl, name))

__all__ = [
    'NumpyComputeBackend',
]