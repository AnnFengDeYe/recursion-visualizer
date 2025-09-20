// 类型定义文件
export interface ExecutionStep {
  step_number: number;
  function_call: string;
  args: any[];
  depth: number;
  status: string; // "✅", "❌", "递归表达式", "回归结果"
  result?: any;
  phase: string; // "entry" 或 "return"
  call_id: string; // 用于标识同一个函数调用
}

export interface VisualizationResult {
  steps: ExecutionStep[];
  final_result: any;
  success: boolean;
  error?: string;
}

export interface StepAnnotation {
  [stepNumber: number]: string;
}