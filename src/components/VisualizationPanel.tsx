import React from 'react';
import type { ExecutionStep } from '../types';

interface VisualizationPanelProps {
  data: {
    steps: ExecutionStep[];
    finalResult: any;
    success: boolean;
    error?: string;
  } | null;
}

const VisualizationPanel: React.FC<VisualizationPanelProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <p>点击"生成可视化"按钮开始分析您的递归代码</p>
        </div>
      </div>
    );
  }

  if (!data.success) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center mb-3">
          <div className="text-red-600 text-xl mr-2">❌</div>
          <h3 className="text-lg font-semibold text-red-800">执行失败</h3>
        </div>
        <p className="text-red-700">{data.error || '未知错误'}</p>
      </div>
    );
  }

  if (data.steps.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-center mb-3">
          <div className="text-yellow-600 text-xl mr-2">⚠️</div>
          <h3 className="text-lg font-semibold text-yellow-800">没有找到匹配的步骤</h3>
        </div>
        <p className="text-yellow-700">
          请检查您的步骤编号标记是否与代码匹配。确保代码片段能够准确匹配到您的Python代码中的相应语句。
        </p>
      </div>
    );
  }

  // 按深度分组步骤
  const groupedSteps = data.steps.reduce((acc, step) => {
    if (!acc[step.depth]) {
      acc[step.depth] = {};
    }
    if (!acc[step.depth][step.function_call]) {
      acc[step.depth][step.function_call] = { step1: null, step2: [] };
    }
    
    if (step.step_number === 1) {
      acc[step.depth][step.function_call].step1 = step;
    } else if (step.step_number === 2) {
      acc[step.depth][step.function_call].step2.push(step);
    }
    
    return acc;
  }, {} as Record<number, Record<string, { step1: ExecutionStep | null; step2: ExecutionStep[] }>>);

  const maxDepth = Math.max(...Object.keys(groupedSteps).map(Number));

  return (
    <div className="space-y-6">
      {/* 最终结果 */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center mb-2">
          <div className="text-green-600 text-xl mr-2">✅</div>
          <h3 className="text-lg font-semibold text-green-800">最终结果</h3>
        </div>
        <p className="text-green-700 text-lg font-mono">
          {JSON.stringify(data.finalResult)}
        </p>
      </div>

      {/* 执行过程可视化 */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">递归执行过程（缩进编号法）</h3>
        
        {/* 表头 */}
        <div className="grid grid-cols-3 gap-4 mb-4 pb-2 border-b border-gray-300 font-semibold text-gray-700">
          <div>函数调用</div>
          <div className="text-center">步骤1</div>
          <div className="text-center">步骤2</div>
        </div>

        {/* 可视化内容 */}
        <div className="space-y-2">
          {Object.keys(groupedSteps)
            .map(Number)
            .sort((a, b) => a - b)
            .map(depth => {
              return Object.entries(groupedSteps[depth]).map(([functionCall, steps]) => {
                const step1 = steps.step1;
                const step2List = steps.step2;
                
                // 找到递归调用步骤和回归结果步骤
                const recursiveCall = step2List.find(s => !s.status.includes('='));
                const returnResult = step2List.find(s => s.status.includes('='));
                
                return (
                  <div 
                    key={`${depth}-${functionCall}`}
                    className="grid grid-cols-3 gap-4 py-3 hover:bg-gray-100 rounded border-l-4 border-transparent hover:border-blue-300"
                    style={{ marginLeft: `${depth * 20}px` }}
                  >
                    {/* 函数调用 */}
                    <div className="font-mono text-sm font-semibold">
                      {functionCall}
                    </div>

                    {/* 步骤1状态 */}
                    <div className="text-center">
                      {step1 && (
                        <span className="text-xl">
                          {step1.status === '✅' ? '✅' : 
                           step1.status === '❌' ? '❌' : ''}
                        </span>
                      )}
                    </div>

                    {/* 步骤2：递出和回归在同一个单元格中分层显示 */}
                    <div className="text-center">
                      <div className="space-y-2">
                        {/* 递出调用 */}
                        {recursiveCall && (
                          <div className="bg-blue-50 px-3 py-2 rounded border border-blue-200 recursive-call shadow-sm">
                            <span className="text-sm font-mono text-blue-700 font-semibold">
                              {recursiveCall.status}
                            </span>
                            <div className="text-xs text-blue-500 mt-1">递出调用</div>
                          </div>
                        )}
                        {/* 回归计算 */}
                        {returnResult && (
                          <div className="bg-green-50 px-3 py-2 rounded border border-green-200 return-result shadow-sm">
                            <span className="text-sm font-mono text-green-700 font-semibold">
                              {returnResult.status}
                            </span>
                            <div className="text-xs text-green-500 mt-1">回归计算</div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              });
            }).flat()}
        </div>

        {/* 图例 */}
        <div className="mt-6 pt-4 border-t border-gray-300">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">图例说明</h4>
          <div className="grid grid-cols-2 gap-6 text-sm text-gray-600">
            <div>
              <h5 className="font-semibold mb-2 text-gray-700">步骤状态标记</h5>
              <div className="flex items-center space-x-1 mb-1">
                <span className="text-xl">✅</span>
                <span>条件满足/到达基本情况</span>
              </div>
              <div className="flex items-center space-x-1">
                <span className="text-xl">❌</span>
                <span>条件不满足</span>
              </div>
            </div>
            <div>
              <h5 className="font-semibold mb-2 text-gray-700">递归阶段区分</h5>
              <div className="flex items-center space-x-1 mb-1">
                <div className="bg-blue-50 border border-blue-200 px-2 py-1 rounded">
                  <span className="text-blue-700 font-mono text-xs">n * factorial(n-1)</span>
                </div>
                <span>递出调用</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="bg-green-50 border border-green-200 px-2 py-1 rounded">
                  <span className="text-green-700 font-mono text-xs">n * result = value</span>
                </div>
                <span>回归计算</span>
              </div>
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            • 同一函数调用的递出和回归过程在步骤2列中垂直堆叠显示<br/>
            • 递出阶段：函数调用向更深层级递进；回归阶段：从深层级返回并计算结果
          </div>
        </div>
      </div>

      {/* 详细步骤信息 */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">详细执行步骤</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {data.steps.map((step, index) => {
            const isReturnStep = step.status.includes('=');
            const isRecursiveCall = step.status.includes('*') && !step.status.includes('=');
            
            return (
              <div 
                key={index} 
                className="flex items-center space-x-3 p-2 bg-gray-50 rounded text-sm"
                style={{ marginLeft: `${step.depth * 16}px` }}
              >
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded font-medium min-w-1-5rem text-center">
                  {step.step_number}
                </span>
                <span className="font-mono flex-1">{step.function_call}</span>
                <span className={`text-sm ${
                  isReturnStep ? 'text-green-600 font-semibold' :
                  isRecursiveCall ? 'text-blue-600' :
                  step.status === '✅' ? 'text-green-600' :
                  step.status === '❌' ? 'text-red-600' : ''
                }`}>
                  {step.status}
                </span>
                {step.result !== undefined && (
                  <span className="font-mono text-green-600 font-semibold">
                    → {JSON.stringify(step.result)}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default VisualizationPanel;