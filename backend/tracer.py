#!/usr/bin/env python3
"""
递归算法可视化追踪器
实现缩进编号法的递归执行过程可视化
"""

import ast
import sys
import traceback
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import re


@dataclass
class ExecutionStep:
    """执行步骤数据类"""
    step_number: int
    function_call: str
    args: List[Any]
    depth: int
    status: str  # "✅", "❌", "递归表达式", "回归结果"
    result: Optional[Any] = None
    phase: str = "entry"  # "entry" 或 "return"
    call_id: str = ""  # 用于标识同一个函数调用


class HierarchicalRecursionTracer:
    """层次化递归追踪器 - 实现缩进编号法可视化"""
    
    def __init__(self, step_annotations: Dict[int, str]):
        """
        初始化追踪器
        
        Args:
            step_annotations: 步骤编号到代码片段的映射
        """
        self.step_annotations = step_annotations
        self.steps: List[ExecutionStep] = []
        self.call_stack: List[Dict[str, Any]] = []  # 调用栈
        self.function_name = ""
        self.param_names = []  # 存储函数参数名
        self.call_counter = 0  # 用于生成唯一的调用ID
        
    def execute_and_trace(self, code: str, function_name: str, args: List[Any]) -> Dict[str, Any]:
        """
        执行代码并生成层次化追踪数据
        
        Args:
            code: Python源代码
            function_name: 要执行的函数名
            args: 函数参数
            
        Returns:
            包含步骤和结果的字典
        """
        self.function_name = function_name
        self.steps = []
        self.call_stack = []
        self.call_counter = 0
        
        # 提取函数参数名
        self._extract_param_names(code)
        
        try:
            # 创建执行环境，注入追踪器
            exec_globals = {
                '__builtins__': __builtins__,
                '_tracer': self
            }
            
            # 修改代码，添加追踪调用
            modified_code = self._instrument_function(code)
            
            # 执行修改后的代码
            exec(modified_code, exec_globals)
            
            # 获取并执行目标函数
            target_function = exec_globals[function_name]
            final_result = target_function(*args)
            
            return {
                "steps": [asdict(step) for step in self.steps],
                "final_result": final_result,
                "success": True
            }
            
        except Exception as e:
            return {
                "steps": [asdict(step) for step in self.steps],
                "final_result": None,
                "success": False,
                "error": str(e)
            }
    
    def _extract_param_names(self, code: str):
        """提取函数参数名"""
        # 查找函数定义行
        pattern = f'def\\s+{self.function_name}\\s*\\(([^)]+)\\)'
        match = re.search(pattern, code)
        if match:
            param_str = match.group(1).strip()
            # 解析参数，去除空白和默认值
            params = [p.split('=')[0].strip() for p in param_str.split(',') if p.strip()]
            self.param_names = params
        else:
            self.param_names = ['n']  # 默认参数名
    
    def _instrument_function(self, code: str) -> str:
        """
        为函数添加追踪逻辑
        """
        lines = code.split('\n')
        modified_lines = []
        
        for i, line in enumerate(lines):
            # 先添加原始行
            modified_lines.append(line)
            
            # 检查是否是函数定义行
            if line.strip().startswith(f'def {self.function_name}'):
                # 在函数开始后添加函数调用追踪
                indent = len(line) - len(line.lstrip()) + 4
                entry_trace = ' ' * indent + "_tracer.trace_function_entry(locals())"
                modified_lines.append(entry_trace)
            
            # 检查是否是if语句（步骤1）
            elif "if" in line and any(step_code.strip() in line.strip() for step_code in self.step_annotations.values() if "if" in step_code):
                # 在if语句后添加条件检查追踪
                if i + 1 < len(lines):  # 确保有下一行
                    next_line = lines[i + 1]
                    indent = len(next_line) - len(next_line.lstrip())
                    # 在条件满足的分支中添加追踪
                    main_param = self.param_names[0] if self.param_names else 'n'
                    trace_call = f' ' * indent + f"_tracer.trace_step(1, {main_param}, True)  # 条件满足"
                    modified_lines.append(trace_call)
                    
                    # 查找 else 分支，添加条件不满足的追踪
                    for j in range(i + 1, len(lines)):
                        check_line = lines[j].strip()
                        if check_line.startswith('else:'):
                            # 在else分支中添加追踪
                            else_indent = len(lines[j]) - len(lines[j].lstrip()) + 4
                            trace_call_false = f' ' * else_indent + f"_tracer.trace_step(1, {main_param}, False)  # 条件不满足"
                            lines.insert(j + 1, trace_call_false)
                            break
                        elif "return" in check_line and any(fname in check_line for fname in [self.function_name]):
                            # 如果没有显式else，但有递归return语句
                            return_indent = len(lines[j]) - len(lines[j].lstrip())
                            trace_call_false = f' ' * return_indent + f"_tracer.trace_step(1, {main_param}, False)  # 条件不满足"
                            lines.insert(j, trace_call_false)
                            break
            
            # 检查是否是递归return语句（步骤2）
            elif "return" in line and self.function_name in line and any(step_code.strip() in line.strip() for step_code in self.step_annotations.values() if "return" in step_code):
                indent = len(line) - len(line.lstrip())
                main_param = self.param_names[0] if self.param_names else 'n'
                # 在return之前添加递归调用追踪
                trace_call = f' ' * indent + f"_tracer.trace_step(2, {main_param}, None)"
                modified_lines.insert(-1, trace_call)  # 在return之前插入
                
                # 修改return语句，包装递归调用以追踪返回值
                original_return = modified_lines[-1]
                # 处理可能的多个递归调用（如斐波那契数列）
                wrapped_return = original_return
                
                # 查找所有递归调用并包装
                pattern = f'{self.function_name}\\([^)]+\\)'
                matches = re.findall(pattern, original_return)
                for match in matches:
                    wrapped_call = f"_tracer.trace_recursive_call({match}, {main_param})"
                    wrapped_return = wrapped_return.replace(match, wrapped_call)
                modified_lines[-1] = wrapped_return
        
        return '\n'.join(modified_lines)
    
    def trace_function_entry(self, local_vars: Dict[str, Any]):
        """追踪函数调用入口"""
        # 获取函数参数
        args = []
        for param_name in self.param_names:
            args.append(local_vars.get(param_name, 'unknown'))
        
        # 生成唯一调用ID
        self.call_counter += 1
        call_id = f"call_{self.call_counter}"
        
        # 压入调用栈
        call_info = {
            'call_id': call_id,
            'args': args,
            'depth': len(self.call_stack)
        }
        self.call_stack.append(call_info)
    
    def trace_step(self, step_number: int, arg_value: Any, condition_result: Optional[bool]):
        """追踪执行步骤"""
        if not self.call_stack:
            return  # 如果调用栈为空，不记录步骤
            
        current_call = self.call_stack[-1]
        depth = current_call['depth']
        args = current_call['args']
        call_id = current_call['call_id']
        
        # 根据步骤类型和结果确定状态
        if step_number == 1:  # 基本情况检查
            if condition_result is True:  # 条件满足
                status = "✅"  # 条件满足
                result = arg_value  # 返回对应的值
            else:  # 条件不满足
                status = "❌"  # 条件不满足
                result = None
        else:  # 递归情况
            # 步骤2显示具体的递归表达式
            step_annotation = self.step_annotations.get(2, "")
            if "fibonacci" in step_annotation or "+" in step_annotation:
                # 斐波那契类型：包含加法的递归
                status = f"{self.function_name}({arg_value - 1}) + {self.function_name}({arg_value - 2})"
            elif "*" in step_annotation:
                # 阶乘类型：包含乘法的递归
                status = f"{arg_value} * {self.function_name}({arg_value - 1})"
            else:
                # 通用情况：直接显示注释内容，并替换参数
                status = step_annotation
                # 替换主要参数名为具体数值
                if self.param_names:
                    main_param = self.param_names[0]
                    status = re.sub(f'\\b{main_param}\\b', str(arg_value), status)
                    # 替换 param-1, param-2 等表达式
                    status = re.sub(f'\\b{main_param}\\s*-\\s*(\\d+)\\b', lambda m: str(arg_value - int(m.group(1))), status)
            result = None
            
        # 生成函数调用显示
        if len(args) > 1:
            args_str = ', '.join(map(str, args))
            function_call = f"{self.function_name}({args_str})"
        else:
            function_call = f"{self.function_name}({arg_value})"
            
        step = ExecutionStep(
            step_number=step_number,
            function_call=function_call,
            args=args,
            depth=depth,
            status=status,
            result=result,
            phase="entry",
            call_id=call_id
        )
        
        self.steps.append(step)
    
    def trace_recursive_call(self, result: Any, current_n: int) -> Any:
        """追踪递归调用的返回值（回归过程）"""
        if not self.call_stack:
            return result  # 如果调用栈为空，直接返回结果
            
        # 找到需要记录返回结果的父调用
        # 这里的父调用是那个发起递归调用的函数
        # 我们需要在调用栈中找到那个正在等待 current_n 返回值的调用
        parent_call = None
        
        # 遍历调用栈，找到那个包含对 current_n 调用的父函数
        for call in self.call_stack:
            # 检查这个调用是否可能会调用 current_n
            if call['args'] and len(call['args']) > 0:
                parent_n = call['args'][0]
                if isinstance(parent_n, int) and parent_n > current_n:
                    # 这个可能是父调用，因为它的参数比 current_n 大
                    parent_call = call
                    break
        
        if not parent_call:
            # 如果找不到父调用，使用最顶层的调用
            parent_call = self.call_stack[0] if self.call_stack else None
            
        if not parent_call:
            return result
            
        depth = parent_call['depth']
        call_id = parent_call['call_id']
        
        # 添加回归步骤
        step_annotation = self.step_annotations.get(2, "")
        if "+" in step_annotation:
            # 斐波那契类型：加法递归
            status = f"= {result}"
            final_result = result
        elif "*" in step_annotation:
            # 阶乘类型：乘法递归
            parent_n = parent_call['args'][0] if parent_call['args'] else current_n
            status = f"{parent_n} * {result} = {parent_n * result if isinstance(result, (int, float)) else result}"
            final_result = parent_n * result if isinstance(result, (int, float)) else result
        else:
            # 通用情况
            status = f"= {result}"
            final_result = result
            
        # 这里使用父调用的函数名和参数
        parent_args = parent_call['args']
        if len(parent_args) > 1:
            args_str = ', '.join(map(str, parent_args))
            function_call = f"{self.function_name}({args_str})"
        else:
            function_call = f"{self.function_name}({parent_args[0]})"
            
        step = ExecutionStep(
            step_number=2,
            function_call=function_call,
            args=parent_args,
            depth=depth,
            status=status,
            result=final_result,
            phase="return",
            call_id=call_id
        )
        
        self.steps.append(step)
        
        return result



def test_tracer():
    """测试追踪器"""
    code = '''
def factorial(n):
    if n == 1:
        return 1
    return n * factorial(n - 1)
'''
    
    step_annotations = {
        1: "if n == 1:",
        2: "return n * factorial(n - 1)"
    }
    
    tracer = HierarchicalRecursionTracer(step_annotations)
    result = tracer.execute_and_trace(code, "factorial", [3])
    
    print("追踪结果:")
    for step in result["steps"]:
        print(f"  步骤 {step['step_number']}: {step['function_call']} -> {step['status']}")
    print(f"最终结果: {result['final_result']}")


if __name__ == "__main__":
    test_tracer()