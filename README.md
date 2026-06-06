# 集成教务管理系统 — 基于 XML 数据集成技术

## 项目概述

本系统基于 **XML 数据集成技术**，将学院A（SQL Server）、学院B（Oracle）、学院C（MySQL）三个**真实异构数据库**的教务系统互联互通，实现跨院系课程共享。

核心特性：
- **异构 DBMS**：底层使用三种不同的数据库管理系统（SQL Server / Oracle / MySQL），全部通过 Docker 容器运行
- **透明性**：屏蔽底层数据库差异，用户无需关注数据分布
- **可扩展性**：基于 XML 标准格式进行数据交换，采用 XSLT 进行格式转换
- **健壮性**：XML Schema 验证保证数据规范性
- **安全性**：各学院独立认证，数据按需暴露

## 技术架构

```
                        ┌─────────────────────────┐
                        │      集成服务器           │
                        │      :5000              │
                        │  ─────────────────────  │
  ┌───────────┐         │  XSLT 格式转换           │          ┌───────────┐
  │  学院A    │   XML    │  XML Schema 验证        │   XML    │  学院B    │
  │ SQL Server│◄───────►│  跨院选课 / 退课          │◄───────►│  Oracle   │
  │  :5001    │         │  统一统计查询             │         │  :5002    │
  │ (Docker)  │         └────────────┬────────────┘         │ (Docker)  │
  └───────────┘                      │                      └───────────┘
                                     │ XML
                                     │
                              ┌──────┴──────┐
                              │   学院C      │
                              │   MySQL     │
                              │   :5003     │
                              │  (Docker)   │
                              └─────────────┘
```

## 数据库架构

| 组件 | 数据库系统 | 端口 | 表名风格 | 列名风格 |
|------|-----------|------|---------|---------|
| 学院A | Microsoft SQL Server 2022 | 1433 | 中文（账号表、学生表...） | 中文（学号、姓名...） |
| 学院B | Oracle XE 21c | 1521 | 中文（账户表、学生表...） | 中文（编号、名字...） |
| 学院C | MySQL 8.0 | 3307 | 中文（账户表、学生表...） | 英文缩写（Sno、Snm...） |

各学院的表结构和字段名称不同，模拟真实异构数据库环境。通过统一XML格式进行数据交换。

> **注意**：学院B（Oracle）的课程表中「学分」和「学时」的列名语义与学院A相反，体现了异构数据库中"数据意义差异"的特征。

## 环境要求

- Python 3.8+
- Docker Desktop（用于运行全部三个数据库容器）
- pip（Python包管理器）

> **不需要**单独安装 SQL Server、Oracle 或 MySQL — 全部通过 Docker 提供。

## 从零启动步骤

### 步骤 1：安装 Python 依赖

```bash
cd xml-data-integration
pip install -r requirements.txt
```

依赖包说明：
- **Flask**：Web 应用框架，用于构建各学院和集成服务器的 GUI 界面
- **lxml**：XML 处理库，用于 XML 生成、解析和 XSLT 转换
- **requests**：HTTP 客户端库，用于集成服务器与各学院之间的通信
- **sqlalchemy**：数据库抽象层，统一访问三种异构数据库
- **pymssql**：SQL Server 数据库驱动（纯 Python，无需 ODBC）
- **oracledb**：Oracle 数据库驱动（Thin 模式，无需 Oracle Instant Client）
- **pymysql**：MySQL 数据库驱动（纯 Python）

### 步骤 2：启动数据库容器

```bash
docker compose up -d
```

首次启动会自动下载 SQL Server、Oracle、MySQL 三个镜像（约 5-10 分钟，取决于网络速度）。

等待所有容器健康检查通过：

```bash
docker compose ps
# 三个容器的 STATUS 应显示 "(healthy)"
```

### 步骤 3：一键启动系统

```bash
python run.py
```

首次运行会自动生成测试数据（50 名学生 + 10 门课程 + 250 条选课记录），然后启动全部四个服务器：

```
============================================================
  集成教务管理系统 — 启动中...
  基于XML数据集成技术 — 异构数据库版
============================================================

[数据库] 所有数据库容器已就绪
[系统] 首次运行，正在生成测试数据...
[系统] 学院A → SQL Server  |  学院B → Oracle  |  学院C → MySQL

  学院A: 50 学生, 10 课程, 250 选课记录 → 已写入 SQL Server
  学院B: 50 学生, 10 课程, 250 选课记录 → 已写入 Oracle
  学院C: 50 学生, 10 课程, 250 选课记录 → 已写入 MySQL

所有测试数据已生成完成！

[A] 启动于 http://127.0.0.1:5001
[B] 启动于 http://127.0.0.1:5002
[C] 启动于 http://127.0.0.1:5003
[集成服务器] 启动于 http://127.0.0.1:5000
```

### 步骤 4：访问系统

打开浏览器访问以下地址：

| 系统 | 地址 | 说明 |
|------|------|------|
| 集成服务器 | http://127.0.0.1:5000 | 跨院选课、退课、统一统计 |
| 学院A教务系统 | http://127.0.0.1:5001/login | SQL Server，中文列名 |
| 学院B教务系统 | http://127.0.0.1:5002/login | Oracle，中文列名（不同命名） |
| 学院C教务系统 | http://127.0.0.1:5003/login | MySQL，英文缩写列名 |

### 步骤 5：测试功能

#### 5.1 各学院独立登录

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 可查看学生、课程、统计信息 |
| 学生 | STUA001 | 123456 | 学院A 学生（SQL Server） |
| 学生 | STUB010 | 123456 | 学院B 学生（Oracle） |
| 学生 | STUC020 | 123456 | 学院C 学生（MySQL） |

#### 5.2 跨院选课

1. 打开集成服务器 http://127.0.0.1:5000
2. 点击导航栏「跨院选课」
3. 输入学号（如 `STUA001`）和课程编号（如 `COUB001`）
4. 点击「确认选课」，学生 STUA001（学院A）即选修了 COUB001（学院B）的课程

#### 5.3 退选课程

1. 在集成服务器点击导航栏「退选课程」
2. 输入学号和要退选的课程编号
3. 点击「确认退课」

#### 5.4 查看统计数据

在集成服务器点击「统计信息」，可看到：
- 三个学院的学生总数、课程总数、选课记录总数
- 各学院详细统计信息

### 步骤 6：停止系统

在 `run.py` 终端中按 `Ctrl+C` 停止所有服务器。

停止并删除数据库容器：

```bash
# 停止容器（保留数据）
docker compose down

# 停止容器并删除数据卷（完全重置）
docker compose down -v
```

## 项目结构

```
xml-data-integration/
├── docker-compose.yml               # 三数据库容器编排（SQL Server + Oracle + MySQL）
├── run.py                           # 一键启动所有服务器 + 自动生成测试数据
├── requirements.txt                 # Python 依赖清单
├── README.md                        # 本文档
├── shared/                          # 共享模块
│   ├── __init__.py                  # 统一 XML 格式常量定义
│   └── xml_schemas.py               # XML Schema 定义（XSD）
├── college/                         # 学院教务系统
│   ├── app.py                       # 可配置 Flask 应用（三学院共用）
│   ├── db.py                        # 数据库操作层（SQLAlchemy Core，支持三种 DBMS）
│   ├── xml_api.py                   # XML 数据导出/导入（统一格式 ↔ 本地格式）
│   ├── data_generator.py            # 测试数据生成器（50 学生 + 10 课程 + 250 选课）
│   ├── configs/                     # 三学院异构配置
│   │   ├── college_a.json          # 学院A 配置（SQL Server，中文列名）
│   │   ├── college_b.json          # 学院B 配置（Oracle，中文列名，不同命名 + 语义交换）
│   │   └── college_c.json          # 学院C 配置（MySQL，英文缩写列名）
│   └── templates/                   # 学院前端模板
│       ├── login.html               # 登录页面
│       ├── student_dashboard.html   # 学生控制面板
│       └── admin_dashboard.html     # 管理员控制面板
├── integration/                     # 集成服务器
│   ├── app.py                       # 集成服务器主应用（跨院选课、退课、统计）
│   ├── templates/
│   │   └── integrated_dashboard.html # 集成服务器前端
│   ├── xslt/                        # XSLT 样式表（12 个）
│   │   ├── formatStudent.xsl       # 学院格式 → 统一学生格式
│   │   ├── formatClass.xsl         # 学院格式 → 统一课程格式
│   │   ├── formatChoice.xsl        # 学院格式 → 统一选课格式
│   │   ├── studentToA.xsl          # 统一格式 → 学院A 学生格式
│   │   ├── studentToB.xsl          # 统一格式 → 学院B 学生格式
│   │   ├── studentToC.xsl          # 统一格式 → 学院C 学生格式
│   │   ├── classToA.xsl            # 统一格式 → 学院A 课程格式
│   │   ├── classToB.xsl            # 统一格式 → 学院B 课程格式
│   │   ├── classToC.xsl            # 统一格式 → 学院C 课程格式
│   │   ├── choiceToA.xsl           # 统一格式 → 学院A 选课格式
│   │   ├── choiceToB.xsl           # 统一格式 → 学院B 选课格式
│   │   └── choiceToC.xsl           # 统一格式 → 学院C 选课格式
│   └── schema/                      # XML Schema 验证文件
│       ├── student.xsd              # 学生统一格式校验
│       ├── class.xsd                # 课程统一格式校验
│       └── choice.xsd               # 选课统一格式校验
└── .gitignore
```

## 异构数据库设计

系统使用三个不同DBMS，各自有不同的表结构和字段命名：

| 逻辑概念 | 学院A (SQL Server) | 学院B (Oracle) | 学院C (MySQL) |
|----------|-------------------|----------------|---------------|
| 账户表名 | 账号表 | 账户表 | 账户表 |
| 学生表名 | 学生表 | 学生表 | 学生表 |
| 课程表名 | 课程表 | 课程表 | 课程表 |
| 选课表名 | 选课表 | 选课表 | 选课表 |
| 学号列 | 学号 | 编号 | Sno |
| 姓名列 | 姓名 | 名字 | Snm |
| 性别列 | 性别 | 性别 | Sex |
| 专业列 | 院系 | 专业 | Sde |
| 课程编号列 | 课程编号 | 编号 | Cno |
| 课程名称列 | 课程名称 | 名称 | Cnm |
| 学分列 | 学分 | 学时⚠️ | Cpt |
| 教师列 | 授课教师 | 教师 | Tec |
| 地点列 | 授课地点 | 地点 | Pla |
| 学时列 | 学时 | 学分⚠️ | time |
| 成绩列 | 成绩 | 得分 | Grd |

> ⚠️ 学院B的「学分」和「学时」列名语义与其他学院相反 — 体现了异构数据库系统中"数据意义差异"的典型特征。

## 数据集成流程

### 跨院选课流程

```
1. 学生在集成服务器提交选课请求（学号 + 课程编号）
       │
2. 集成服务器识别学号和课程所属学院
       │
3. 向学生所在学院验证学生身份（HTTP GET /api/student/{id}）
       │
4. 构建统一XML格式的选课数据（Choices/choice/sid+cid+score）
       │
5. POST XML到目标学院的导入接口（/api/xml/enrollments/import）
       │
6. 目标学院解析XML，写入本地数据库（SQL Server/Oracle/MySQL），返回结果
       │
7. 集成服务器向用户展示选课结果
```

### 跨院退课流程

```
1. 学生在集成服务器提交退课请求
       │
2. 集成服务器构建删除XML（与选课格式相同）
       │
3. POST XML到目标学院的删除接口（/api/xml/enrollments/delete）
       │
4. 目标学院解析XML，删除本地选课记录，返回结果
```

### XML数据交换格式

统一XML格式屏蔽了各学院数据库的结构差异：

```xml
<!-- 课程统一XML格式 -->
<?xml version="1.0" encoding="utf-8"?>
<Classes college="A">
  <class>
    <id>COUA001</id>
    <name>高等数学</name>
    <score>2</score>
    <time>64</time>
    <teacher>刘副教授</teacher>
    <location>综合楼E502</location>
  </class>
</Classes>

<!-- 选课统一XML格式 -->
<?xml version="1.0" encoding="utf-8"?>
<Choices>
  <choice>
    <sid>STUA001</sid>
    <cid>COUB001</cid>
    <score>0</score>
  </choice>
</Choices>
```

## 直接连接数据库

如需直接查看各数据库中的数据，可使用以下命令：

```bash
# SQL Server (学院A)
docker exec -it college_a_sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "CollegeA_Pass123!" -C -d CollegeA

# Oracle (学院B)
docker exec -it college_b_oracle sqlplus system/CollegeB_Pass123@XEPDB1

# MySQL (学院C)
docker exec -it college_c_mysql mysql -u root -p123456 college_c
```

## 常见问题

**Q: 启动时提示 Docker 未运行？**
A: 请先启动 Docker Desktop，确保 Docker 引擎正在运行。

**Q: 数据库容器启动超时？**
A: 首次启动需要下载镜像（SQL Server ~1.5GB, Oracle ~3GB, MySQL ~500MB），可能需要 5-10 分钟。可用 `docker compose logs -f` 查看各容器启动进度。

**Q: 端口被占用？**
A: 检查端口 1433、1521、3307、5000-5003 是否被其他程序占用。可使用 `netstat -ano | findstr <端口号>` 检查。

> **注意**：学院C（MySQL）默认使用端口 3307（而非标准 3306），以避免与本机已有 MySQL 服务冲突。如需改回 3306，请同步修改 `docker-compose.yml` 和 `college/configs/college_c.json` 中的端口配置。

**Q: 选课提示"可能已选过该课程"？**
A: 同一学生不能重复选修同一门课程。如需重新测试，重新生成数据即可。

**Q: 学院A数据显示乱码？**
A: 本项目已使用 `NVARCHAR`（Unicode）列类型和 `Latin1_General_100_CI_AS_SC_UTF8` 数据库排序规则，确保 SQL Server 正确存储中文字符。如仍有问题，请完全重置数据：

```bash
docker compose down -v
docker compose up -d
# 等待所有容器 healthy 后：
python run.py
```

**Q: 如何完全重置？**
A:
```bash
# 1. 停止所有容器并删除数据卷
docker compose down -v

# 2. 重新启动容器
docker compose up -d

# 3. 等待容器健康检查通过后，启动系统（自动重新生成数据）
python run.py
```

## 技术要点

### SQL Server 中文支持

学院A 使用 SQL Server 2022。为确保中文字符正确存储和显示，系统进行了以下处理：

1. **列类型**：所有字符串列使用 `NVARCHAR`（SQLAlchemy `Unicode` 类型），支持完整 Unicode 字符集
2. **数据库排序规则**：`Latin1_General_100_CI_AS_SC_UTF8`，支持 UTF-8 编码
3. **连接编码**：pymssql 连接使用 `charset=utf8`

### 异构语义映射

学院B（Oracle）的课程表中「学分」和「学时」列名语义与学院A 相反，XSLT 样式表提供了完整的双向映射转换：

| 转换方向 | 文件 | 功能 |
|---------|------|------|
| 学院A 格式 → 统一格式 | formatClass.xsl | 识别各学院列名，输出统一 XML |
| 统一格式 → 学院A 格式 | classToA.xsl | 正确映射 score↔学分, time↔学时 |
| 统一格式 → 学院B 格式 | classToB.xsl | 正确映射 score↔学时, time↔学分 |
| 统一格式 → 学院C 格式 | classToC.xsl | 正确映射 score↔Cpt, time↔time |
