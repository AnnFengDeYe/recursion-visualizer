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
                
                # 修改return语句，使其通过tracer追踪结果
                original_return = modified_lines[-1]
                wrapped_return = re.sub(
                    f'return\\s+(.+)',
                    f'return _tracer.trace_return(\\1, {main_param})',
                    original_return
                )
                modified_lines[-1] = wrapped_return
            
            # 检查是否是简单return语句（基本情况）
            elif "return" in line and "return" in line.strip() and not (self.function_name and self.function_name in line):
                # 基本情况的return，直接追踪
                indent = len(line) - len(line.lstrip())
                main_param = self.param_names[0] if self.param_names else 'n'
                
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
        
        # 直接使用Python计算好的结果，不要再次计算
        final_result = return_value
        status = f"= {final_result}"
        
        function_call = f"{self.function_name}({current_n})"
        
        step = ExecutionStep(
            step_number=2,
            function_call=function_call,
            args=[current_n],
            depth=depth,
            status=status,
            result=final_result,
            phase="return",
            call_id=call_id
        )
        
        self.steps.append(step)
        
        # 返回原始结果，不要修改
        return return_value


class PermutationRecursionTracer(HierarchicalRecursionTracer):
    """专门用于排列函数的递归追踪器"""
    
    def __init__(self, step_annotations: Dict[int, str], function_name: Optional[str] = None):
        super().__init__(step_annotations, function_name)
        self.nums_states = []  # 记录nums数组的状态变化
        
    def _instrument_function(self, code: str) -> str:
        """为排列函数添加追踪逻辑"""
        lines = code.split('\n')
        modified_lines = []
        
        for i, line in enumerate(lines):
            modified_lines.append(line)
            
            # 检查是否是函数定义行
            if line.strip().startswith(f'def {self.function_name}'):
                indent = len(line) - len(line.lstrip()) + 4
                entry_trace = ' ' * indent + "_tracer.trace_function_entry(locals())"
                modified_lines.append(entry_trace)
                # 在函数入口处直接检查步骤1
                step1_trace = ' ' * indent + "_tracer.trace_permutation_step(1, locals())"
                modified_lines.append(step1_trace)
            
            # 步骤2: for循环开始
            elif "for i in range(start, len(nums))" in line:
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    indent = len(next_line) - len(next_line.lstrip())
                    trace_call = f' ' * indent + "_tracer.trace_permutation_step(2, locals())"
                    modified_lines.append(trace_call)
            
            # 步骤3: 交换前
            elif "nums[start], nums[i] = nums[i], nums[start]" in line:
                # 检查是否是第一次出现（交换前）还是第二次（回溯）
                is_backtrack = False
                # 查找上一行是否有递归调用
                for j in range(i-1, max(0, i-5), -1):
                    if self.function_name and self.function_name in lines[j]:
                        is_backtrack = True
                        break
                
                indent = len(line) - len(line.lstrip())
                if is_backtrack:
                    trace_call = f' ' * indent + "_tracer.trace_permutation_step(5, locals())"
                else:
                    trace_call = f' ' * indent + "_tracer.trace_permutation_step(3, locals())"
                modified_lines.insert(-1, trace_call)
            
            # 步骤4: 递归调用
            elif f"{self.function_name}(nums, start + 1, result)" in line:
                indent = len(line) - len(line.lstrip())
                trace_call = f' ' * indent + "_tracer.trace_permutation_step(4, locals())"
                modified_lines.insert(-1, trace_call)
                # 在递归调用后添加返回追踪
                return_trace = f' ' * indent + "_tracer.trace_permutation_return(locals())"
                modified_lines.append(return_trace)
        
        return '\n'.join(modified_lines)
    
    def trace_permutation_step(self, step_number: int, local_vars: Dict[str, Any]):
        """追踪排列函数的执行步骤"""
        if not self.call_stack:
            return
            
        current_call = self.call_stack[-1]
        depth = current_call['depth']
        call_id = current_call['call_id']
        
        # 获取当前函数的参数
        nums = local_vars.get('nums', [])
        start = local_vars.get('start', 0)
        result = local_vars.get('result', [])
        i_val = local_vars.get('i', None)
        
        # 记录nums状态
        nums_copy = nums[:] if nums else []
        self.nums_states.append({
            'step': step_number,
            'nums': nums_copy,
            'start': start,
            'i': i_val,
            'depth': depth
        })
        
        # 构造函数调用显示
        function_call = f"{self.function_name}({nums}, {start}, {len(result)}个结果)"
        
        # 根据步骤号确定状态
        if step_number == 1:  # 基本情况检查
            condition_met = start == len(nums)
            if condition_met:
                status = "✅ 达到边界，添加排列"
                step_result = f"添加 {nums} 到结果"
            else:
                status = "❌ 条件不满足，继续递归"
                step_result = None
        elif step_number == 2:  # for循环
            status = f"循环 i={i_val}, 范围[{start}, {len(nums)})"
            step_result = None
        elif step_number == 3:  # 交换前
            status = f"交换 nums[{start}]={nums[start]} 和 nums[{i_val}]={nums[i_val] if i_val is not None and i_val < len(nums) else 'N/A'}"
            step_result = f"nums = {nums}"
        elif step_number == 4:  # 递归调用
            status = f"递归调用 start={start+1}"
            step_result = None
        elif step_number == 5:  # 交换后（回溯）
            status = f"回溯交换 nums[{start}] 和 nums[{i_val}]"
            step_result = f"nums = {nums}"
        else:
            status = "未知步骤"
            step_result = None
            
        step = ExecutionStep(
            step_number=step_number,
            function_call=function_call,
            args=[nums, start, result],
            depth=depth,
            status=status,
            result=step_result,
            phase="entry",
            call_id=call_id
        )
        
        self.steps.append(step)
    
    def trace_permutation_return(self, local_vars: Dict[str, Any]):
        """追踪排列函数的返回阶段，显示nums状态"""
        if not self.call_stack:
            return
            
        current_call = self.call_stack[-1]
        depth = current_call['depth']
        call_id = current_call['call_id']
        
        # 获取当前函数的参数
        nums = local_vars.get('nums', [])
        start = local_vars.get('start', 0)
        result = local_vars.get('result', [])
        
        # 构造函数调用显示
        function_call = f"{self.function_name}({nums}, {start}, {len(result)}个结果)"
        
        # 显示返回时的nums状态
        status = f"返回 nums = {nums}"
        step_result = f"当前排列状态: {nums}"
            
        step = ExecutionStep(
            step_number=6,  # 用步骤6表示返回阶段
            function_call=function_call,
            args=[nums, start, result],
            depth=depth,
            status=status,
            result=step_result,
            phase="return",
            call_id=call_id
        )
        
        self.steps.append(step)


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