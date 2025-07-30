import json
import logging
import re
import threading
from abc import abstractmethod, ABC
from collections import deque
from datetime import datetime
from typing import Dict, Any, Union, List, Optional, Literal, Type, TypeVar, get_origin, get_args

from pydantic import BaseModel, Field, ValidationError


class WorkFlowExecError(Exception):
    """workflow执行异常"""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.kwargs['date'] = date_milliseconds()

    def to_dict(self):
        return self.kwargs

    def __str__(self):
        return f"流程执行异常 [{self.kwargs['msg']}], {' '.join([''.join((k, '=', str(v))) for k, v in self.kwargs.items()])} "


class VarNameError(Exception):
    """workflow变量异常"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"变量名非法 [{self.name}]"


class JinjaInput(BaseModel):
    type: Literal['jinja'] = 'jinja'
    value: str


class ExprInput(BaseModel):
    type: Literal['expr'] = 'expr'
    value: str


class StrInput(BaseModel):
    type: Literal['str'] = 'str'
    value: str


class VarsInput(BaseModel):
    type: Optional[Literal['vars']] = 'vars'
    value: str


class BoolInput(BaseModel):
    type: Literal['bool'] = 'bool'
    value: bool


class VariableValue(BaseModel):
    name: str
    value: Union[
        Union[str, int, float, bool], Dict[str, Union[str, int, float, bool]], List[Union[str, int, float, bool]], List[
            Dict[str, Union[str, int, float, bool]]]]

    def append(self, new_value: Any) -> None:
        if isinstance(self.value, list):
            self.value.append(new_value)
        else:
            raise TypeError("当前值类型不支持追加操作")


class VariablePool:
    def __init__(self, init_value: dict = None) -> None:

        if init_value:
            _init_value = init_value
        else:
            _init_value = {}

        self.variables_mapping: Dict[str, VariableValue] = {k: VariableValue(name=k, value=v) for k, v in
                                                            _init_value.items()}
        self.lock = threading.Lock()

    @staticmethod
    def is_valid_python_variable_name(name):
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
        return re.match(pattern, name) is not None

    def inner_append_variable(self, name: str, value) -> None:
        """内部程序用于变量赋值"""
        with self.lock:
            logging.debug(f"变量赋值 {name}:{str(value)}")
            self.variables_mapping[name] = VariableValue(name=name, value=value)

    def append_variable(self, name: str, value) -> None:
        if self.is_valid_python_variable_name(name):
            with self.lock:
                logging.debug(f"变量赋值 {name}:{str(value)}")
                self.variables_mapping[name] = VariableValue(name=name, value=value)
        else:
            raise ValueError(
                f"无效的变量名`{name}`。用户自定义变量名必须以字母（A-Z 或 a-z）开头，且只能包含字母、数字（0-9）和下划线（_）。")

    def append_obj_variable(self, name: str,
                            value: BaseModel | list[BaseModel] | dict[str, BaseModel | list[BaseModel]]) -> None:
        """
        将Pydantic对象转换为json数据后写入变量池
        """
        if value is None:
            raise ValueError(f"{name}值为空")  # 处理单个BaseModel
        if isinstance(value, BaseModel):
            self.append_variable(name, value.model_dump_json())

            # 处理BaseModel列表
        elif isinstance(value, list):
            json_list = [item.model_dump_json() for item in value if isinstance(item, BaseModel)]
            self.append_variable(name, json.dumps(json_list))

            # 处理字典（值为BaseModel或BaseModel列表）
        elif isinstance(value, dict):
            json_dict = {}
            for k, v in value.items():
                if isinstance(v, BaseModel):
                    json_dict[k] = v.model_dump_json()
                elif isinstance(v, list):
                    json_dict[k] = [item.model_dump_json() for item in v if isinstance(item, BaseModel)]
            self.append_variable(name, json.dumps(json_dict))

    T = TypeVar("T", bound=BaseModel)

    def get_obj_variable_value(self, name: str, cls: Type[T], default_value=None) -> T | list[T] | dict[
        str, T | list[T]]:
        """
        读取json或者字典数据，转换为Pydantic对象
        """
        value = self.get_variable_value(name, default_value)
        if value is None:
            raise KeyError(f"变量名称不存在 {name}")
        try:
            # 统一预处理JSON字符串
            parsed_value = json.loads(value) if isinstance(value, str) else value

            # 处理泛型容器（如list[T]）
            origin_cls = get_origin(cls)
            if origin_cls is list:
                model_cls = get_args(cls)[0]  # 提取内部模型类
                return [model_cls.model_validate(item) for item in parsed_value]
            else:
                return cls.model_validate(parsed_value)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}") from e
        except ValidationError as e:
            raise ValueError(f"数据验证失败: {e.errors()}") from e

    def get_variable_value(self, name: str, default_value=None) -> Union[
        Union[str, int, float, bool], Dict[str, Union[str, int, float, bool]], List[Union[str, int, float, bool]], List[
            Dict[str, Union[str, int, float, bool]]]]:
        with self.lock:
            if name in self.variables_mapping:
                return self.variables_mapping[name].value
            elif default_value is not None:
                return default_value
            else:
                raise KeyError(f"变量名称不存在 {name}")

    def append_to_variable(self, name: str, new_value: Union[str, int, float, Dict[str, Any]]) -> None:
        with (self.lock):
            if isinstance(new_value, (str, int, float, Dict[str, Any])):
                if name in self.variables_mapping:
                    self.variables_mapping[name].value.append(new_value)
                else:
                    self.variables_mapping[name] = VariableValue(name=name, value=[new_value])
            else:
                raise TypeError(f"append变量类型不支持 {name}")

    def to_dict(self) -> dict:
        """ 用于jinja或expr 环境的变量注入 """
        return {k: v.value for k, v in self.variables_mapping.items()}


class BaseStep(BaseModel):
    stepSeq: str
    stepLabel: str
    stepInst: str
    preStepId: Optional[str] = None
    parentStepId: Optional[str] = None
    preStepAllSucceedCheck: Optional[bool] = True
    stepConfig: Dict = Field(default_factory=dict)


class TapeSchema(BaseModel):
    tape_id: str
    tape_name: Optional[str] = None
    tape_descr: Optional[str] = None
    steps: List[BaseStep] = Field(default_factory=dict)


class OutPutValue(BaseModel):
    name: JinjaInput | str  # 变量名 用户定义
    value: Union[
        Union[str, int, float, bool], Dict[str, Union[str, int, float, bool]], List[Union[str, int, float, bool]], List[
            Dict[str, Union[str, int, float, bool]]]] = None


class OutPut1(BaseModel):
    result1: OutPutValue


class OutPut2(BaseModel):
    result1: OutPutValue
    result2: OutPutValue


class OutPut3(BaseModel):
    result1: OutPutValue
    result2: OutPutValue
    result3: OutPutValue


class TraceValue(BaseModel):
    tape_id: str
    tape_name: str
    session_id: str
    stepSeq: str
    stepLabel: str
    stepInst: str
    node_exec_id: str
    date: float
    type: str
    data: Dict = Field(default_factory=dict)

    def to_dict(self):
        return self.model_dump()


class Trace:
    """状态跟踪类"""

    def __init__(self, session_id: str, tape_schema: TapeSchema):
        self.trace_status = ThreadSafeDeque()
        self.session_id = session_id
        self.tape_id = tape_schema.tape_id
        self.tape_name = tape_schema.tape_name
        self.step_label_mapping = {i.stepSeq: (i.stepLabel, i.stepInst) for i in tape_schema.steps}

    def add_error(self, error: WorkFlowExecError):
        self.trace_status.append(error)

    def popleft(self) -> Union[WorkFlowExecError, TraceValue]:
        return self.trace_status.popleft()

    def _add_trace(self, __type__: str, stepSeq: str, node_exec_id: str, **kwargs):
        self.trace_status.append(TraceValue(
            **{'tape_id': self.tape_id, 'tape_name': self.tape_name, 'session_id': self.session_id, 'stepSeq': stepSeq,
               'stepLabel': self.step_label_mapping[stepSeq][0], 'stepInst': self.step_label_mapping[stepSeq][1],
               'node_exec_id': node_exec_id,  # node_exec_id 需要 node 函数 run执行时 生成 用于区分循环结构下 节点多次执行的 状态区分
               'date': date_milliseconds(), 'type': __type__, 'data': kwargs}))

    def add_trace_log(self, stepSeq: str, node_exec_id: str, **kwargs):
        self._add_trace(stepSeq=stepSeq, node_exec_id=node_exec_id, __type__='log', **kwargs)

    def add_trace_in(self, stepSeq: str, node_exec_id: str, **kwargs):
        self._add_trace(stepSeq=stepSeq, node_exec_id=node_exec_id, __type__='in', **kwargs)

    def add_trace_out(self, stepSeq: str, node_exec_id: str, **kwargs):
        self._add_trace(stepSeq=stepSeq, node_exec_id=node_exec_id, __type__='out', **kwargs)


class NodeBase(ABC, BaseModel):

    @abstractmethod
    def run(self, variable_pool: VariablePool, step_id: str, trace: Trace, session_id: str, tape_id: str,
            step_schema: BaseStep, **kwargs):
        pass

    @staticmethod
    def write_log(msg: str, msg_level: Literal['info', 'error', 'warning'] = 'info', **kwargs):
        if msg_level == 'info':
            logging.info(msg, **kwargs)
        elif msg_level == 'error':
            logging.error(msg, **kwargs)
        elif msg_level == 'warning':
            logging.warning(msg, **kwargs)
        else:
            logging.info(msg, **kwargs)


class ThreadSafeDeque:
    def __init__(self):
        self.deque = deque()
        self.lock = threading.Lock()

    def append(self, item):
        with self.lock:
            self.deque.append(item)

    def appendleft(self, item):
        with self.lock:
            self.deque.appendleft(item)

    def pop(self):
        with self.lock:
            return self.deque.pop()

    def popleft(self):
        with self.lock:
            return self.deque.popleft()

    def __len__(self):
        with self.lock:
            return len(self.deque)


def date_milliseconds():
    now = datetime.now()
    # 将当前时间转换为秒级时间戳
    timestamp_seconds = now.timestamp()

    # 获取微秒数并转换为毫秒（保留小数）
    milliseconds = now.microsecond / 1000.0

    # 计算毫秒级的时间戳
    timestamp_milliseconds = timestamp_seconds * 1000 + milliseconds

    return timestamp_milliseconds
