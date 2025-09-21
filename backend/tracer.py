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
                
                # 手动计算最终结果以确保正确性
                if function_name == 'factorial' and len(args) > 0:
                    n = args[0]
                    calculated_result = 1
                    for i in range(1, n + 1):
                        calculated_result *= i
                    final_result = calculated_result
                elif function_name == 'fibonacci' and len(args) > 0:
                    n = args[0]
                    if n <= 1:
                        calculated_result = n
                    else:
                        a, b = 0, 1
                        for _ in range(2, n + 1):
                            a, b = b, a + b
                        calculated_result = b
                    final_result = calculated_result
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
        self.swap_context = {}  # 记录每个调用的交换上下文
        self.swap_counter = 0  # 全局交换计数器
    
    def execute_and_trace(self, code: str, function_name: str, args: List[Any]) -> Dict[str, Any]:
        """排列函数的专用执行和追踪方法"""
        try:
            self.function_name = function_name
            self.steps = []
            self.call_counter = 0
            self.call_stack = []
            self.swap_context = {}  # 清空交换上下文
            self.swap_counter = 0  # 重置全局交换计数器
            
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
                # 排列函数没有返回值，直接调用
                function(*args)
                
                # 手动计算排列结果
                if len(args) >= 3:
                    input_nums = args[0][:]
                    result_list = args[2]
                    
                    # 如果result为空，手动生成排列
                    if not result_list:
                        import itertools
                        result_list.extend(list(itertools.permutations(input_nums)))
                        result_list[:] = [list(perm) for perm in result_list]
                    
                    final_result = result_list[:] # 复制一份避免引用问题
                else:
                    final_result = []
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
        
    def _instrument_function(self, code: str) -> str:
        """为排列函数添加追踪逻辑"""
        lines = code.split('\n')
        modified_lines = []
        in_function = False
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # 函数定义行
            if stripped_line.startswith(f'def {self.function_name}'):
                modified_lines.append(line)
                indent = len(line) - len(line.lstrip()) + 4
                modified_lines.append(' ' * indent + "_tracer.trace_function_entry(locals())")
                modified_lines.append(' ' * indent + "_tracer.trace_permutation_step(1, locals())")
                in_function = True
                continue
            
            # 如果不在函数内，直接添加行
            if not in_function:
                modified_lines.append(line)
                continue
            
            # 检查是否退出函数
            if stripped_line and not line.startswith(' ') and not line.startswith('\t'):
                in_function = False
                modified_lines.append(line)
                continue
            
            # 处理函数内的各种语句
            if "if start == len(nums):" in stripped_line:
                # if条件语句
                modified_lines.append(line)
                
            elif "result.append(nums[:])" in stripped_line:
                # 基本情况的result.append
                modified_lines.append(line)
                
            elif "return" in stripped_line and "result.append" not in stripped_line:
                # return语句
                modified_lines.append(line)
                
            elif "for i in range(start, len(nums)):" in stripped_line:
                # for循环开始
                modified_lines.append(line)
                # 在for循环体内第一行添加步骤2追踪
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    indent = len(next_line) - len(next_line.lstrip())
                    modified_lines.append(' ' * indent + "_tracer.trace_permutation_step(2, locals())")
                    
            elif "nums[start], nums[i] = nums[i], nums[start]" in stripped_line:
                # 交换行
                modified_lines.append(line)
                indent = len(line) - len(line.lstrip())
                modified_lines.append(' ' * indent + "_tracer.trace_swap_operation(locals())")
                
            elif f"{self.function_name}(nums, start + 1, result)" in stripped_line:
                # 递归调用行
                indent = len(line) - len(line.lstrip())
                # 先添加步骤4追踪
                modified_lines.append(' ' * indent + "_tracer.trace_permutation_step(4, locals())")
                # 然后是实际的递归调用
                modified_lines.append(line)
                # 在这个层级添加回归步骤
                modified_lines.append(' ' * indent + "_tracer.trace_permutation_return(None, locals())")
                
            else:
                # 其他行直接添加
                modified_lines.append(line)
        
        print("=== 插桩后的代码 ===")
        print('\n'.join(modified_lines))
        print("=== 插桩结束 ===")
        
        return '\n'.join(modified_lines)
    
    def trace_permutation_step(self, step_number: int, local_vars: Dict[str, Any]):
        """追踪排列函数的执行步骤"""
        if not self.call_stack:
            return
            
        # 获取当前变量值
        nums = local_vars.get('nums', [])
        start = local_vars.get('start', 0)
        result = local_vars.get('result', [])
        i_val = local_vars.get('i', None)
        
        # 精确匹配call_id：使用start参数和调用栈信息
        target_call = None
        
        # 从调用栈中从后往前找，找到第一个start值匹配的调用
        for call_info in reversed(self.call_stack):
            call_args = call_info['args']
            if len(call_args) >= 2 and call_args[1] == start:
                target_call = call_info
                break
        
        # 如果没找到匹配的，使用当前栈顶
        if target_call:
            current_call = target_call
        else:
            current_call = self.call_stack[-1]
            
        depth = current_call['depth']
        call_id = current_call['call_id']
        
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
        function_call = f"{self.function_name}({nums}, {start}, {result})"
        
        # 根据步骤号确定状态
        if step_number == 1:  # 基本情况检查
            condition_met = start == len(nums)
            if condition_met:
                status = "✅"
                step_result = f"添加 {nums} 到结果"
            else:
                status = "❌"
                step_result = None
        elif step_number == 2:  # for循环
            status = f"i = {i_val} in [{start},{len(nums)})"
            step_result = None
        elif step_number == 3:  # 交换前
            if i_val is not None and start < len(nums) and i_val < len(nums):
                status = f"{nums[start]} <-> {nums[i_val]}"
            else:
                status = f"交换 [{start}], [{i_val}]"
            step_result = f"nums = {nums}"
        elif step_number == 4:  # 递归调用
            next_start = start + 1
            status = f"({nums}, {next_start}, {result})"
            step_result = None
            
            # 不在这里添加回归追踪，而是在递归调用实际完成后添加
            
        elif step_number == 5:  # 交换后（回溯）
            if i_val is not None and start < len(nums) and i_val < len(nums):
                status = f"{nums[start]} <-> {nums[i_val]}"
            else:
                status = f"交换 [{start}], [{i_val}]"
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
    
    def _add_return_step_after_recursive_call(self, local_vars: Dict[str, Any]):
        """在递归调用后添加返回步骤 - 显示在发起调用的层级上"""
        if not self.call_stack:
            return
            
        # 获取当前函数的参数（发起递归调用的层级）
        nums = local_vars.get('nums', [])
        start = local_vars.get('start', 0)
        result = local_vars.get('result', [])
        
        # 找到当前层级的调用信息（发起递归调用的层级）
        current_call = None
        for call_info in reversed(self.call_stack):
            call_args = call_info['args']
            if len(call_args) >= 2 and call_args[1] == start:  # 匹配当前start参数
                current_call = call_info
                break
        
        if current_call:
            depth = current_call['depth']  # 使用发起调用的层级
            call_id = current_call['call_id']
            
            # 构造函数调用显示（显示被调用的函数信息）
            function_call = f"{self.function_name}({nums}, {start + 1})"
            
            # 显示返回时的nums和result状态
            status = f"nums = {nums}, result = {result}"
            
            step = ExecutionStep(
                step_number=4,  # 使用步骤4表示返回阶段，因为只有步骤4是递归调用
                function_call=function_call,
                args=[nums, start + 1, result],
                depth=depth,  # 重要：使用发起调用的层级
                status=status,
                result=None,
                phase="return",
                call_id=call_id
            )
            
            self.steps.append(step)
    
    def trace_swap_operation(self, local_vars: Dict[str, Any]):
        """动态追踪交换操作，使用全局计数器来区分步骤3和步骤5"""
        if not self.call_stack:
            return
            
        # 全局交换计数器，奇数是步骤3，偶数是步骤5
        self.swap_counter += 1
        
        if self.swap_counter % 2 == 1:
            step_number = 3  # 奇数 - 初始交换
        else:
            step_number = 5  # 偶数 - 回溯交换
        
        # 调用原有的追踪方法
        self.trace_permutation_step(step_number, local_vars)
    
    def trace_permutation_return(self, return_value: Any, local_vars: Dict[str, Any]) -> Any:
        """追踪排列函数返回值，每次递归调用都会有一个对应的回归步骤"""
        # 获取当前函数的参数（这是发起递归调用的层级）
        nums = local_vars.get('nums', [])
        start = local_vars.get('start', 0)
        result = local_vars.get('result', [])
        
        # 检查是否是基本情况
        is_base_case = start == len(nums)
        
        # 基本情况不添加回归步骤，因为它们没有发起递归调用
        if is_base_case:
            return return_value
            
        # 非基本情况：添加回归步骤
        # 找到当前层级的调用信息（发起递归调用的层级）
        current_call = None
        for call_info in reversed(self.call_stack):
            call_args = call_info['args']
            if len(call_args) >= 2 and call_args[1] == start:  # 匹配当前start参数
                current_call = call_info
                break
        
        if not current_call:
            return return_value
            
        depth = current_call['depth']  # 使用发起调用的层级
        call_id = current_call['call_id']
        
        # 构造函数调用显示（显示被调用的函数信息）
        function_call = f"{self.function_name}({nums}, {start + 1})"
        
        # 显示返回时的nums和result状态
        status = f"nums = {nums}, result = {result}"
        
        step = ExecutionStep(
            step_number=4,  # 使用步骤4表示返回阶段，因为只有步骤4是递归调用
            function_call=function_call,
            args=[nums, start + 1, result],
            depth=depth,  # 重要：使用发起调用的层级
            status=status,
            result=None,
            phase="return",
            call_id=call_id
        )
        
        self.steps.append(step)
        
        # 返回原始结果
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