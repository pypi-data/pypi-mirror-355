from instaui.common.jsonable import Jsonable
from instaui.vars.mixin_types.py_binding import CanInputMixin
from instaui.runtime._app import get_app_slot


class JsFn(Jsonable, CanInputMixin):
    """
    Creates a JavaScript function object from a raw code string.
    Valid targets include: `js_computed`, `js_watch`, and similar JS-bound methods.

    Args:
        code (str): Valid JavaScript function definition string.

    Example:
    .. code-block:: python
        a = ui.state(1)
        add = ui.js_fn(code="(a,b)=> a+b ")
        result = ui.js_computed(inputs=[add, a], code="(add,a)=>  add(a,10) ")

        html.number(a)
        ui.label(result)
    """

    def __init__(self, code: str, *, execute_immediately=False):
        self.code = code
        self.__type = "jsFn"
        app = get_app_slot()
        app.register_js_fn(self)
        self.__id = app.generate_js_fn_id()
        self._execute_immediately = execute_immediately

    def _to_input_config(self):
        return {
            "type": self.__type,
            "id": self.__id,
        }

    def _to_json_dict(self):
        data = super()._to_json_dict()
        data["type"] = self.__type
        data["id"] = self.__id

        if self._execute_immediately is True:
            data["immediately"] = 1

        return data
