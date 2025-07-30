import logging
from typing import Union

from jinja2 import Environment, StrictUndefined

from .entities import VariablePool, JinjaInput, ExprInput, StrInput, VarsInput, BoolInput

# 创建 Jinja2 环境并启用严格模式
template_env = Environment(undefined=StrictUndefined)


def is_list(obj):
    return isinstance(obj, list)


def evaluate_expression(expr_str: str, variable_pool: VariablePool):
    _import = "from datetime import datetime,timedelta\nimport math\n"
    code = _import + "\n\n" + f"__expr_result__ = (\n{expr_str.strip()}\n)"
    logging.debug(f"表达式执行 {code}")
    env_dict = variable_pool.to_dict()
    env_dict["__expr_result__"] = None
    exec(code, env_dict)
    return env_dict["__expr_result__"]


def render_jinja_template(jinja_template: str, variable_pool: VariablePool):
    env_dict = variable_pool.to_dict()
    template = template_env.from_string(jinja_template.strip())
    # template = Template(jinja_template.strip())
    return template.render(**env_dict).strip()


def execute_expression(input: Union[JinjaInput, ExprInput, StrInput, VarsInput, BoolInput],
                       variable_pool: VariablePool):
    if isinstance(input, str):
        return variable_pool.get_variable_value(input)
    elif isinstance(input, bool):
        return input
    elif isinstance(input, JinjaInput):
        return render_jinja_template(input.value, variable_pool)
    elif isinstance(input, ExprInput):
        return evaluate_expression(input.value, variable_pool)
    elif isinstance(input, VarsInput):
        if '[' in input.value:
            return evaluate_expression(input.value, variable_pool)
        return variable_pool.get_variable_value(input.value)
    elif isinstance(input, (BoolInput, StrInput)):
        return input.value
    else:
        raise TypeError(f"不支持的输入异常 {input}")
