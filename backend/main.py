#!/usr/bin/env python3
"""
递归算法可视化工具后端API服务
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from tracer import HierarchicalRecursionTracer, PermutationRecursionTracer


app = FastAPI(title="递归算法可视化API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite默认端口
        "http://localhost:5174",  # Vite备用端口
        "http://localhost:5175",  # Vite备用端口
        "http://localhost:5176",  # Vite备用端口
        "http://localhost:5177",  # Vite备用端口
        "http://localhost:5178",  # Vite备用端口
        "http://localhost:3000",  # 其他可能的前端端口
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeInput(BaseModel):
    """代码输入模型"""
    code: str
    function_name: str
    args: List[Any]
    step_annotations: Dict[int, str]  # 步骤编号到代码的映射


class ExecutionStep(BaseModel):
    """执行步骤模型"""
    step_number: int
    function_call: str
    args: List[Any]
    depth: int
    status: str  # "✅", "❌", "➡️"
    result: Optional[Any] = None
    line_number: Optional[int] = None


class VisualizationResult(BaseModel):
    """可视化结果模型"""
    steps: List[Dict[str, Any]]
    final_result: Any
    success: bool
    error: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "递归算法可视化API服务正在运行"}


@app.post("/analyze_code")
async def analyze_code(code_input: CodeInput) -> VisualizationResult:
    """
    分析Python代码并生成递归调用的可视化数据
    """
    try:
        # 判断是否是排列函数
        if code_input.function_name == 'permute_helper':
            # 使用专门的排列追踪器
            tracer = PermutationRecursionTracer(code_input.step_annotations)
        else:
            # 使用通用递归追踪器
            tracer = HierarchicalRecursionTracer(code_input.step_annotations)
        
        # 执行代码并追踪
        result = tracer.execute_and_trace(
            code_input.code,
            code_input.function_name,
            code_input.args
        )
        
        return VisualizationResult(
            steps=result["steps"],
            final_result=result["final_result"],
            success=result["success"],
            error=result.get("error")
        )
        
    except Exception as e:
        return VisualizationResult(
            steps=[],
            final_result=None,
            success=False,
            error=str(e)
        )


@app.get("/test_factorial")
async def test_factorial():
    """
    测试阶乘函数的可视化
    """
    code = '''
def factorial(n):
    if n == 1:
        return 1
    return n * factorial(n - 1)
'''
    
    step_annotations = {
        1: "if n == 1:",
        2: "return n * factorial(n - 1)"
    }
    
    tracer = HierarchicalRecursionTracer(step_annotations)
    result = tracer.execute_and_trace(code, "factorial", [3])
    
    return {
        "message": "阶乘函数测试完成",
        "result": result
    }


if __name__ == "__main__":
    import uvicorn
    print("启动递归算法可视化API服务...")
    print("访问 http://localhost:8000/docs 查看API文档")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)