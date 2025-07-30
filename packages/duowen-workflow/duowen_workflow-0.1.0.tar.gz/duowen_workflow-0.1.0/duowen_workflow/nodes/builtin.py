import logging
from typing import Union, Optional, List
from uuid import uuid4

from pydantic import BaseModel

from ..entities import VariablePool, NodeBase, JinjaInput, ExprInput, VarsInput, OutPut1, Trace, StrInput
from ..utils import execute_expression, is_list


class ForInput(BaseModel):
    text: Union[ExprInput, VarsInput]  # 循环条件
    vars_name: Optional[JinjaInput] = None  # 条件变量名


class ForOutput(BaseModel):
    name: Optional[StrInput] = None  # 变量名 用户定义
    value: Optional[Union[VarsInput, JinjaInput]] = None  # 循环体内选择绑定


class For(NodeBase):
    input: ForInput
    output: Optional[ForOutput] = None  # 输出结果

    def get_loop_value(self, variable_pool: VariablePool, stepSeq: str, trace: Trace, **kwargs):

        if isinstance(self.input.text, VarsInput):

            _value = variable_pool.get_variable_value(self.input.text.value)

            if not is_list(_value):
                raise Exception(f"变量 {self.input.text.value} 不支持循环")

            return self.input.text.value, variable_pool.get_variable_value(self.input.text.value)

        elif isinstance(self.input.text, ExprInput):
            if self.input.vars_name:
                _value = execute_expression(self.input.text, variable_pool)
                _vars_name = execute_expression(self.input.vars_name, variable_pool)
                if not is_list(_value):
                    raise Exception(f"变量 {_vars_name} 不支持循环")

                variable_pool.append_variable(_vars_name, _value)

                return _vars_name, _value
            else:
                raise ValueError("循环组件内,使用表达式循环需要定义变量")

    def run(self, **kwargs):
        ...


class CondExpr(BaseModel):
    next_id: str
    expr: ExprInput


class IfInput(BaseModel):
    cond: List[CondExpr]  # If条件


class If(NodeBase):
    """
    {input:{cond:
        [
            {next_id:1, expr:{type:expr,value:1=1},
            {next_id:1, expr:{type:expr,value:1=1},
        ]
    }}
    """
    input: IfInput

    def run(self, variable_pool: VariablePool, stepSeq: str, trace: Trace, next_id: str = None, **kwargs):

        _node_exec_id = uuid4().hex
        trace.add_trace_in(stepSeq=stepSeq, node_exec_id=_node_exec_id, **self.input.model_dump())

        for i in self.input.cond:
            _res = execute_expression(i.expr, variable_pool)
            trace.add_trace_log(stepSeq=stepSeq, node_exec_id=_node_exec_id, next_id=i.next_id,
                                expr=i.expr.model_dump(), res=_res)
            if _res:
                if next_id:
                    if i.next_id == next_id:
                        trace.add_trace_out(stepSeq=stepSeq, node_exec_id=_node_exec_id, next_id=i.next_id)
                        return i.next_id
                    else:
                        return False
                else:
                    trace.add_trace_out(stepSeq=stepSeq, node_exec_id=_node_exec_id, next_id=i.next_id)
                    return i.next_id
        return False


class PrintInput(BaseModel):
    text: Union[JinjaInput, VarsInput]  # 打印内容


class Print(NodeBase):
    input: PrintInput

    def run(self, variable_pool: VariablePool, stepSeq: str, trace: Trace, **kwargs):
        _node_exec_id = uuid4().hex
        trace.add_trace_in(stepSeq=stepSeq, node_exec_id=_node_exec_id, **self.input.dict())
        res = execute_expression(self.input.text, variable_pool)
        print(res)
        logging.info(res)
        trace.add_trace_in(stepSeq=stepSeq, node_exec_id=_node_exec_id, print_value=res)
        trace.add_trace_out(stepSeq=stepSeq, node_exec_id=_node_exec_id, result="END")


class CodeExecInput(BaseModel):
    code_text: StrInput  # 代码


class CodeExec(NodeBase):
    """代码执行"""
    input: CodeExecInput
    output: OutPut1  # 输出结果

    def run(self, variable_pool: VariablePool, stepSeq: str, trace: Trace, **kwargs):
        """
        前端用户代码模板
        def main(var_a,var_b):
            return abc
        """
        _node_exec_id = uuid4().hex
        trace.add_trace_in(stepSeq=stepSeq, node_exec_id=_node_exec_id, **self.input.model_dump())

        code_text = execute_expression(self.input.code_text, variable_pool)

        # 获取函数变量
        _inspect_code = '''
{code_text}

import inspect
__sig__ = inspect.signature(main)
__param_names__ = [param.name for param in __sig__.parameters.values()]
'''
        _inspect_code = _inspect_code.format(code_text=code_text)
        _inspect_env_dct = {'__param_names__': []}

        exec_env_dct = {"__exec_code_res__": None}
        variable_pool_dct = variable_pool.to_dict()
        exec(_inspect_code, _inspect_env_dct)
        if _inspect_env_dct["__param_names__"] and is_list(_inspect_env_dct["__param_names__"]):
            trace.add_trace_log(stepSeq=stepSeq, node_exec_id=_node_exec_id,
                                vars_name=_inspect_env_dct["__param_names__"])
            for i in _inspect_env_dct["__param_names__"]:
                if i not in variable_pool_dct:
                    raise ValueError(f"变量名 {i} 不存在")
                else:
                    exec_env_dct[i] = variable_pool_dct[i]

        _code = '''
{code_text}

__exec_code_res__=main({params})'''.format(code_text=execute_expression(self.input.code_text, variable_pool),
                                           params=', '.join(
                                               [i for i in list(exec_env_dct.keys()) if i != "__exec_code_res__"]))

        exec(_code, exec_env_dct)

        if exec_env_dct["__exec_code_res__"]:
            self.output.result1.value = exec_env_dct["__exec_code_res__"]
        trace.add_trace_log(stepSeq=stepSeq, node_exec_id=_node_exec_id, res=exec_env_dct["__exec_code_res__"])
        trace.add_trace_out(stepSeq=stepSeq, node_exec_id=_node_exec_id, result=exec_env_dct["__exec_code_res__"])


class StartInput(BaseModel):
    vars_name: List[StrInput]


class Start(NodeBase):
    """开始节点"""
    input: StartInput

    def run(self, variable_pool, stepSeq, trace, **kwargs):
        _node_exec_id = uuid4().hex
        trace.add_trace_in(stepSeq=stepSeq, node_exec_id=_node_exec_id, **self.input.dict())
        var_list = []
        for i in self.input.vars_name:
            var = execute_expression(i, variable_pool)
            if var not in variable_pool.to_dict().keys():
                var_list.append(var)
        if var_list:
            raise KeyError(f"变量{', '.join(var_list)}不存在")

        trace.add_trace_out(stepSeq=stepSeq, node_exec_id=_node_exec_id, result="END")
