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

interface CallGroup {
  call_id: string;
  function_call: string;
  depth: number;
  step1?: ExecutionStep;
  step2_entries: ExecutionStep[];
  step2_returns: ExecutionStep[];
}

const HierarchicalVisualizationPanel: React.FC<VisualizationPanelProps> = ({ data }) => {
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

  // 按调用ID分组步骤
  const callGroups: { [key: string]: CallGroup } = {};
  
  data.steps.forEach(step => {
    const callId = step.call_id || `${step.function_call}_${step.depth}`;
    
    if (!callGroups[callId]) {
      callGroups[callId] = {
        call_id: callId,
        function_call: step.function_call,
        depth: step.depth,
        step1: undefined,
        step2_entries: [],
        step2_returns: []
      };
    }
    
    if (step.step_number === 1) {
      callGroups[callId].step1 = step;
    } else if (step.step_number === 2) {
      if (step.phase === 'entry') {
        callGroups[callId].step2_entries.push(step);
      } else {
        callGroups[callId].step2_returns.push(step);
      }
    }
  });

  // 按执行顺序排序调用组
  const sortedCallGroups = Object.values(callGroups).sort((a, b) => {
    // 按第一个步骤的出现顺序排序
    const aFirstStep = data.steps.find(s => s.call_id === a.call_id);
    const bFirstStep = data.steps.find(s => s.call_id === b.call_id);
    return data.steps.indexOf(aFirstStep!) - data.steps.indexOf(bFirstStep!);
  });

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

      {/* 递归执行过程可视化 */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">递归执行过程（缩进编号法）</h3>
        
        {(() => {
          const maxSteps = Math.max(...data.steps.map(s => s.step_number));
          const isPermutationFunction = maxSteps > 2; // 排列函数有5个步骤
          
          if (isPermutationFunction) {
            // 排列函数专用布局 - 更宽的列和更大的间距
            return (
              <div className="overflow-x-auto">
                {/* 表头 */}
                <div className="grid gap-6 mb-6 pb-3 border-b border-gray-300 font-semibold text-gray-700" style={{
                  gridTemplateColumns: `100px 300px repeat(${maxSteps}, minmax(200px, 1fr))`,
                  minWidth: `${600 + maxSteps * 200}px`
                }}>
                  <div className="text-center">层级</div>
                  <div>函数调用</div>
                  {Array.from({length: maxSteps}, (_, i) => (
                    <div key={i} className="text-center font-medium">步骤{i + 1}</div>
                  ))}
                </div>

                {/* 排列函数行显示 */}
                <div className="space-y-3">
                  {sortedCallGroups.map(group => {
                    const stepsByNumber: { [key: number]: ExecutionStep[] } = {};
                    
                    // 按步骤编号分组该函数的所有步骤
                    [...group.step2_entries, ...group.step2_returns].forEach(step => {
                      if (!stepsByNumber[step.step_number]) {
                        stepsByNumber[step.step_number] = [];
                      }
                      stepsByNumber[step.step_number].push(step);
                    });
                    if (group.step1) {
                      stepsByNumber[1] = [group.step1];
                    }
                    
                    return (
                      <div 
                        key={group.call_id} 
                        className="grid gap-6 py-4 px-4 hover:bg-gray-100 rounded-lg border-l-4 border-transparent hover:border-blue-300 transition-colors"
                        style={{
                          gridTemplateColumns: `100px 300px repeat(${maxSteps}, minmax(200px, 1fr))`,
                          minWidth: `${600 + maxSteps * 200}px`,
                          backgroundColor: group.depth > 0 ? `rgba(59, 130, 246, ${0.08 * group.depth})` : 'transparent'
                        }}
                      >
                        {/* 层级标识 */}
                        <div className="text-center flex items-center justify-center">
                          <span className={`px-3 py-2 rounded-full text-sm font-semibold ${
                            group.depth === 0 ? 'bg-purple-100 text-purple-800' :
                            group.depth === 1 ? 'bg-blue-100 text-blue-800' :
                            group.depth === 2 ? 'bg-green-100 text-green-800' :
                            'bg-orange-100 text-orange-800'
                          }`}>
                            L{group.depth}
                          </span>
                        </div>
                        
                        {/* 函数调用 */}
                        <div className="font-mono text-sm font-semibold flex items-center break-all">
                          {group.function_call}
                        </div>

                        {/* 动态步骤列 - 排列函数专用样式 */}
                        {Array.from({length: maxSteps}, (_, i) => {
                          const stepNum = i + 1;
                          const stepsForThisNumber = stepsByNumber[stepNum] || [];
                          
                          return (
                            <div key={stepNum} className="flex flex-col items-center justify-center min-h-[3rem] p-2 rounded-lg bg-white border border-gray-200">
                              {stepNum === 1 ? (
                                // 步骤1：显示条件判断结果
                                stepsForThisNumber.length > 0 && (
                                  <span className="text-2xl">
                                    {stepsForThisNumber[0].status === '✅' ? '✅' : 
                                     stepsForThisNumber[0].status === '❌' ? '❌' : ''}
                                  </span>
                                )
                              ) : (
                                // 其他步骤：显示递归调用和结果
                                <div className="flex flex-col items-center justify-center gap-2 w-full">
                                  {stepsForThisNumber.map((step, idx) => (
                                    <div key={idx} className={`px-2 py-1 rounded text-xs font-mono text-center w-full break-words ${
                                      step.phase === 'entry' ? 'bg-blue-50 border border-blue-200 text-blue-700' :
                                      'bg-green-50 border border-green-200 text-green-700'
                                    }`} style={{
                                      lineHeight: '1.2',
                                      wordBreak: 'break-word',
                                      hyphens: 'auto'
                                    }}>
                                      {step.status}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          } else {
            // 阶乘和fibonacci函数的原有布局
            return (
              <>
                {/* 表头 */}
                <div className="grid gap-4 mb-4 pb-2 border-b border-gray-300 font-semibold text-gray-700" style={{
                  gridTemplateColumns: `80px 200px repeat(${maxSteps}, 1fr)`
                }}>
                  <div className="text-center">层级</div>
                  <div>函数调用</div>
                  {Array.from({length: maxSteps}, (_, i) => (
                    <div key={i} className="text-center">步骤{i + 1}</div>
                  ))}
                </div>

                {/* 按执行顺序显示所有调用 */}
                <div className="space-y-1">
                  {sortedCallGroups.map(group => {
                    const stepsByNumber: { [key: number]: ExecutionStep[] } = {};
                    
                    // 按步骤编号分组该函数的所有步骤
                    [...group.step2_entries, ...group.step2_returns].forEach(step => {
                      if (!stepsByNumber[step.step_number]) {
                        stepsByNumber[step.step_number] = [];
                      }
                      stepsByNumber[step.step_number].push(step);
                    });
                    if (group.step1) {
                      stepsByNumber[1] = [group.step1];
                    }
                    
                    return (
                      <div 
                        key={group.call_id} 
                        className="grid gap-4 py-2 px-3 hover:bg-gray-100 rounded border-l-4 border-transparent hover:border-blue-300"
                        style={{
                          gridTemplateColumns: `80px 200px repeat(${maxSteps}, 1fr)`,
                          backgroundColor: group.depth > 0 ? `rgba(59, 130, 246, ${0.05 * group.depth})` : 'transparent'
                        }}
                      >
                        {/* 层级标识 */}
                        <div className="text-center flex items-center justify-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            group.depth === 0 ? 'bg-purple-100 text-purple-800' :
                            group.depth === 1 ? 'bg-blue-100 text-blue-800' :
                            group.depth === 2 ? 'bg-green-100 text-green-800' :
                            'bg-orange-100 text-orange-800'
                          }`}>
                            L{group.depth}
                          </span>
                        </div>
                        
                        {/* 函数调用 */}
                        <div className="font-mono text-sm font-semibold flex items-center">
                          {group.function_call}
                        </div>

                        {/* 动态步骤列 */}
                        {Array.from({length: maxSteps}, (_, i) => {
                          const stepNum = i + 1;
                          const stepsForThisNumber = stepsByNumber[stepNum] || [];
                          
                          return (
                            <div key={stepNum} className="text-center flex items-center justify-center">
                              {stepNum === 1 ? (
                                // 步骤1：显示条件判断结果
                                stepsForThisNumber.length > 0 && (
                                  <span className="text-xl">
                                    {stepsForThisNumber[0].status === '✅' ? '✅' : 
                                     stepsForThisNumber[0].status === '❌' ? '❌' : ''}
                                  </span>
                                )
                              ) : (
                                // 其他步骤：显示递归调用和结果
                                <div className="flex flex-col items-center justify-center gap-1 min-h-[2rem]">
                                  {stepsForThisNumber.map((step, idx) => (
                                    <div key={idx} className={`px-3 py-1 rounded text-xs font-mono whitespace-nowrap ${
                                      step.phase === 'entry' ? 'bg-blue-50 border border-blue-200 text-blue-700' :
                                      'bg-green-50 border border-green-200 text-green-700'
                                    }`}>
                                      {step.status}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              </>
            );
          }
        })()}

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
                  <span className="text-blue-700 font-mono text-xs">递归表达式</span>
                </div>
                <span>递出调用</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="bg-green-50 border border-green-200 px-2 py-1 rounded">
                  <span className="text-green-700 font-mono text-xs">= 结果值</span>
                </div>
                <span>回归计算</span>
              </div>
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            • 函数调用按调用深度缩进显示，体现层次关系<br/>
            • 递出阶段：函数调用向更深层级递进；回归阶段：从深层级返回并计算结果
          </div>
        </div>
      </div>

      {/* 详细执行步骤信息 */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">详细执行步骤</h3>
        <div className="max-h-96 overflow-y-auto overflow-x-scroll font-mono text-sm leading-relaxed border border-gray-200 rounded p-2 text-left" style={{ minWidth: '100%' }}>
          {data.steps.map((step, index) => {
            const isReturnStep = step.phase === 'return';
            const isConditionStep = step.step_number === 1;
            const isRecursiveStep = step.step_number === 2 && step.phase === 'entry';
            
            // 生成说明文本
            let description = '';
            if (isConditionStep) {
              if (step.status === '✅') {
                description = `(基本情况，返回${step.result})`;
              } else {
                description = '(条件不满足)';
              }
            } else if (isRecursiveStep) {
              description = '(进入递归)';
            } else if (isReturnStep) {
              description = `(回归，结果为${step.result})`;
            }
            
            const indentText = '  '.repeat(step.depth);
            const stepText = `步骤${step.step_number}: ${step.function_call} -> ${step.status} ${description}`;
            
            return (
              <div 
                key={index} 
                className="text-gray-800 whitespace-nowrap"
                style={{ 
                  minWidth: 'max-content',
                  paddingLeft: `${step.depth * 20}px`,
                  textAlign: 'left'
                }}
              >
                步骤{step.step_number}: {step.function_call} {'->'} {step.status} {description}
              </div>
            );
          })}
          
          {/* 最终结果 */}
          <div className="mt-4 pt-2 border-t border-gray-200 font-semibold text-green-600 whitespace-nowrap">
            最终结果: {data.finalResult} ✅
          </div>
        </div>
      </div>
    </div>
  );
};

export default HierarchicalVisualizationPanel;