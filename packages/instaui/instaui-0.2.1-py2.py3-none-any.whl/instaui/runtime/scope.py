from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List
import functools
import weakref
from instaui.common.jsonable import Jsonable


if TYPE_CHECKING:
    from instaui.vars.mixin_types.var_type import VarMixin
    from instaui.vars.mixin_types.py_binding import CanInputMixin
    from instaui.vars.web_computed import WebComputed
    from instaui.vars.js_computed import JsComputed
    from instaui.vars.vue_computed import VueComputed
    from instaui.vars.data import ConstData
    from instaui.watch.web_watch import WebWatch
    from instaui.watch.js_watch import JsWatch
    from instaui.watch.vue_watch import VueWatch
    from instaui.vars.element_ref import ElementRef


class Scope(Jsonable):
    def __init__(self, id: str) -> None:
        super().__init__()
        self.id = id
        self._vars_id_counter = 0
        self._element_ref_id_counter = 0
        self._refs: List[VarMixin] = []
        self._const_data: List[ConstData] = []
        self._js_computeds: List[JsComputed] = []
        self._vue_computeds: List[VueComputed] = []
        self._web_computeds: List[WebComputed] = []
        self._element_refs: List[ElementRef] = []
        self._run_method_records: List = []
        self._web_watchs: List[WebWatch] = []
        self._js_watchs: List[JsWatch] = []
        self._vue_watchs: List[VueWatch] = []
        self._query = {}

    def set_run_method_record(
        self, scope_id: str, element_ref_id: str, method_name: str, args
    ):
        self._run_method_records.append((scope_id, element_ref_id, method_name, args))

    def generate_vars_id(self) -> str:
        self._vars_id_counter += 1
        return str(self._vars_id_counter)

    def generate_element_ref_id(self) -> str:
        self._element_ref_id_counter += 1
        return str(self._element_ref_id_counter)

    def register_element_ref(self, ref: ElementRef):
        self._element_refs.append(ref)

    def set_query(self, url: str, key: str, on: List[CanInputMixin]) -> None:
        self._query = {
            "url": url,
            "key": key,
            "on": [v._to_input_config() for v in on],
        }

    def register_web_watch(self, watch: WebWatch) -> None:
        self._web_watchs.append(watch)

    def register_js_watch(self, watch: JsWatch) -> None:
        self._js_watchs.append(watch)

    def register_vue_watch(self, watch: VueWatch) -> None:
        self._vue_watchs.append(watch)

    def register_data_task(self, data: ConstData):
        weak_obj = weakref.ref(data)

        def register_fn():
            self._const_data.append(weak_obj())  # type: ignore
            return self.generate_vars_id()

        return VarRegisterTask(self.id, register_fn)

    def register_ref_task(self, ref: VarMixin):
        weak_obj = weakref.ref(ref)

        def register_fn():
            self._refs.append(weak_obj())  # type: ignore
            return self.generate_vars_id()

        return VarRegisterTask(self.id, register_fn)

    def register_js_computed_task(self, computed: JsComputed):
        weak_obj = weakref.ref(computed)

        def register_fn():
            self._js_computeds.append(weak_obj())  # type: ignore
            return self.generate_vars_id()

        return VarRegisterTask(self.id, register_fn)

    def register_computed_task(self, computed: WebComputed):
        weak_obj = weakref.ref(computed)

        def register_fn():
            self._web_computeds.append(weak_obj())  # type: ignore
            return self.generate_vars_id()

        return VarRegisterTask(self.id, register_fn)

    def register_vue_computed_task(self, computed: VueComputed):
        weak_obj = weakref.ref(computed)

        def register_fn():
            self._vue_computeds.append(weak_obj())  # type: ignore
            return self.generate_vars_id()

        return VarRegisterTask(self.id, register_fn)

    def _to_json_dict(self):
        data = super()._to_json_dict()
        if self._refs:
            data["refs"] = self._refs
        if self._query:
            data["query"] = self._query
        if self._web_watchs:
            data["py_watch"] = self._web_watchs
        if self._js_watchs:
            data["js_watch"] = self._js_watchs
        if self._vue_watchs:
            data["vue_watch"] = self._vue_watchs
        if self._element_refs:
            data["eRefs"] = self._element_refs

        if self._web_computeds:
            data["web_computed"] = self._web_computeds

        if self._js_computeds:
            data["js_computed"] = self._js_computeds

        if self._vue_computeds:
            data["vue_computed"] = self._vue_computeds
        if self._const_data:
            data["data"] = self._const_data

        return data


class GlobalScope(Scope):
    def __init__(self, id: str) -> None:
        super().__init__(id)

    def register_ref_task(self, var: VarMixin) -> None:
        raise ValueError("Can not register ref in global scope")

    def register_computed_task(self, computed: WebComputed) -> None:
        raise ValueError("Can not register web_computeds  in global scope")

    def register_js_computed_task(self, computed: JsComputed):
        raise ValueError("Can not register js_computeds  in global scope")

    def register_vue_computed_task(self, computed: VueComputed):
        raise ValueError("Can not register vue_computeds  in global scope")

    def register_web_watch(self, watch: WebWatch) -> None:
        raise ValueError("Can not register web_watchs  in global scope")

    def register_js_watch(self, watch: JsWatch) -> None:
        raise ValueError("Can not register js_watchs  in global scope")

    def register_vue_watch(self, watch: VueWatch) -> None:
        raise ValueError("Can not register vue_watchs  in global scope")


class VarRegisterTask:
    def __init__(self, scope_id: str, register_fn: Callable[[], str]) -> None:
        self._scope_id = scope_id
        self._id_gen_fn = functools.lru_cache(maxsize=1)(register_fn)

    @property
    def scope_id(self) -> str:
        return self._scope_id

    @property
    def var_id(self) -> str:
        return self._id_gen_fn()
