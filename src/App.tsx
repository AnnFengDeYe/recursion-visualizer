import React, { useState } from 'react';
import CodeEditor from './components/CodeEditor.js';
import StepAnnotator from './components/StepAnnotator.js';
import HierarchicalVisualizationPanel from './components/HierarchicalVisualizationPanel.js';
import type { ExecutionStep } from './types.js';
import './App.css';

function App() {
  const [code, setCode] = useState<string>(`def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)`);
  
  const [functionName, setFunctionName] = useState<string>('fibonacci');
  const [args, setArgs] = useState<string>('[3]');
  const [stepAnnotations, setStepAnnotations] = useState<Record<number, string>>({
    1: "if n <= 1:",
    2: "return fibonacci(n - 1) + fibonacci(n - 2)"
  });
  const [visualizationData, setVisualizationData] = useState<{
    steps: ExecutionStep[];
    finalResult: any;
    success: boolean;
    error?: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleVisualize = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/analyze_code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
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
        finalResult: null,
        success: false,
        error: '连接后端服务失败，请确保后端服务正在运行'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">
              递归算法可视化工具
            </h1>
            <p className="text-gray-600">缩进编号法可视化展示</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 左侧：代码编辑和设置 */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">代码编辑器</h2>
              <CodeEditor 
                value={code} 
                onChange={setCode}
                language="python"
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
                    onChange={(e) => setFunctionName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              onChange={setStepAnnotations}
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
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">可视化结果</h2>
            <HierarchicalVisualizationPanel data={visualizationData} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
