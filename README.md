# 集成教务管理系统 — 基于XML数据集成技术

## 项目概述

本系统基于 **XML数据集成技术**，将学院A（SQL Server）、学院B（Oracle）、学院C（MySQL）三个**真实异构数据库**的教务系统互联互通，实现跨院系课程共享。

核心特性：
- **异构DBMS**: 底层使用三种不同的数据库管理系统（SQL Server / Oracle / MySQL）
- **透明性**：屏蔽底层数据库差异，用户无需关注数据分布
- **可扩展性**：基于XML标准格式进行数据交换，采用XSLT进行格式转换
- **健壮性**：XML Schema验证保证数据规范性
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
                              │  (本地安装)  │
                              └─────────────┘
```

## 数据库架构

| 组件 | 数据库系统 | 端口 | 表名风格 | 列名风格 |
|------|-----------|------|---------|---------|
| 学院A | Microsoft SQL Server 2022 | 1433 | 中文（账号表、学生表...） | 中文（学号、姓名...） |
| 学院B | Oracle XE 21c | 1521 | 中文（账户表、学生表...） | 中文（编号、名字...） |
| 学院C | MySQL 8.0 (本地) | 3306 | 中文（账户表、学生表...） | 英文缩写（Sno、Snm...） |

各学院的表结构和字段名称不同，模拟真实异构数据库环境。通过统一XML格式进行数据交换。

## 环境要求

- Python 3.8+
- Docker Desktop （用于运行 SQL Server 和 Oracle 容器）
- MySQL 8.0 （本地安装，学院C使用）
- pip（Python包管理器）

## 从零启动步骤

### 步骤1：安装Python依赖

```bash
pip install -r requirements.txt
```

依赖包说明：
- **Flask**：Web应用框架，用于构建各学院和集成服务器的GUI界面
- **lxml**：XML处理库，用于XML生成、解析和XSLT转换
- **requests**：HTTP客户端库，用于集成服务器与各学院之间的通信
- **sqlalchemy**：数据库抽象层，统一访问三种异构数据库
- **pymssql**：SQL Server 数据库驱动（纯Python）
- **oracledb**：Oracle 数据库驱动（Thin模式，无需客户端）
- **pymysql**：MySQL 数据库驱动（纯Python）

### 步骤2：启动数据库容器

```bash
docker compose up -d
```

首次启动会自动下载 SQL Server、Oracle、MySQL 镜像（约 5-10 分钟）。

等待所有容器健康检查通过：

```bash
docker compose ps
# 三个容器的 STATUS 应显示 "(healthy)"
```

### 步骤3：生成测试数据

```bash
python -c "import sys; sys.path.insert(0, '.'); from college.data_generator import generate_college_data; generate_college_data()"
```

该步骤会为每个学院生成：
- 50名学生信息（中文姓名、随机专业）
- 10门课程信息（含课程名称、学分、授课教师、上课地点）
- 250条选课记录（每名学生选修5门课程）
- 1个管理员账号（admin / admin123）

数据分别写入 **SQL Server**、**Oracle**、**MySQL** 三个数据库。

### 步骤4：启动所有服务器

```bash
python run.py
```

启动后终端将显示：

```
============================================================
  集成教务管理系统 — 启动中...
  基于XML数据集成技术 — 异构数据库版
============================================================

[数据库] 所有数据库容器已就绪
[系统] 数据库已有数据，跳过数据生成

[A] 启动于 http://127.0.0.1:5001
[B] 启动于 http://127.0.0.1:5002
[C] 启动于 http://127.0.0.1:5003
[集成服务器] 启动于 http://127.0.0.1:5000
```

### 步骤5：访问系统

打开浏览器访问以下地址：

| 系统 | 地址 | 说明 |
|------|------|------|
| 集成服务器 | http://127.0.0.1:5000 | 跨院选课、退课、统一统计 |
| 学院A教务系统 | http://127.0.0.1:5001/login | SQL Server，中文列名 |
| 学院B教务系统 | http://127.0.0.1:5002/login | Oracle，中文列名（不同命名） |
| 学院C教务系统 | http://127.0.0.1:5003/login | MySQL，英文缩写列名 |

### 步骤6：测试功能

#### 6.1 各学院独立登录

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 可查看学生、课程、统计信息 |
| 学生 | STUA001 | 123456 | 学院A学生（SQL Server） |
| 学生 | STUB010 | 123456 | 学院B学生（Oracle） |
| 学生 | STUC020 | 123456 | 学院C学生（MySQL） |

#### 6.2 跨院选课

1. 打开集成服务器 http://127.0.0.1:5000
2. 点击导航栏「跨院选课」
3. 输入学号（如 `STUA001`）和课程编号（如 `COUB001`）
4. 点击「确认选课」，学生STUA001（学院A）即选修了COUB001（学院B）的课程

#### 6.3 退选课程

1. 在集成服务器点击导航栏「退选课程」
2. 输入学号和要退选的课程编号
3. 点击「确认退课」

#### 6.4 查看统计数据

在集成服务器点击「统计信息」，可看到：
- 三个学院的学生总数、课程总数、选课记录总数
- 各学院详细统计信息

### 步骤7：停止服务器

在 run.py 终端中按 `Ctrl+C` 停止所有服务器。

停止数据库容器（SQL Server + Oracle）：

```bash
docker compose down
```

如需同时删除数据库数据卷（完全重置）：

```bash
docker compose down -v
```

> 注意：学院C的 MySQL 是本地服务，不会随 Docker 停止。

## 项目结构

```
hw3/
├── docker-compose.yml               # 三数据库容器编排
├── run.py                           # 一键启动所有服务器
├── requirements.txt                 # Python依赖清单
├── shared/                          # 共享模块
│   ├── __init__.py                  # 统一XML格式常量
│   └── xml_schemas.py               # XML Schema定义（XSD）
├── college/                         # 学院教务系统
│   ├── app.py                       # 可配置Flask应用
│   ├── db.py                        # 数据库操作层（SQLAlchemy Core）
│   ├── xml_api.py                   # XML数据导出/导入
│   ├── data_generator.py            # 测试数据生成器
│   ├── configs/                     # 三学院异构配置
│   │   ├── college_a.json          # 学院A配置（SQL Server）
│   │   ├── college_b.json          # 学院B配置（Oracle）
│   │   └── college_c.json          # 学院C配置（MySQL）
│   └── templates/                   # 学院前端模板
│       ├── login.html
│       ├── student_dashboard.html
│       └── admin_dashboard.html
├── integration/                     # 集成服务器
│   ├── app.py                       # 集成服务器应用
│   ├── templates/
│   │   └── integrated_dashboard.html
│   ├── xslt/                        # XSLT转换文件（12个）
│   │   ├── formatStudent.xsl       # → 统一学生格式
│   │   ├── formatClass.xsl         # → 统一课程格式
│   │   ├── formatChoice.xsl        # → 统一选课格式
│   │   ├── studentToA.xsl          # → 学院A格式
│   │   ├── studentToB.xsl          # → 学院B格式
│   │   ├── studentToC.xsl          # → 学院C格式
│   │   ├── classToA.xsl            # → 学院A格式
│   │   ├── classToB.xsl            # → 学院B格式
│   │   ├── classToC.xsl            # → 学院C格式
│   │   ├── choiceToA.xsl           # → 学院A格式
│   │   ├── choiceToB.xsl           # → 学院B格式
│   │   └── choiceToC.xsl           # → 学院C格式
│   └── schema/                      # XML Schema验证文件
│       ├── student.xsd
│       ├── class.xsd
│       └── choice.xsd
└── data/                            # Docker数据卷挂载目录
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
| 学分列 | 学分 | 学时 | Cpt |
| 教师列 | 授课教师 | 教师 | Tec |
| 地点列 | 授课地点 | 地点 | Pla |
| 成绩列 | 成绩 | 得分 | Grd |

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

# MySQL (学院C — 本地安装)
mysql -u root -p123456 college_c
```

## 常见问题

**Q: 启动时提示 Docker 未运行？**
A: 请先启动 Docker Desktop，确保 Docker 引擎正在运行。

**Q: 数据库容器启动超时？**
A: 首次启动需要下载镜像，可能需要 5-10 分钟。可用 `docker-compose logs -f` 查看进度。

**Q: 端口被占用？**
A: 检查端口 1433、1521、3306、5000-5003 是否被其他程序占用。

**Q: 选课提示"可能已选过该课程"？**
A: 同一学生不能重复选修同一门课程。如需重新测试，重新生成数据即可。

**Q: 如何完全重置？**
A:
```bash
# 1. 重置 Docker 容器（SQL Server + Oracle）
docker compose down -v
docker compose up -d

# 2. 重置本地 MySQL
mysql -u root -p123456 -e "DROP DATABASE IF EXISTS college_c; CREATE DATABASE college_c CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 3. 重新生成测试数据
python -c "import sys; sys.path.insert(0, '.'); from college.data_generator import generate_college_data; generate_college_data()"
```
