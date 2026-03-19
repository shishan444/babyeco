# BabyEco 项目结构文档

## 架构概览

```
BabyEco
├── apps/                          # 应用层
│   ├── parent-app/                # 家长端 App
│   └── child-app/                 # 孩子端 App
├── packages/                      # 共享包
│   ├── shared/                    # 共享代码
│   ├── ui/                        # 共享 UI 组件库
│   └── config/                    # 共享配置
├── backend/                       # 后端 API 服务
└── docs/                          # 项目文档
```

---

## 完整目录结构

```
babyeco/
├── apps/
│   ├── parent-app/                        # 家长端 Next.js 应用
│   │   ├── app/                           # Next.js App Router
│   │   │   ├── (auth)/                    # 认证相关页面
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── (dashboard)/               # 主要功能页面
│   │   │   │   ├── dashboard/             # 仪表盘
│   │   │   │   ├── tasks/                 # 任务管理
│   │   │   │   │   ├── create/
│   │   │   │   │   ├── edit/
│   │   │   │   │   └── list/
│   │   │   │   ├── review/                # 审核中心
│   │   │   │   ├── rewards/               # 奖励设置
│   │   │   │   ├── content/               # 内容管理（电子书等）
│   │   │   │   ├── reports/               # 报告与数据
│   │   │   │   └── settings/              # 设置
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/                    # 组件
│   │   │   ├── ui/                        # 基础 UI 组件
│   │   │   ├── tasks/                     # 任务相关组件
│   │   │   ├── review/                    # 审核相关组件
│   │   │   ├── reports/                   # 报告组件
│   │   │   └── layout/                    # 布局组件
│   │   ├── hooks/                         # 自定义 Hooks
│   │   ├── stores/                        # Zustand 状态管理
│   │   ├── services/                      # API 服务层
│   │   ├── lib/                           # 工具函数
│   │   ├── types/                         # TypeScript 类型定义
│   │   ├── styles/                        # 样式文件
│   │   ├── public/                        # 静态资源
│   │   │   ├── sounds/                    # 音效文件
│   │   │   └── images/
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   └── package.json
│   │
│   └── child-app/                         # 孩子端 Next.js 应用
│       ├── app/                           # Next.js App Router
│       │   ├── (auth)/                    # 认证（简化版）
│       │   ├── (main)/                    # 主要功能页面
│       │   │   ├── home/                  # 首页/看板
│       │   │   ├── tasks/                 # 任务列表
│       │   │   │   ├── list/
│       │   │   │   └── detail/
│       │   │   ├── wallet/                # 积分钱包
│       │   │   │   ├── balance/
│       │   │   │   └── history/
│       │   │   ├── exchange/              # 兑换中心
│       │   │   │   ├── wishlist/
│       │   │   │   ├── rewards/
│       │   │   │   └── timer/
│       │   │   ├── entertainment/         # 娱乐模块
│       │   │   │   ├── books/             # 电子书
│       │   │   │   └── games/             # 游戏时间
│       │   │   ├── ai/                    # AI 问答
│       │   │   └── profile/               # 个人中心
│       │   ├── onboarding/                # 新手引导
│       │   ├── layout.tsx
│       │   └── page.tsx
│       ├── components/                    # 组件
│       │   ├── ui/                        # 基础 UI 组件（大按钮、大字体）
│       │   ├── tasks/                     # 任务卡片组件
│       │   ├── wallet/                    # 积分相关组件
│       │   ├── exchange/                  # 兑换相关组件
│       │   ├── entertainment/             # 娱乐组件
│       │   ├── ai/                        # AI 对话组件
│       │   ├── animations/                # 动效组件
│       │   │   ├── confetti/              # 庆祝动效
│       │   │   ├── progress/              # 进度动效
│       │   │   └── transitions/           # 过渡动效
│       │   └── layout/                    # 布局组件
│       ├── hooks/                         # 自定义 Hooks
│       ├── stores/                        # Zustand 状态管理
│       ├── services/                      # API 服务层
│       ├── lib/                           # 工具函数
│       ├── types/                         # TypeScript 类型定义
│       ├── styles/                        # 样式文件
│       ├── public/                        # 静态资源
│       │   ├── sounds/                    # 音效文件（反馈音）
│       │   ├── images/
│       │   └── models/                    # 3D 模型（可选）
│       ├── next.config.js
│       ├── tailwind.config.js
│       └── package.json
│
├── packages/
│   ├── shared/                            # 共享业务代码
│   │   ├── src/
│   │   │   ├── types/                     # 共享类型定义
│   │   │   │   ├── task.ts
│   │   │   │   ├── user.ts
│   │   │   │   ├── points.ts
│   │   │   │   ├── reward.ts
│   │   │   │   └── index.ts
│   │   │   ├── constants/                 # 共享常量
│   │   │   │   ├── task-types.ts
│   │   │   │   ├── point-rules.ts
│   │   │   │   └── index.ts
│   │   │   ├── utils/                     # 共享工具函数
│   │   │   │   ├── points-calculator.ts
│   │   │   │   ├── date-helpers.ts
│   │   │   │   └── validation.ts
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── ui/                                # 共享 UI 组件库
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── button/
│   │   │   │   ├── card/
│   │   │   │   ├── dialog/
│   │   │   │   ├── progress/
│   │   │   │   ├── avatar/
│   │   │   │   └── index.ts
│   │   │   ├── hooks/
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── config/                            # 共享配置
│       ├── eslint/
│       ├── typescript/
│       └── tailwind/
│
├── backend/                               # 后端 API 服务
│   ├── app/
│   │   ├── main.py                        # FastAPI 入口
│   │   ├── config.py                      # 配置管理
│   │   ├── dependencies.py                # 依赖注入
│   │   ├── api/                           # API 路由
│   │   │   ├── v1/
│   │   │   │   ├── router.py              # 路由汇总
│   │   │   │   ├── auth.py                # 认证接口
│   │   │   │   ├── users.py               # 用户接口
│   │   │   │   ├── tasks.py               # 任务接口
│   │   │   │   ├── points.py              # 积分接口
│   │   │   │   ├── rewards.py             # 奖励接口
│   │   │   │   ├── content.py             # 内容接口
│   │   │   │   ├── ai.py                  # AI 问答接口
│   │   │   │   └── reports.py             # 报告接口
│   │   │   └── deps.py
│   │   ├── models/                        # 数据模型（ORM）
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── family.py
│   │   │   ├── task.py
│   │   │   ├── point_transaction.py
│   │   │   ├── reward.py
│   │   │   └── content.py
│   │   ├── schemas/                       # Pydantic 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   ├── points.py
│   │   │   ├── reward.py
│   │   │   └── common.py
│   │   ├── services/                      # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── task_service.py
│   │   │   ├── point_service.py
│   │   │   ├── reward_service.py
│   │   │   ├── ai_service.py
│   │   │   └── report_service.py
│   │   ├── repositories/                  # 数据访问层
│   │   │   ├── __init__.py
│   │   │   ├── user_repo.py
│   │   │   ├── task_repo.py
│   │   │   ├── point_repo.py
│   │   │   └── reward_repo.py
│   │   ├── core/                          # 核心模块
│   │   │   ├── security.py                # 安全相关
│   │   │   ├── exceptions.py              # 异常定义
│   │   │   └── middleware.py              # 中间件
│   │   └── utils/                         # 工具函数
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── alembic/                           # 数据库迁移
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/                             # 测试
│   │   ├── conftest.py
│   │   ├── test_tasks.py
│   │   ├── test_points.py
│   │   └── test_rewards.py
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── docs/                                  # 项目文档
│   ├── api/                               # API 文档
│   ├── design/                            # 设计文档
│   └── guides/                            # 开发指南
│
├── .moai/                                 # MoAI 配置
│   └── project/
│       ├── product.md
│       ├── structure.md
│       └── tech.md
│
├── turbo.json                             # Turborepo 配置
├── package.json                           # 根 package.json
├── pnpm-workspace.yaml                    # pnpm workspace 配置
└── README.md
```

---

## 各目录职责说明

### apps/ - 应用层

#### parent-app/ - 家长端应用

| 目录 | 职责 |
|------|------|
| `app/` | Next.js App Router 页面路由 |
| `components/` | 页面级和功能组件 |
| `hooks/` | 状态逻辑复用 |
| `stores/` | 全局状态管理（Zustand） |
| `services/` | API 调用封装 |
| `lib/` | 工具函数和辅助方法 |

#### child-app/ - 孩子端应用

| 目录 | 职责 |
|------|------|
| `app/` | Next.js App Router 页面路由 |
| `components/animations/` | 动效组件（GSAP/Three.js） |
| `components/ui/` | 大尺寸适配的 UI 组件 |
| `hooks/` | 状态逻辑复用 |
| `stores/` | 全局状态管理 |
| `services/` | API 调用封装 |

### packages/ - 共享包

| 目录 | 职责 |
|------|------|
| `shared/` | 两端共享的业务类型、常量、工具 |
| `ui/` | 共享 UI 组件（基础组件） |
| `config/` | ESLint、TypeScript、Tailwind 共享配置 |

### backend/ - 后端服务

| 目录 | 职责 |
|------|------|
| `api/` | API 路由定义和请求处理 |
| `models/` | ORM 数据模型 |
| `schemas/` | Pydantic 请求/响应模型 |
| `services/` | 核心业务逻辑 |
| `repositories/` | 数据库操作封装 |
| `core/` | 安全、异常、中间件 |
| `alembic/` | 数据库版本迁移 |

---

## 模块组织方式

### 前端模块化原则

```
功能模块 = components + hooks + types + services
```

每个功能域保持内聚，通过以下方式组织：

1. **组件分层**
   - `ui/` - 基础 UI 组件（Button、Card、Dialog）
   - `feature/` - 业务功能组件（TaskCard、PointHistory）
   - `layout/` - 布局组件（Header、Sidebar、TabBar）

2. **状态管理**
   - 全局状态：Zustand stores（用户信息、应用配置）
   - 局部状态：React useState/useReducer
   - 服务端状态：直接通过 services 层管理

3. **类型共享**
   - 业务类型放在 `packages/shared/`
   - UI 组件类型放在 `packages/ui/`
   - 应用特有类型放在各自的 `types/`

### 后端分层架构

```
┌─────────────────────────────────────────┐
│              API Layer                   │
│  (路由、请求验证、响应格式化)            │
├─────────────────────────────────────────┤
│            Service Layer                 │
│  (业务逻辑、事务管理、跨模块协调)        │
├─────────────────────────────────────────┤
│          Repository Layer                │
│  (数据访问、ORM 操作、缓存)              │
├─────────────────────────────────────────┤
│            Model Layer                   │
│  (数据模型定义、关系映射)                │
└─────────────────────────────────────────┘
```

---

## 前后端分离架构

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
├────────────────────────────┬────────────────────────────────┤
│       家长端 App            │          孩子端 App            │
│  (Next.js + Tailwind)      │    (Next.js + Tailwind)        │
│                            │    + GSAP + Three.js           │
└─────────────┬──────────────┴───────────────┬────────────────┘
              │                               │
              │         REST API              │
              │     (JSON over HTTPS)         │
              └───────────────┬───────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                      后端 API 层                             │
│                    (FastAPI + Python)                       │
├─────────────────────────────────────────────────────────────┤
│  Auth  │  Users  │  Tasks  │  Points  │  Rewards  │  AI    │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                       数据层                                 │
├────────────────────────────┬────────────────────────────────┤
│     PostgreSQL/MySQL       │         Redis (缓存)           │
└────────────────────────────┴────────────────────────────────┘
```

### API 设计原则

1. **RESTful 风格**
   - 资源命名使用复数形式
   - HTTP 方法语义正确（GET/POST/PUT/DELETE）
   - 统一响应格式

2. **版本控制**
   - URL 路径版本：`/api/v1/`
   - 向后兼容

3. **认证授权**
   - JWT Token 认证
   - 家长端与孩子端权限隔离

---

## 数据流说明

### 任务完成流程

```
┌─────────┐    1. 查看任务列表    ┌─────────┐
│  孩子端  │ ──────────────────► │ 后端API  │
│         │                      │         │
│         │ ◄────────────────── │         │
└─────────┘    2. 返回任务数据    └─────────┘
     │
     │ 3. 完成任务并打卡
     ▼
┌─────────┐    4. 提交完成记录    ┌─────────┐
│  孩子端  │ ──────────────────► │ 后端API  │
│         │                      │         │
│         │                      │   保存   │
│         │                      │ Pending │
└─────────┘                      └─────────┘
                                      │
                                      │ 5. 推送通知
                                      ▼
                                 ┌─────────┐
                                 │  家长端  │
                                 │         │
                                 │ 收到审核 │
                                 │  请求   │
                                 └─────────┘
                                      │
                                      │ 6. 审核确认
                                      ▼
┌─────────┐    8. 积分到账通知    ┌─────────┐
│  孩子端  │ ◄────────────────── │ 后端API  │
│         │                      │         │
│ +积分   │ ◄────────────────── │ 更新余额 │
│ +动效   │    9. WebSocket推送  │ 记录流水 │
└─────────┘                      └─────────┘
```

### 积分健康检测流程

```
┌──────────────────────────────────────────────────────┐
│                   定时任务（每日）                    │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│ 1. 计算当月赚取积分总额                              │
│ 2. 计算当月扣除积分总额                              │
│ 3. 判断: 扣除 > 赚取 * 50% ?                        │
└─────────────────────────┬───────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │        是             │ 否
              ▼                       ▼
    ┌─────────────────┐      ┌─────────────────┐
    │ 生成健康预警     │      │   正常状态      │
    │ 推送家长端通知   │      │                 │
    └─────────────────┘      └─────────────────┘
```

### 数据同步策略

1. **乐观更新** - 孩子端打卡时先本地更新状态，失败后回滚
2. **WebSocket** - 积分变动实时推送到两端
3. **轮询降级** - WebSocket 断开时自动切换轮询
4. **离线缓存** - 任务列表支持本地缓存，网络恢复后同步

---

## Monorepo 工具链

### Turborepo 配置

```json
{
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {
      "dependsOn": ["^lint"]
    },
    "test": {
      "dependsOn": ["^build"]
    }
  }
}
```

### 常用命令

```bash
# 安装依赖
pnpm install

# 启动所有应用开发模式
pnpm dev

# 构建所有应用
pnpm build

# 只构建家长端
pnpm --filter parent-app build

# 只启动后端
cd backend && python -m uvicorn app.main:app --reload
```

---

*文档版本: 1.0*
*最后更新: 2024*
