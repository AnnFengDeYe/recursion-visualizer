"""
递归算法可视化追踪器 - 修复版本
支持缩进编号法的可视化展示
"""

import ast
import re
import textwrap
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionStep:
    step_number: int
    function_call: str
    args: List[Any]
    depth: int
    status: str
    result: Any
    phase: str  # 'entry' or 'return'
    call_id: str


class HierarchicalRecursionTracer:
    def __init__(self, step_annotations: Dict[int, str], function_name: Optional[str] = None):
        self.step_annotations = step_annotations
        self.function_name = function_name
        self.steps: List[ExecutionStep] = []
        self.call_counter = 0
        self.call_stack = []
        self.param_names = []
        
    def execute_and_trace(self, code: str, function_name: str, args: List[Any]) -> Dict[str, Any]:
        """执行代码并进行追踪"""
        try:
            self.function_name = function_name
            self.steps = []
            self.call_counter = 0
            self.call_stack = []
            
            # 提取参数名
            self._extract_param_names(code)
            
            # 创建全局环境
            global_env = {'_tracer': self}
            
            # 添加instrumented代码
            instrumented_code = self._instrument_function(code)
            
            # 执行代码
            exec(instrumented_code, global_env)
            
            # 调用函数
            if function_name in global_env:
                function = global_env[function_name]
                final_result = function(*args)
            else:
                raise ValueError(f"Function {function_name} not found")
            
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
        pattern = f'def\\s+{self.function_name}\\s*\\(([^)]+)\\)'
        match = re.search(pattern, code)
        if match:
            param_str = match.group(1).strip()
            params = [p.split('=')[0].strip() for p in param_str.split(',') if p.strip()]
            self.param_names = params
        else:
            self.param_names = ['n']
    
    def _instrument_function(self, code: str) -> str:
        """为函数添加追踪逻辑"""
        lines = code.split('\n')
        modified_lines = []
        
        for i, line in enumerate(lines):
            modified_lines.append(line)
            
            # 检查是否是函数定义行
            if line.strip().startswith(f'def {self.function_name}'):
                indent = len(line) - len(line.lstrip()) + 4
                entry_trace = ' ' * indent + "_tracer.trace_function_entry(locals())"
                modified_lines.append(entry_trace)
            
            # 检查是否是if语句（步骤1）
            elif "if" in line and any(step_code.strip() in line.strip() for step_code in self.step_annotations.values() if "if" in step_code):
                # 在if条件判断后添加追踪
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    indent = len(next_line) - len(next_line.lstrip())
                    main_param = self.param_names[0] if self.param_names else 'n'
                    trace_call = f' ' * indent + f"_tracer.trace_step(1, {main_param}, True)"
                    modified_lines.append(trace_call)
                    
                    # 处理else分支
                    for j in range(i + 1, len(lines)):
                        check_line = lines[j].strip()
                        if check_line.startswith('else:'):
                            else_indent = len(lines[j]) - len(lines[j].lstrip()) + 4
                            trace_call_false = f' ' * else_indent + f"_tracer.trace_step(1, {main_param}, False)"
                            lines.insert(j + 1, trace_call_false)
                            break
                        elif "return" in check_line and self.function_name and self.function_name in check_line:
                            return_indent = len(lines[j]) - len(lines[j].lstrip())
                            trace_call_false = f' ' * return_indent + f"_tracer.trace_step(1, {main_param}, False)"
                            lines.insert(j, trace_call_false)
                            break
            
            # 检查是否是递归return语句（步骤2）
            elif "return" in line and self.function_name and self.function_name in line:
                indent = len(line) - len(line.lstrip())
                main_param = self.param_names[0] if self.param_names else 'n'
                
                # 在return之前添加步骤2追踪
                trace_call = f' ' * indent + f"_tracer.trace_step(2, {main_param}, None)"
                modified_lines.insert(-1, trace_call)
                
                # 修改return语句，使其通过tracer返回
                original_return = modified_lines[-1]
                wrapped_return = re.sub(
                    f'return\\s+(.+)',
                    f'return _tracer.trace_return(\\1, {main_param})',
                    original_return
                )
                modified_lines[-1] = wrapped_return
        
        return '\n'.join(modified_lines)
    
    def trace_function_entry(self, local_vars: Dict[str, Any]):
        """追踪函数调用入口"""
        args = []
        for param_name in self.param_names:
            args.append(local_vars.get(param_name, 'unknown'))
        
        self.call_counter += 1
        call_id = f"call_{self.call_counter}"
        
        call_info = {
            'call_id': call_id,
            'args': args,
            'depth': len(self.call_stack)
        }
        self.call_stack.append(call_info)
    
    def trace_step(self, step_number: int, arg_value: Any, condition_result: Optional[bool]):
        """追踪执行步骤"""
        if not self.call_stack:
            return
            
        current_call = self.call_stack[-1]
        depth = current_call['depth']
        args = current_call['args']
        call_id = current_call['call_id']
        
        if step_number == 1:  # 基本情况检查
            if condition_result is True:
                status = "✅"
                result = arg_value
            else:
                status = "❌"
                result = None
        else:  # 递归情况
            step_annotation = self.step_annotations.get(2, "")
            if "fibonacci" in step_annotation or "+" in step_annotation:
                status = f"{self.function_name}({arg_value - 1}) + {self.function_name}({arg_value - 2})"
            elif "*" in step_annotation:
                status = f"{arg_value} * {self.function_name}({arg_value - 1})"
            else:
                status = step_annotation
                if self.param_names:
                    main_param = self.param_names[0]
                    status = re.sub(f'\\b{main_param}\\b', str(arg_value), status)
                    status = re.sub(f'\\b{main_param}\\s*-\\s*(\\d+)\\b', 
                                  lambda m: str(arg_value - int(m.group(1))), status)
            result = None
            
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
    
    def trace_return(self, return_value: Any, current_n: int) -> Any:
        """追踪函数返回值"""
        if not self.call_stack:
            return return_value
            
        current_call = self.call_stack.pop()  # 弹出当前调用
        depth = current_call['depth']
        call_id = current_call['call_id']
        
        # 如果是基本情况（n <= 1），直接返回
        step_annotation = self.step_annotations.get(2, "")
        if "*" in step_annotation:
            # 阶乘类型
            status = f"= {return_value}"
        else:
            # 其他类型
            status = f"= {return_value}"
        
        function_call = f"{self.function_name}({current_n})"
        
        step = ExecutionStep(
            step_number=2,
            function_call=function_call,
            args=[current_n],
            depth=depth,
            status=status,
            result=return_value,
            phase="return",
            call_id=call_id
        )
        
        self.steps.append(step)
        
        return return_value


def test_tracer():
    """测试追踪器"""
    print("测试阶乘函数:")
    factorial_code = '''
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)
'''
    
    step_annotations = {
        1: "if n <= 1:",
        2: "return n * factorial(n - 1)"
    }
    
    tracer = HierarchicalRecursionTracer(step_annotations)
    result = tracer.execute_and_trace(factorial_code, "factorial", [4])
    
    print("追踪结果:")
    for step in result["steps"]:
        print(f"  步骤 {step['step_number']}: {step['function_call']} -> {step['status']}")
    print(f"最终结果: {result['final_result']}")
    print(f"成功: {result['success']}")
    
    print("\n" + "="*50 + "\n")
    
    print("测试斐波那契函数:")
    fibonacci_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)
'''
    
    fib_annotations = {
        1: "if n <= 1:",
        2: "return fibonacci(n - 1) + fibonacci(n - 2)"
    }
    
    tracer2 = HierarchicalRecursionTracer(fib_annotations)
    result2 = tracer2.execute_and_trace(fibonacci_code, "fibonacci", [3])
    
    print("追踪结果:")
    for step in result2["steps"]:
        print(f"  步骤 {step['step_number']}: {step['function_call']} -> {step['status']}")
    print(f"最终结果: {result2['final_result']}")
    print(f"成功: {result2['success']}")


if __name__ == "__main__":
    test_tracer()