# 递归算法可视化工具 🔄

递归算法可视化工具，采用创新的**缩进编号法**帮助理解递归算法的执行过程。

![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tech Stack](https://img.shields.io/badge/tech-React%20%2B%20FastAPI-orange.svg)

## ✨ 特性

- 🎯 **缩进编号法可视化**：独特的层级缩进展示递归调用关系
- 📝 **代码编辑器**：基于Monaco Editor的Python代码编辑器
- 🔄 **实时追踪**：动态追踪递归函数的执行过程
- 📊 **多维度展示**：表格化、详细步骤、层级结构多种视图
- 🎨 **美观界面**：现代化的Web界面，支持响应式设计
- 🚀 **预设模板**：内置阶乘、斐波那契、排列生成等经典递归算法

## 🖼️ 功能演示

### 主要功能界面
- **代码编辑器**：支持Python语法高亮和自动补全
- **层级可视化**：清晰展示递归调用的层次关系
- **步骤追踪**：详细记录每一步的执行过程
- **结果展示**：实时显示递归计算的最终结果

### 支持的算法类型
- ✅ 阶乘函数 (`factorial`)
- ✅ 斐波那契数列 (`fibonacci`)
- ✅ 排列生成 (`permutation`)
- 🔄 更多算法持续支持中...

## 🚀 快速开始

### 环境要求

- **前端**: Node.js 16+ 
- **后端**: Python 3.8+
- **浏览器**: Chrome, Firefox, Safari, Edge

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd recursion-visualizer
```

2. **启动后端服务**
```bash
cd backend
pip install -r requirements.txt
python main.py
```
后端服务将在 `http://localhost:8000` 启动

3. **启动前端服务**
```bash
npm install
npm run dev
```
前端服务将在 `http://localhost:5173` 启动

4. **访问应用**
打开浏览器访问 `http://localhost:5173`

## 📖 使用说明

### 基本使用流程

1. **选择算法模板**：点击页面顶部的算法按钮（阶乘、Fibonacci、排列生成）
2. **编辑代码**：在Monaco编辑器中修改或编写递归函数
3. **配置参数**：
   - 设置函数名称
   - 输入参数（JSON格式，如 `[4]` 或 `[[1,2], 0, []]`）
   - 配置步骤注释（可选）
4. **生成可视化**：点击"生成可视化"按钮
5. **查看结果**：在右侧面板查看可视化结果

### 代码示例

#### 阶乘函数
```python
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)
```

#### 斐波那契数列
```python
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)
```

## 🏗️ 技术架构

### 前端技术栈
- **React 19**: 现代化React框架
- **TypeScript**: 类型安全的JavaScript
- **Vite**: 快速的构建工具
- **Monaco Editor**: VSCode同款代码编辑器
- **Tailwind CSS**: 实用优先的CSS框架

### 后端技术栈
- **FastAPI**: 高性能Python API框架
- **代码插桩技术**: 动态注入追踪代码
- **Uvicorn**: ASGI服务器
- **Pydantic**: 数据验证和设置管理

### 核心算法
- **递归追踪器**: 动态注入追踪代码，记录函数调用
- **层级分析**: 分析递归调用的深度和关系
- **步骤标注**: 智能识别和标记执行步骤

## 📁 项目结构

```
recursion-visualizer/
├── src/                          # 前端源码
│   ├── components/               # React组件
│   │   ├── CodeEditor.tsx        # 代码编辑器组件
│   │   ├── HierarchicalVisualizationPanel.tsx  # 层级可视化面板
│   │   ├── StepAnnotator.tsx     # 步骤注释器
│   │   └── VisualizationPanel.tsx # 可视化面板
│   ├── types.ts                  # TypeScript类型定义
│   ├── App.tsx                   # 主应用组件
│   └── main.tsx                  # 应用入口
├── backend/                      # 后端源码
│   ├── main.py                   # FastAPI主服务
│   ├── tracer.py                 # 递归追踪器核心
│   └── requirements.txt          # Python依赖
├── package.json                  # 前端依赖配置
└── README.md                     # 项目说明文档
```

## 🎯 可视化原理

### 缩进编号法
本工具采用独创的"缩进编号法"来可视化递归过程：

1. **层级标识**：不同递归深度用不同的缩进和颜色表示
2. **步骤编号**：每个递归函数的关键步骤都有编号标识
3. **状态追踪**：实时显示条件判断结果（✅/❌）和递归表达式
4. **阶段区分**：区分"递出"和"回归"两个阶段

### 执行流程追踪
- **函数调用入口**: 记录参数和调用深度
- **条件判断**: 追踪基本情况的判断结果
- **递归调用**: 展示递归表达式的构造
- **结果回归**: 显示从深层级返回的计算结果

## 🔧 API 接口

### 主要接口

#### POST `/analyze_code`
分析递归代码并生成可视化数据

**请求参数**:
```json
{
  "code": "def factorial(n): ...",
  "function_name": "factorial",
  "args": [4],
  "step_annotations": {
    "1": "if n <= 1:",
    "2": "return n * factorial(n - 1)"
  }
}
```

**返回结果**:
```json
{
  "steps": [...],
  "final_result": 24,
  "success": true,
  "error": null
}
```

## 🎓 教学应用

这个工具特别适合：

- **计算机科学教育**：帮助理解递归概念
- **算法学习**：可视化经典递归算法的执行过程
- **编程教学**：展示递归函数的调用栈和执行流程

## 🤝 贡献指南

欢迎参与项目贡献！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

安枫的叶：https://space.bilibili.com/295283060?spm_id_from=333.788.0.0

---

⭐ 如果这个项目对您有帮助，请给一个 Star！