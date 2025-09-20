import React, { useState } from 'react';
import type { StepAnnotation } from '../types';

interface StepAnnotatorProps {
  annotations: StepAnnotation;
  onChange: (annotations: StepAnnotation) => void;
}

const StepAnnotator: React.FC<StepAnnotatorProps> = ({ annotations, onChange }) => {
  const [newStepNumber, setNewStepNumber] = useState<string>('');
  const [newStepCode, setNewStepCode] = useState<string>('');

  const addStep = () => {
    const stepNum = parseInt(newStepNumber);
    if (stepNum && newStepCode.trim()) {
      onChange({
        ...annotations,
        [stepNum]: newStepCode.trim()
      });
      setNewStepNumber('');
      setNewStepCode('');
    }
  };

  const removeStep = (stepNumber: number) => {
    const newAnnotations = { ...annotations };
    delete newAnnotations[stepNumber];
    onChange(newAnnotations);
  };

  const updateStep = (stepNumber: number, code: string) => {
    onChange({
      ...annotations,
      [stepNumber]: code
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-xl font-semibold mb-4">步骤编号标记</h2>
      
      {/* 现有步骤列表 */}
      <div className="space-y-3 mb-6">
        {Object.entries(annotations).map(([stepNum, code]) => (
          <div key={stepNum} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-md">
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium min-w-2rem text-center">
              {stepNum}
            </span>
            <input
              type="text"
              value={code}
              onChange={(e) => updateStep(parseInt(stepNum), e.target.value)}
              className="flex-1 px-3 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="代码片段"
            />
            <button
              onClick={() => removeStep(parseInt(stepNum))}
              className="text-red-600 hover:text-red-800 px-2 py-1"
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {/* 添加新步骤 */}
      <div className="border-t pt-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">添加新步骤</h3>
        <div className="flex space-x-3">
          <input
            type="number"
            value={newStepNumber}
            onChange={(e) => setNewStepNumber(e.target.value)}
            className="w-20 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="编号"
            min="1"
          />
          <input
            type="text"
            value={newStepCode}
            onChange={(e) => setNewStepCode(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="输入对应的代码片段"
            onKeyPress={(e) => e.key === 'Enter' && addStep()}
          />
          <button
            onClick={addStep}
            disabled={!newStepNumber || !newStepCode.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            添加
          </button>
        </div>
      </div>

      {/* 说明文字 */}
      <div className="mt-4 p-3 bg-blue-50 rounded-md">
        <p className="text-sm text-blue-800">
          <strong>使用说明：</strong> 
          为代码中的关键步骤分配编号，例如基本情况（终止条件）可以标记为步骤1，递归调用可以标记为步骤2。
          代码片段应该能够匹配到您的Python代码中的相应语句。
        </p>
      </div>
    </div>
  );
};

export default StepAnnotator;