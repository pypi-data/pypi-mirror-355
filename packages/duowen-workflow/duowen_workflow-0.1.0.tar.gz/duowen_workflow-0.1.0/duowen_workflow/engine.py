import logging
import traceback
from typing import Dict, Literal
from uuid import uuid4

from pydantic import ValidationError

from .entities import VariablePool, TapeSchema, ThreadSafeDeque, BaseStep, Trace, JinjaInput
from .entities import WorkFlowExecError
from .nodes import nodes, For, If
from .utils import execute_expression


class EngineFlow:

    def __init__(self, tape_schema: TapeSchema, variable_pool: VariablePool = None, session_id=None,
                 trace: Trace = None, step_mapping: Dict[str, BaseStep] = None, parent_id: str = None):

        self.tape_schema = tape_schema

        if variable_pool:
            self.variable_pool = variable_pool
        else:
            self.variable_pool = VariablePool()

        if session_id:
            self.session_id = session_id
        else:
            self.session_id = uuid4().hex

        if step_mapping:
            self.step_mapping = step_mapping
        else:
            self.step_mapping = {i.stepSeq: i for i in self.tape_schema.steps}

        if parent_id:
            self.parent_id = parent_id
        else:
            self.parent_id = '-1'

        self.success_step_id = set()

        if trace:
            self.trace = trace
        else:
            self.trace = Trace(self.session_id, self.tape_schema)


    def get_loop_tape_schema(self, stepSeq):
        # todo 目前没有实现多层循环图的获取，后续需要添加
        _tape_schema = {'tape_id': self.tape_schema.tape_id, 'tape_name': self.tape_schema.tape_name,
                        'tape_descr': self.tape_schema.tape_descr, 'steps': []}

        for i in self.filter_parent_id(stepSeq):
            _tape_schema['steps'].append(i.model_dump())

        return _tape_schema

    def filter_pre_step_id(self, step_id, parent_id):
        _data = []
        for i in self.tape_schema.steps:
            if step_id in [j.strip() for j in i.preStepId.split(",")] and i.parentStepId == parent_id:
                _data.append(i)
        return _data

    def filter_parent_id(self, stepSeq):
        _data = []
        for i in self.tape_schema.steps:
            if i.parentStepId == stepSeq:
                _data.append(i)
        return _data

    def is_pre_dependency_succeeded(self, check_step_id: str, trigger_step_id: str, trace: Trace):
        """check_step_id 需要被检查的步骤ID trigger_step_id 触发该检查的步骤ID"""
        for i in self.step_mapping[check_step_id].preStepId.split(','):
            # print("-----------------",i)
            # print(self.step_mapping[check_step_id].preStepAllSucceedCheck)
            # print(i in self.success_step_id)
            # print(self.success_step_id)

            if self.step_mapping[i].stepInst == 'If':  # 如果前置节点是条件判断需要 判断里面的条件
                inst_if: If = nodes['If'](**self.step_mapping[i].stepConfig)
                if inst_if.run(stepSeq=trigger_step_id, next_id=check_step_id, variable_pool=self.variable_pool,
                               trace=trace):
                    pass
                else:
                    return False

            elif self.step_mapping[
                check_step_id].preStepAllSucceedCheck is False and trigger_step_id in self.success_step_id:
                return True

            elif i in self.success_step_id:
                pass

            else:
                return False
        return True

    def run(self):

        queue = ThreadSafeDeque()
        for k, v in self.step_mapping.items():
            if v.preStepId == '-1' and v.parentStepId == self.parent_id:
                queue.append(v)

        while 1:
            try:
                curr_step: BaseStep = queue.popleft()
            except IndexError:
                break  # 正常退出循环，程序结束

            _exec_vars = {"variable_pool": self.variable_pool, "trace": self.trace, "session_id": self.session_id,
                          'tape_id': self.tape_schema.tape_id, 'tape_name': self.tape_schema.tape_name,
                          'tape_descr': self.tape_schema.tape_descr, "stepSeq": curr_step.stepSeq,
                          "stepInst": curr_step.stepInst, "step_schema": self.step_mapping[curr_step.stepSeq]}

            try:
                if curr_step.stepInst == 'For':
                    # 获取子图 构建新的 WorkflowEngineManager
                    _sub_tape = self.get_loop_tape_schema(curr_step.stepSeq)
                    curr_init: For = nodes[curr_step.stepInst](**curr_step.stepConfig)

                    _node_exec_id = uuid4().hex
                    self.trace.add_trace_in(stepSeq=curr_step.stepSeq, node_exec_id=_node_exec_id,
                                            **curr_init.model_dump())

                    for_vars_name, for_vars_value = curr_init.get_loop_value(**_exec_vars)

                    for_out_name = None
                    if curr_init.output.name:
                        for_out_name = execute_expression(curr_init.output.name, self.variable_pool)

                    self.trace.add_trace_log(stepSeq=curr_step.stepSeq, node_exec_id=_node_exec_id,
                                             var_name=for_vars_name, var_value=for_vars_value)

                    try:

                        # 获取循环变量
                        for e, i in enumerate(for_vars_value):
                            self.variable_pool.inner_append_variable(f"__index__{for_vars_name}", e)
                            EngineFlow(tape_schema=TapeSchema(**_sub_tape), session_id=self.session_id,
                                       variable_pool=self.variable_pool, trace=self.trace, parent_id=curr_step.stepSeq,
                                       step_mapping=self.step_mapping).run()

                            if for_out_name:
                                for_out_value = execute_expression(curr_init.output.value, self.variable_pool)
                                self.variable_pool.append_to_variable(for_out_name, for_out_value)

                    except WorkFlowExecError as e:
                        self.trace.add_trace_out(stepSeq=curr_step.stepSeq, node_exec_id=_node_exec_id,
                                                 msg='循环体执行失败')
                        raise

                    self.trace.add_trace_out(stepSeq=curr_step.stepSeq, node_exec_id=_node_exec_id, status='over')

                    self.success_step_id.add(curr_step.stepSeq)

                    for i in self.filter_pre_step_id(curr_step.stepSeq, self.parent_id):
                        if self.is_pre_dependency_succeeded(check_step_id=i.stepSeq, trigger_step_id=curr_step.stepSeq,
                                                            trace=self.trace):
                            queue.append(i)

                elif curr_step.stepInst == 'If':
                    curr_init: If = nodes[curr_step.stepInst](**curr_step.stepConfig)
                    _next_id = curr_init.run(**_exec_vars)
                    self.success_step_id.add(curr_step.stepSeq)
                    if _next_id:

                        if not self.step_mapping.get(_next_id, None):
                            logging.warning(
                                f"程序 {self.tape_schema.tape_name} 条件判断{curr_step.stepSeq} 分支 没有下级节点{_next_id}")

                        elif self.step_mapping[_next_id].parentStepId != self.parent_id:
                            logging.warning(f"程序 {self.tape_schema.tape_name} 下级节点不在parent层次")

                        # 条件判断的下级节点的上级节点指向唯一且当前节点相同则直接进行进入工作队列
                        elif self.step_mapping[_next_id].preStepId == curr_step.stepSeq:
                            queue.append(self.step_mapping[_next_id])

                        # 多个指向进入前置完成队列
                        elif self.is_pre_dependency_succeeded(check_step_id=_next_id, trigger_step_id=curr_step.stepSeq,
                                                              trace=self.trace):
                            queue.append(self.step_mapping[_next_id])

                else:
                    curr_init = nodes[curr_step.stepInst](**curr_step.stepConfig)
                    curr_init.run(**_exec_vars)

                    self.success_step_id.add(curr_step.stepSeq)

                    if hasattr(curr_init, 'output'):
                        for k, v in curr_init.output.model_dump().items():
                            if v["name"] is not None and v['value'] is not None:
                                if isinstance(v["name"], str):
                                    v_name = v["name"]
                                else:
                                    v_name = execute_expression(JinjaInput(**v["name"]), self.variable_pool)
                                self.variable_pool.append_variable(v_name, v['value'])

                    for i in self.filter_pre_step_id(curr_step.stepSeq, self.parent_id):

                        if self.is_pre_dependency_succeeded(trigger_step_id=curr_step.stepSeq, check_step_id=i.stepSeq,
                                                            trace=self.trace):
                            queue.append(i)

            except WorkFlowExecError:
                raise

            except ValidationError as e:

                error = WorkFlowExecError(
                    **{'tape_id': self.tape_schema.tape_id, 'tape_name': self.tape_schema.tape_name,
                       "stepSeq": curr_step.stepSeq, "stepLabel": curr_step.stepLabel, "stepInst": curr_step.stepInst,
                       "stepConfig": self.step_mapping[curr_step.stepSeq].stepConfig,
                       "traceback": traceback.format_exc(), "msg": str(e), "type": "format_error"})

                self.trace.add_error(error)
                raise error

            except Exception as e:

                error = WorkFlowExecError(
                    **{'tape_id': self.tape_schema.tape_id, 'tape_name': self.tape_schema.tape_name,
                       "stepSeq": curr_step.stepSeq, "stepLabel": curr_step.stepLabel, "stepInst": curr_step.stepInst,
                       "stepConfig": self.step_mapping[curr_step.stepSeq].stepConfig,
                       "traceback": traceback.format_exc(), "msg": str(e), "type": "other", })
                self.trace.add_error(error)
                raise error

        return True
