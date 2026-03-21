# BabyEco - 儿童行为奖励管理系统

## 项目概述

BabyEco 是一个专为家庭设计的儿童行为奖励管理系统，旨在通过游戏化和奖励机制帮助家长培养孩子良好的行为习惯。系统支持多子女家庭管理，提供任务分配、奖励发放、行为追踪等功能。

### 🎯 核心功能

- **多子女管理** - 为每个孩子建立独立的档案和任务系统
- **任务分配** - 家长可以创建各种类型的任务（日常、学习、习惯等）
- **奖励系统** - 通过积分和虚拟奖励激励孩子完成任务
- **行为追踪** - 记录孩子的行为表现和成长轨迹
- **数据洞察** - 提供数据分析和成长报告

### 🚀 最新更新

#### ✅ 已完成功能

1. **后端认证系统 (SPEC-AUTH-001)** - 2026-03-21 完成
   - 手机号作为主要标识的用户认证
   - 用户状态和角色管理
   - 登录令牌管理和黑名单机制
   - 速率限制保护（登录：5次/15分钟，注册：3次/小时）
   - 密码复杂度验证
   - 子档案设备绑定功能
   - 25项测试全部通过

2. **前端父应用框架 (SPEC-FE-AUTH-001)** - 2026-03-21 完成
   - Next.js 15 + React 19 技术栈
   - 完整的认证界面（登录、注册）
   - Zustand 状态管理带持久化
   - 路由保护和中间件
   - 360个依赖包已安装
   - 24个文件完成构建

#### 📋 计划中功能

- 数据迁移脚本
- API 文档更新
- Redis 分布式限流集成
- 子女任务管理界面
- 奖励兑换系统

## 技术架构

### 后端技术栈

- **框架**: FastAPI (Python 3.10+)
- **数据库**: PostgreSQL + SQLAlchemy ORM
- **认证**: JWT 令牌 + 手机号验证
- **测试**: pytest (85%+ 覆盖率)
- **工具**: Ruff 代码检查 + 黑格式化

### 前端技术栈

- **框架**: Next.js 15.1.0 + React 19.0.0
- **语言**: TypeScript 5.3.0
- **状态管理**: Zustand 4.5.0 (带持久化)
- **样式**: Tailwind CSS 3.4.0
- **表单**: react-hook-form 7.50.0
- **验证**: Zod 3.23.0

## 项目结构

```
babyeco/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── api/            # API 路由
│   │   ├── schemas/       # Pydantic 模式
│   │   ├── services/       # 业务逻辑
│   │   └── repositories/   # 数据访问层
│   ├── tests/              # 测试文件
│   └── main.py            # 应用入口
├── apps/                   # 前端应用
│   └── parent-app/         # 父母管理应用
│       ├── app/           # Next.js App Router
│       ├── components/    # React 组件
│       ├── stores/        # 状态管理
│       └── lib/           # 工具库
└── .moai/                 # MoAI 项目配置
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Git

### 后端设置

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端设置

```bash
cd apps/parent-app
npm install
npm run dev
```

### 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试（待实现）
cd apps/parent-app
npm test
```

## 开发规范

### 代码质量

项目遵循 TRUST 5 质量标准：
- **Tested** - 85%+ 测试覆盖率
- **Readable** - 清晰的命名和文档
- **Unified** - 一致的代码格式
- **Secured** - OWASP 安全标准
- **Trackable** - 规范的提交记录

### SPEC 流程

采用 MoAI 的 SPEC-First 开发流程：
1. **计划阶段** - 创建需求规格
2. **执行阶段** - DDD/TDD 实现
3. **同步阶段** - 文档同步更新

## 已完成的 SPEC

- ✅ **SPEC-DESIGN-001** - 系统架构设计
- ✅ **SPEC-DESIGN-002** - 父应用设计
- ✅ **SPEC-DESIGN-003** - 设计系统
- ✅ **SPEC-AUTH-001** - 后端认证模块
- ✅ **SPEC-FE-AUTH-001** - 前端认证框架

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请提交 Issue 或联系开发团队。

---

**BabyEco** - 让成长更有趣，让教育更简单 🌟

*使用 MoAI-ADK 智能开发框架构建*