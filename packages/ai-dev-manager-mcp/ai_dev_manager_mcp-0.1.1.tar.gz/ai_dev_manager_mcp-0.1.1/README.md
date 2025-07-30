# AI开发经理 MCP服务

一个基于FastMCP框架的智能开发经理服务，帮助AI有条不紊地完成从需求分析、迭代规划、任务拆解到生成开发报告的完整软件开发生命周期。

## 🎯 项目概述

本MCP服务扮演AI的"开发经理"角色，提供：

- **项目状态机**: 作为项目元数据的唯一、可靠的数据源
- **AI引导者**: 为AI提供结构清晰的工具集和上下文感知的引导提示

### 核心特性

- ✅ **自动感知工作目录**: 基于当前工作目录进行项目管理
- ✅ **版本化迭代管理**: 支持语义化版本号和完整的迭代生命周期
- ✅ **结构化数据存储**: 所有数据存储在`.cursor/devplan/`目录
- ✅ **智能引导系统**: 根据开发阶段提供针对性指导
- ✅ **原子性操作**: 确保数据一致性和操作安全性
- ✅ **多种使用方式**: 支持MCP服务器和CLI两种模式

## 📦 安装方式

### 方式一：PyPI安装（推荐）

```bash
# 全局安装
pip install ai-dev-manager-mcp

# 或使用pipx（推荐）
pipx install ai-dev-manager-mcp
```

### 方式二：使用uvx（一次性运行）

```bash
# 直接启动MCP服务器
uvx ai-dev-manager-mcp

# 在指定项目目录启动
uvx ai-dev-manager-mcp -p /path/to/your/project
```

### 方式三：源码安装

```bash
git clone https://github.com/yourusername/ai-dev-manager-mcp.git
cd ai-dev-manager-mcp
pip install -e .
```

## 🚀 使用方式

### MCP服务器模式（主要用法）

#### 使用uvx（推荐）

```json
{
  "mcpServers": {
    "ai-dev-manager": {
      "command": "uvx",
      "args": ["ai-dev-manager-mcp", "-p", "/your/project/directory"]
    }
  }
}
```

#### 使用pipx安装后

```json
{
  "mcpServers": {
    "ai-dev-manager": {
      "command": "ai-dev-manager-mcp",
      "args": ["-p", "/your/project/directory"]
    }
  }
}
```

### 基本使用流程

配置好Claude Desktop后，直接在对话中使用MCP工具：

1. **获取项目上下文** - 调用 `get_project_context()` 
2. **开始新迭代** - 调用 `start_new_iteration("1.0.0", "项目需求描述")`
3. **拆解需求** - 调用 `decompose_goal_into_requirements(goal_id, requirements_list)`
4. **生成任务** - 调用 `generate_tasks_for_requirement(requirement_id, tasks_list)`
5. **跟踪进度** - 调用 `update_task_status(task_id, "done")`

## 🛠️ 主要功能

### MCP工具（Claude Desktop中使用）

#### 类别一：上下文与引导工具

- `get_project_context()` - 获取项目根目录、计划目录和当前活动迭代
- `get_guidance(phase)` - 根据开发阶段提供引导建议

#### 类别二：迭代管理工具

- `start_new_iteration(version, prd)` - 创建新的开发迭代
- `list_iterations()` - 列出所有历史迭代
- `complete_iteration(version)` - 完成并归档指定迭代

#### 类别三：规划与拆解工具

- `decompose_goal_into_requirements(goal_id, requirements)` - 将目标拆解为功能需求
- `generate_tasks_for_requirement(requirement_id, tasks)` - 为需求生成具体任务

#### 类别四：执行与报告工具

- `update_task_status(task_id, status)` - 更新任务完成状态
- `update_development_report(content, mode)` - 更新开发报告

#### 类别五：查询与视图工具

- `view_current_iteration_plan()` - 查看当前迭代的完整计划
- `view_development_report()` - 查看当前迭代的开发报告

## 📁 数据存储结构

```
.cursor/devplan/
├── active_iteration.json      # 当前活动迭代
├── iterations_index.json      # 迭代索引
├── v1.0.0/                    # 版本目录
│   ├── iteration.json          # 迭代数据
│   └── report.md              # 开发报告
└── v1.1.0/
    ├── iteration.json
    └── report.md
```

## 🔧 配置选项

### 环境变量
- 无需特殊环境变量配置
- 自动使用当前工作目录作为项目根目录

### 自定义项目根目录
```bash
# 使用uvx
uvx ai-dev-manager-mcp -p /custom/path

# 在Claude Desktop配置中指定
{
  "args": ["ai-dev-manager-mcp", "-p", "/custom/path"]
}
```

## 📚 使用场景

### 1. 个人开发者
```bash
# 启动MCP服务器进行开发
uvx ai-dev-manager-mcp -p ~/my-blog-project
```

### 2. 团队协作
```bash
# 团队成员配置Claude Desktop指向同一项目目录
# 在配置中设置项目路径，确保所有人使用相同的项目状态
```

### 3. AI助手集成
在Claude Desktop中配置MCP服务器，让AI助手自动管理开发流程。

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**自我挑战**: 

这个AI开发经理MCP服务的设计有什么潜在的改进空间？

1. **数据持久化**: 当前使用JSON文件存储，对于大型项目可能需要考虑数据库支持
2. **并发控制**: 多人协作时可能需要更强的锁机制
3. **模板系统**: 可以为不同类型的项目提供预定义的需求和任务模板
4. **集成能力**: 可以考虑与Git、CI/CD系统的集成
5. **可视化**: 可以增加进度图表、甘特图等可视化功能
6. **AI学习**: 可以基于历史数据为AI提供更智能的建议

这些改进点可以根据实际使用反馈逐步实现，确保服务始终满足实际开发需求！ 