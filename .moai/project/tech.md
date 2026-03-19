# BabyEco 技术文档

## 技术栈总览

```
┌─────────────────────────────────────────────────────────────┐
│                         前端技术栈                           │
├─────────────────────────────────────────────────────────────┤
│  框架: Next.js 22                                           │
│  样式: Tailwind CSS + CSS Variables                         │
│  组件: shadcn/ui + Radix UI                                 │
│  动效: GSAP 3 + Framer Motion + React Spring                │
│  3D:   Three.js + React Three Fiber (可选)                  │
│  状态: Zustand                                              │
├─────────────────────────────────────────────────────────────┤
│                         后端技术栈                           │
├─────────────────────────────────────────────────────────────┤
│  语言: Python 3.11+                                         │
│  框架: FastAPI                                              │
│  ORM:  SQLAlchemy 2.0                                       │
│  数据库: PostgreSQL / MySQL                                 │
│  缓存: Redis                                                │
├─────────────────────────────────────────────────────────────┤
│                         基础设施                             │
├─────────────────────────────────────────────────────────────┤
│  包管理: pnpm + Turborepo                                   │
│  容器化: Docker + Docker Compose                            │
│  CI/CD: GitHub Actions                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 前端技术选型及理由

### 核心框架

#### Next.js 22

**选型理由:**
- React 生态最成熟的 SSR/SSG 框架
- App Router 提供现代化路由方案
- 内置优化（图片、字体、代码分割）
- 支持 PWA，可渐进式升级为原生应用
- Turborepo 原生支持，适合 Monorepo 架构

**关键特性使用:**
- Server Components：首页看板、报告页面
- Client Components：交互密集的页面（任务打卡、AI 对话）
- API Routes：BFF 层（可选）

### 样式方案

#### Tailwind CSS + CSS Variables

**选型理由:**
- Tailwind：原子化 CSS，开发效率高，无样式冲突
- CSS Variables：支持运行时主题切换（孩子端可能需要个性化主题）

**主题配置:**
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // 孩子端活泼配色
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        accent: 'var(--color-accent)',
        // 大按钮、大字体规范
        'touch-target': '48px',
        'touch-primary': '60px',
      },
      fontSize: {
        // 6-12岁适配字体
        'child-base': ['18px', '28px'],
        'child-lg': ['24px', '36px'],
      }
    }
  }
}
```

### 组件库

#### shadcn/ui + Radix UI

**选型理由:**
- shadcn/ui：可定制性强，代码直接拷贝到项目
- Radix UI：无障碍支持完善，交互行为可靠
- 不引入额外设计系统约束

**定制方向:**
- 孩子端：放大点击区域，增强视觉反馈
- 家长端：保持标准尺寸，信息密度适中

### 动效方案

#### GSAP 3（主力动效）

**选型理由:**
- 性能优异，适合复杂时间线动画
- ScrollTrigger：滚动驱动动画
- Flip Plugin：列表重排动画（任务列表排序）

**使用场景:**
- 任务完成庆祝动效（彩带、星星）
- 积分增长动画
- 进度条填充动画

#### Framer Motion（页面过渡）

**选型理由:**
- React 友好，声明式 API
- 页面级转场动画
- 手势交互支持

**使用场景:**
- 页面切换过渡
- 卡片滑动手势
- 模态框动画

#### React Spring（物理交互）

**选型理由:**
- 物理弹性动效更自然
- 适合拖拽、弹性反馈

**使用场景:**
- 按钮点击反馈
- 拖拽排序
- 下拉刷新

### 3D 增强（可选）

#### Three.js + React Three Fiber

**选型理由:**
- React Three Fiber：React 声明式 3D 开发
- 可选模块，不影响核心功能

**使用场景:**
- 成就徽章 3D 展示
- 积分积累 3D 可视化
- 节日主题 3D 装饰

### 状态管理

#### Zustand

**选型理由:**
- 极简 API，学习成本低
- 无 Provider 包裹，使用方便
- 支持 persist 中间件
- TypeScript 支持完善

**Store 设计:**
```typescript
// stores/useUserStore.ts
interface UserState {
  user: User | null;
  points: number;
  setUser: (user: User) => void;
  updatePoints: (delta: number) => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      points: 0,
      setUser: (user) => set({ user }),
      updatePoints: (delta) => set((state) => ({
        points: state.points + delta
      })),
    }),
    { name: 'user-storage' }
  )
);
```

---

## 后端技术选型及理由

### 核心框架

#### FastAPI

**选型理由:**
- 高性能异步框架
- 自动生成 OpenAPI 文档
- Pydantic 数据验证
- 类型提示友好，开发体验好

**项目结构:**
```python
# app/main.py
from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(
    title="BabyEco API",
    version="1.0.0",
)

app.include_router(api_router, prefix="/api/v1")
```

### ORM 选择

#### SQLAlchemy 2.0

**选型理由:**
- Python 生态最成熟的 ORM
- 2.0 版本支持 async
- 支持复杂查询和关系映射

**模型示例:**
```python
# models/task.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    points = Column(Integer, default=0)
    task_type = Column(String(20))  # daily, timed, family
    family_id = Column(Integer, ForeignKey("families.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    family = relationship("Family", back_populates="tasks")
```

---

## 数据库选型建议

### 主数据库：PostgreSQL

**选型理由:**
- 开源免费，社区活跃
- JSONB 支持（灵活的任务配置存储）
- 良好的并发性能
- 支持全文检索（搜索功能）

**备选：MySQL 8.0+**
- 团队熟悉度高时可选
- 云服务商支持广泛

### 缓存：Redis

**使用场景:**
- Session 存储
- 积分余额缓存（高频读取）
- 排行榜（ZRANGE）
- 发布订阅（实时通知）

**数据结构设计:**
```
# 积分缓存
points:{user_id} -> integer

# 任务完成缓存
task:completed:{user_id}:{date} -> set

# 排行榜
leaderboard:{family_id}:{month} -> sorted_set
```

---

## 开发环境要求

### 必需软件

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Node.js | >= 20.0.0 | 前端运行时 |
| pnpm | >= 9.0.0 | 包管理器 |
| Python | >= 3.11 | 后端运行时 |
| PostgreSQL | >= 15 | 主数据库 |
| Redis | >= 7.0 | 缓存服务 |
| Docker | >= 24.0 | 容器化（可选） |

### 环境变量

#### 前端

```bash
# apps/parent-app/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# apps/child-app/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

#### 后端

```bash
# backend/.env
DATABASE_URL=postgresql://user:password@localhost:5432/babyeco
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
AI_API_KEY=your-ai-api-key  # AI 问答服务
```

### 本地开发启动

```bash
# 1. 安装依赖
pnpm install

# 2. 启动数据库（Docker）
docker-compose up -d postgres redis

# 3. 初始化数据库
cd backend
alembic upgrade head

# 4. 启动后端
uvicorn app.main:app --reload --port 8000

# 5. 启动前端（新终端）
pnpm dev
```

---

## 构建和部署配置

### 前端构建

#### Next.js 配置

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',  // Docker 部署优化
  images: {
    domains: ['api.babyeco.com'],
  },
  experimental: {
    optimizePackageImports: ['@radix-ui', 'gsap'],
  },
};

module.exports = nextConfig;
```

#### Dockerfile（前端）

```dockerfile
# apps/child-app/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
COPY . .
RUN npm install -g pnpm
RUN pnpm install --frozen-lockfile
RUN pnpm --filter child-app build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/apps/child-app/.next/standalone ./
COPY --from=builder /app/apps/child-app/.next/static ./apps/child-app/.next/static
COPY --from=builder /app/apps/child-app/public ./apps/child-app/public

EXPOSE 3000
CMD ["node", "apps/child-app/server.js"]
```

### 后端构建

#### Dockerfile（后端）

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 运行
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: babyeco
      POSTGRES_PASSWORD: babyeco123
      POSTGRES_DB: babyeco
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://babyeco:babyeco123@postgres:5432/babyeco
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  parent-app:
    build:
      context: .
      dockerfile: apps/parent-app/Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend

  child-app:
    build:
      context: .
      dockerfile: apps/child-app/Dockerfile
    ports:
      - "3001:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### CI/CD（GitHub Actions）

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 9

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm lint

      - name: Build
        run: pnpm build

      - name: Test
        run: pnpm test

  backend-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          pytest
```

---

## 依赖清单

### 前端核心依赖

```json
{
  "dependencies": {
    "next": "^22.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwindcss": "^3.4.0",
    "@radix-ui/react-dialog": "^1.0.0",
    "@radix-ui/react-tabs": "^1.0.0",
    "gsap": "^3.12.0",
    "framer-motion": "^11.0.0",
    "react-spring": "^9.7.0",
    "zustand": "^4.5.0",
    "three": "^0.160.0",
    "@react-three/fiber": "^8.15.0",
    "@react-three/drei": "^9.90.0",
    "axios": "^1.6.0",
    "socket.io-client": "^4.7.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0",
    "@types/node": "^20.10.0",
    "@types/react": "^18.2.0"
  }
}
```

### 后端核心依赖

```txt
# requirements.txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
redis>=5.0.0
httpx>=0.26.0
pytest>=7.4.0
pytest-asyncio>=0.23.0
```

---

## API 设计规范

### 统一响应格式

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "任务不存在",
    "details": {}
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 主要 API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | /api/v1/auth/login | 用户登录 |
| GET | /api/v1/tasks | 获取任务列表 |
| POST | /api/v1/tasks | 创建任务（家长端） |
| POST | /api/v1/tasks/{id}/complete | 完成任务打卡 |
| POST | /api/v1/tasks/{id}/review | 审核任务（家长端） |
| GET | /api/v1/points/balance | 获取积分余额 |
| GET | /api/v1/points/history | 获取积分流水 |
| POST | /api/v1/rewards | 创建奖励 |
| POST | /api/v1/rewards/{id}/redeem | 兑换奖励 |
| POST | /api/v1/ai/chat | AI 问答 |

---

## 性能优化建议

### 前端优化

1. **代码分割**
   - 按路由自动分割
   - 大型组件动态导入

2. **图片优化**
   - Next.js Image 组件自动优化
   - 使用 WebP 格式

3. **动效性能**
   - GSAP 使用 `will-change` 提示
   - 避免布局抖动（Layout Thrashing）

### 后端优化

1. **数据库**
   - 合理使用索引
   - 连接池配置

2. **缓存策略**
   - 积分余额 Redis 缓存
   - 热点数据预加载

3. **异步处理**
   - 报告生成使用后台任务
   - 通知推送异步执行

---

*文档版本: 1.0*
*最后更新: 2024*
