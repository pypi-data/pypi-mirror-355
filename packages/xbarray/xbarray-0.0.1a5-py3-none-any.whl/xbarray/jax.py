from xbarray.cls_impl.cls_base import ComputeBackendImplCls
from ._src.implementations import jax as jax_impl

class JaxComputeBackend(metaclass=ComputeBackendImplCls):
    pass

for name in dir(jax_impl):
    if not name.startswith('_'):
        setattr(JaxComputeBackend, name, getattr(jax_impl, name))

__all__ = [
    'JaxComputeBackend',
]