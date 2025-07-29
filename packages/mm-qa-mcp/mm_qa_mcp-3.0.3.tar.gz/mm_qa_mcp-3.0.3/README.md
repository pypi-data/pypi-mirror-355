# QA 智能体

## 项目介绍

QA智能工具服务是一个集成了多种质量检测和开发辅助功能的服务集合，主要用于支持测试、开发和运维工作。服务通过MCP（Model Control Protocol）接口与各类客户端（Claude/cursor等）集成，提供包括日志检索、代码分析、案例生成和知识库查询等功能。

## 项目结构

```
minimax_qa_mcp/
├── server.py          # MCP服务入口与API定义
├── src/               # 核心功能模块
│   ├── grafana/       # 日志检索和API调用分析
│   ├── gateway_case/  # API流量日志分析
│   ├── query_segments/# 代码分析与搜索
│   ├── generator_case/# 自动生成测试用例
│   ├── get_weaviate_info/ # 知识库检索
│   └── xmind2markdown/    # XMind转Markdown工具
├── conf/              # 配置文件
├── utils/             # 工具函数库
└── logs/              # 日志输出目录
```

## 核心功能

### 1. 日志检索与分析

- **获取Grafana日志**：支持从多个业务线（星野、Talkie、海螺视频等）的不同环境（测试、生产）获取日志
- **接口调用分析**：获取服务的接口调用列表及基本信息
- **HTTP流量日志**：提取API接口的请求与响应日志，支持CSV导出

### 2. 代码分析与搜索

- **多模式代码查询**：
  - API查询：获取API的路径、入参、出参和实现逻辑
  - 函数分析：查询函数的调用链关系图谱
  - 代码影响分析：分析代码变更的影响范围
  - 函数详情查看：查询函数的详细实现代码
  - 模糊搜索：搜索相似的代码片段

### 3. 自动生成测试用例

- 基于API信息自动生成测试用例
- 支持生成前置条件和测试案例
- 与代码仓库集成，自动分析API实现

### 4. 知识库检索

- 基于向量数据库的文档搜索
- 支持语义相似度检索
- 可与模型集成进行内容总结

## 环境配置与启动

### 依赖安装

项目使用pyproject.toml和setup.py管理依赖。可以通过以下方式安装：

```shell
pip install -e .
```

或通过发布脚本build并安装：

```shell
bash publish.sh
pip install dist/*.whl
```

### 启动服务

直接启动server.py：

```shell
python minimax_qa_mcp/server.py
```


### 客户端集成

#### Cursor 集成

在Cursor配置文件中添加：

```json
{
    "agent_name": {
      "command": "uvx",
      "args": [
        "mm_qa_mcp"
      ]
    }
}
```

## API 参考

### 日志服务

- `get_grafana_data(scene, psm, msg, from_time, to_time)`：获取业务日志
  - scene: 枚举值，指定业务线和环境（例如：xingye_prod, talkie_test）
  - psm: 服务名称
  - msg: 筛选关键字
  - from_time/to_time: 时间范围

- `get_top_methods(scene, psm)`：获取服务接口列表
  - scene: 枚举值，指定业务线和协议（例如：xingye_http, talkie_rpc）
  - psm: 服务名称

- `get_http_data(scene, psm, api_path, from_time, to_time)`：获取HTTP接口日志
  - 返回CSV文件访问地址

### 代码分析

- `query_code_segments(query, query_type, limit, exact, advanced, depth, direction, output)`
  - query: 查询内容（API路径、函数名等）
  - query_type: 查询类型（API, FUNC, CODE, FUNC_DETAIL, ANY）
  - 其他参数用于精确控制查询行为

### 测试案例生成

- `gen_case(input_data, pwd)`：生成测试用例
  - input_data: JSON格式的输入数据
  - pwd: 用户当前目录地址
  - 返回前置条件和测试用例文件路径

### 知识库检索

- `get_weaviate_info(input_data)`：从知识库获取业务相关信息
  - input_data: 用户问题
  - 返回相关文档信息

## 打包上传pypi流程

### 1. 创建配置文件

```bash
vim ~/.pypirc
```

添加以下内容（账号密码 联系@星云）:

```ini
[pypi]
username = xxxxx
password = xxxxx
```

### 2. 打包

执行打包脚本:

```bash
bash publish.sh
```


