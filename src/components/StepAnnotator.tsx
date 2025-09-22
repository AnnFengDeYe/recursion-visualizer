import React from 'react';
import type { StepAnnotation } from '../types';

interface StepAnnotatorProps {
  annotations: StepAnnotation;
  onChange?: (annotations: StepAnnotation) => void;
}

const StepAnnotator: React.FC<StepAnnotatorProps> = ({ annotations }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-xl font-semibold mb-4">步骤编号标记</h2>
      
      {/* 现有步骤列表 - 只读模式 */}
      <div className="space-y-3">
        {Object.entries(annotations).map(([stepNum, code]) => (
          <div key={stepNum} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-md">
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium min-w-2rem text-center">
              {stepNum}
            </span>
            <input
              type="text"
              value={code}
              readOnly
              className="flex-1 px-3 py-1 border border-gray-300 rounded bg-gray-50 text-gray-700 cursor-not-allowed"
              placeholder="代码片段"
            />
          </div>
        ))}
      </div>

      {/* 说明文字 */}
      <div className="mt-4 p-3 bg-blue-50 rounded-md text-left">
        <p className="text-sm text-blue-800" style={{ textAlign: 'left' }}>
          <strong>使用说明：</strong> 
          为代码中的关键步骤分配编号，例如基本情况（终止条件）可以标记为步骤1，递归调用可以标记为步骤2。
          代码片段已经根据选中的函数自动设置。
        </p>
      </div>
    </div>
  );
};

export default StepAnnotator;