import React, { useState, useRef, useEffect } from 'react';
import CodeEditor from './components/CodeEditor.js';
import StepAnnotator from './components/StepAnnotator.js';
import HierarchicalVisualizationPanel from './components/HierarchicalVisualizationPanel.js';
import type { ExecutionStep } from './types.js';
import './App.css';

// 预设函数模板
const FUNCTION_TEMPLATES = {
  factorial: {
    code: `def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)`,
    functionName: 'factorial',
    args: '[4]',
    stepAnnotations: {
      1: "if n <= 1:",
      2: "return n * factorial(n - 1)"
    }
  },
  fibonacci: {
    code: `def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)`,
    functionName: 'fibonacci',
    args: '[3]',
    stepAnnotations: {
      1: "if n <= 1:",
      2: "return fibonacci(n - 1) + fibonacci(n - 2)"
    }
  },
  permutation: {
    code: `def permute_helper(nums, start, result):
    if start == len(nums):
        result.append(nums[:])
        return
    
    for i in range(start, len(nums)):
        nums[start], nums[i] = nums[i], nums[start]
        permute_helper(nums, start + 1, result)
        nums[start], nums[i] = nums[i], nums[start]`,
    functionName: 'permute_helper',
    args: '[[1, 2], 0, []]',
    stepAnnotations: {
      1: "if start == len(nums):",
      2: "for i in range(start, len(nums)):",
      3: "nums[start], nums[i] = nums[i], nums[start]",
      4: "permute_helper(nums, start + 1, result)",
      5: "nums[start], nums[i] = nums[i], nums[start]"
    }
  }
};

function App() {
  const [selectedTemplate, setSelectedTemplate] = useState<'factorial' | 'fibonacci' | 'permutation'>('factorial');
  const [functionName, setFunctionName] = useState<string>('factorial');
  const [args, setArgs] = useState<string>('[4]');
  const [stepAnnotations, setStepAnnotations] = useState<Record<number, string>>(FUNCTION_TEMPLATES.factorial.stepAnnotations);
  const [visualizationData, setVisualizationData] = useState<{
    steps: ExecutionStep[];
    final_result: any;
    success: boolean;
    error?: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // 用于动态同步宽度的 refs
  const headerRef = useRef<HTMLDivElement>(null);
  const mainContentRef = useRef<HTMLDivElement>(null);

  // 同步标题栏和内容区域的宽度
  const syncWidths = () => {
    if (headerRef.current && mainContentRef.current) {
      const mainWidth = mainContentRef.current.scrollWidth;
      headerRef.current.style.width = `${mainWidth}px`;
    }
  };

  // 在可视化数据变化时同步宽度
  useEffect(() => {
    // 使用 setTimeout 等待 DOM 更新完成
    const timer = setTimeout(syncWidths, 100);
    return () => clearTimeout(timer);
  }, [visualizationData]);

  // 用 ResizeObserver 监听内容区域尺寸变化
  useEffect(() => {
    if (mainContentRef.current) {
      const resizeObserver = new ResizeObserver(() => {
        syncWidths();
      });
      resizeObserver.observe(mainContentRef.current);
      return () => resizeObserver.disconnect();
    }
  }, []);

  // 处理模板切换
  const handleTemplateChange = (template: 'factorial' | 'fibonacci' | 'permutation') => {
    setSelectedTemplate(template);
    const templateData = FUNCTION_TEMPLATES[template];
    setFunctionName(templateData.functionName);
    setArgs(templateData.args);
    setStepAnnotations(templateData.stepAnnotations);
  };

  const handleVisualize = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/analyze_code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: FUNCTION_TEMPLATES[selectedTemplate].code,
          function_name: functionName,
          args: JSON.parse(args),
          step_annotations: stepAnnotations
        })
      });
      
      const result = await response.json();
      setVisualizationData(result);
    } catch (error) {
      console.error('可视化失败:', error);
      setVisualizationData({
        steps: [],
        final_result: null,
        success: false,
        error: '连接后端服务失败，请确保后端服务正在运行'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="w-full overflow-x-auto">
        {/* 标题栏 - 使用 ref 动态同步宽度 */}
        <div ref={headerRef} style={{
          minWidth: '100vw',
          width: 'fit-content'
        }}>
          <header className="bg-white shadow-sm border-b">
            <div className="px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center py-6">
                <div className="flex items-center space-x-4">
                  <h1 className="text-3xl font-bold text-gray-900">
                    递归算法可视化工具（BiliBili: 安枫的叶）
                  </h1>
                  
                  {/* 移动动画图标 */}
                  <div className="floating-icon">
                    <img 
                      src="/images/biliIcon.png" 
                      alt="BiliBili Icon" 
                      className="opacity-70"
                      style={{ width: '64px', height: '64px' }}
                    />
                  </div>
                </div>
                
                <p className="text-gray-600">缩进编号法可视化展示</p>
              </div>
            </div>
          </header>
        </div>

        {/* 主内容区域 - 使用 ref 监听宽度变化 */}
        <div ref={mainContentRef} style={{
          minWidth: '100vw',
          width: 'fit-content'
        }}>
          <main className="px-4 sm:px-6 lg:px-8 py-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8" style={{
              width: 'fit-content',
              minWidth: '100%'
            }}>
              {/* 左侧：代码编辑和设置 */}
              <div className="space-y-6" style={{ minWidth: 'fit-content' }}>
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">代码编辑器</h2>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleTemplateChange('factorial')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      selectedTemplate === 'factorial'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    阶乘递归
                  </button>
                  <button
                    onClick={() => handleTemplateChange('fibonacci')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      selectedTemplate === 'fibonacci'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Fibonacci递归
                  </button>
                  <button
                    onClick={() => handleTemplateChange('permutation')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      selectedTemplate === 'permutation'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    排列递归
                  </button>
                </div>
              </div>
              <CodeEditor 
                value={FUNCTION_TEMPLATES[selectedTemplate].code} 
                language="python"
                readOnly={true}
              />
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">执行设置</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    函数名
                  </label>
                  <input
                    type="text"
                    value={functionName}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-700 cursor-not-allowed"
                    placeholder="例如: factorial"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    参数 (JSON格式)
                  </label>
                  <input
                    type="text"
                    value={args}
                    onChange={(e) => setArgs(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="例如: [3] 或 [5, 2]"
                  />
                </div>
              </div>
            </div>

            <StepAnnotator
              annotations={stepAnnotations}
            />

            <button
              onClick={handleVisualize}
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {isLoading ? '生成可视化中...' : '生成可视化'}
            </button>
          </div>

          {/* 右侧：可视化结果 */}
          <div className="bg-white rounded-lg shadow-sm border p-6 w-full" style={{
            width: 'fit-content',
            minWidth: '100%',
            overflowX: 'auto'
          }}>
            <h2 className="text-xl font-semibold mb-4">可视化结果</h2>
            <HierarchicalVisualizationPanel data={visualizationData} />
          </div>
        </div>
      </main>
        </div>
      </div>
    </div>
  );
}

export default App;
