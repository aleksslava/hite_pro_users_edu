from __future__ import annotations

from aiogram.filters.state import State, StatesGroup

from fsm_forms import fsm_models

_REGISTRY: dict[str, State] = {}

for _name in dir(fsm_models):
    _obj = getattr(fsm_models, _name)
    if isinstance(_obj, type) and issubclass(_obj, StatesGroup) and _obj is not StatesGroup:
        for _st in _obj.__all_states__:
            if _st.state is not None:
                _REGISTRY[_st.state] = _st


def resolve_state(state_str: str | None) -> State | None:
    if not state_str:
        return None
    return _REGISTRY.get(state_str)
