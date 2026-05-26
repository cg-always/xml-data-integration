# 集成教务管理系统 — 基于XML数据集成技术

## 项目概述

本系统基于 **XML数据集成技术**，将学院A（SQL Server）、学院B（Oracle）、学院C（MySQL）三个异构数据库的教务系统互联互通，实现跨院系课程共享。

核心特性：
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
  └───────────┘         └────────────┬────────────┘         └───────────┘
                                     │
                                     │ XML
                                     │
                              ┌──────┴──────┐
                              │   学院C      │
                              │   MySQL     │
                              │   :5003     │
                              └─────────────┘
```

## 环境要求

- Python 3.8+
- pip（Python包管理器）

## 从零启动步骤

### 步骤1：安装Python依赖

```bash
pip install flask lxml requests
```

这三个包的作用：
- **Flask**：Web应用框架，用于构建各学院和集成服务器的GUI界面
- **lxml**：XML处理库，用于XML生成、解析和XSLT转换
- **requests**：HTTP客户端库，用于集成服务器与各学院之间的通信

### 步骤2：生成测试数据

```bash
cd "C:\Users\Y\Desktop\数据集成\hw3"
python -c "import sys; sys.path.insert(0, '.'); from college.data_generator import generate_college_data; generate_college_data()"
```

该步骤会为每个学院自动生成：
- 50名学生信息（中文姓名、随机专业）
- 10门课程信息（含课程名称、学分、授课教师、上课地点）
- 250条选课记录（每名学生选修5门课程）
- 1个管理员账号（admin / admin123）

生成的数据存储在 `data/` 目录下的三个SQLite数据库文件中。

### 步骤3：启动所有服务器

```bash
python run.py
```

启动后终端将显示：

```
============================================================
  集成教务管理系统 — 启动中...
  基于XML数据集成技术
============================================================

[A] 启动于 http://127.0.0.1:5001
[B] 启动于 http://127.0.0.1:5002
[C] 启动于 http://127.0.0.1:5003
[集成服务器] 启动于 http://127.0.0.1:5000
```

### 步骤4：访问系统

打开浏览器访问以下地址：

| 系统 | 地址 | 说明 |
|------|------|------|
| 集成服务器 | http://127.0.0.1:5000 | 跨院选课、退课、统一统计 |
| 学院A教务系统 | http://127.0.0.1:5001/login | SQL Server模拟，中文列名 |
| 学院B教务系统 | http://127.0.0.1:5002/login | Oracle模拟，中文列名（不同命名） |
| 学院C教务系统 | http://127.0.0.1:5003/login | MySQL模拟，英文缩写列名 |

### 步骤5：测试功能

#### 5.1 各学院独立登录

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 可查看学生、课程、统计信息 |
| 学生 | STUA001 | 123456 | 学院A学生，可查看已选课程 |
| 学生 | STUB010 | 123456 | 学院B学生 |
| 学生 | STUC020 | 123456 | 学院C学生 |

#### 5.2 跨院选课

1. 打开集成服务器 http://127.0.0.1:5000
2. 点击导航栏「跨院选课」
3. 输入学号（如 `STUA001`）和课程编号（如 `COUB001`）
4. 点击「确认选课」，学生STUA001（学院A）即选修了COUB001（学院B）的课程

#### 5.3 退选课程

1. 在集成服务器点击导航栏「退选课程」
2. 输入学号和要退选的课程编号
3. 点击「确认退课」

#### 5.4 查看统计数据

在集成服务器点击「统计信息」，可看到：
- 三个学院的学生总数、课程总数、选课记录总数
- 各学院详细统计信息

### 步骤6：停止服务器

在终端中按 `Ctrl+C` 停止所有服务器。

## 项目结构

```
hw3/
├── run.py                          # 一键启动所有服务器
├── requirements.txt                # Python依赖清单
├── shared/                         # 共享模块
│   ├── __init__.py                 # 统一XML格式常量
│   └── xml_schemas.py              # XML Schema定义（XSD）
├── college/                        # 学院教务系统
│   ├── app.py                      # 可配置Flask应用（含原生/统一XML API、XSD验证）
│   ├── db.py                       # 数据库操作层（含共享课程查询）
│   ├── xml_api.py                  # XML数据导出/导入（原生格式+统一格式）
│   ├── data_generator.py           # 测试数据生成器
│   ├── configs/                    # 三学院异构配置
│   │   ├── college_a.json         # 学院A配置
│   │   ├── college_b.json         # 学院B配置
│   │   └── college_c.json         # 学院C配置
│   └── templates/                  # 学院前端模板
│       ├── login.html
│       ├── student_dashboard.html
│       └── admin_dashboard.html
├── integration/                    # 集成服务器
│   ├── app.py                      # 集成服务器应用
│   ├── templates/
│   │   └── integrated_dashboard.html
│   ├── xslt/                       # XSLT转换文件（12个）
│   │   ├── formatStudent.xsl      # 学院格式 → 统一学生格式
│   │   ├── formatClass.xsl        # 学院格式 → 统一课程格式
│   │   ├── formatChoice.xsl       # 学院格式 → 统一选课格式
│   │   ├── studentToA.xsl         # 统一格式 → 学院A学生格式
│   │   ├── studentToB.xsl         # 统一格式 → 学院B学生格式
│   │   ├── studentToC.xsl         # 统一格式 → 学院C学生格式
│   │   ├── classToA.xsl           # 统一格式 → 学院A课程格式
│   │   ├── classToB.xsl           # 统一格式 → 学院B课程格式
│   │   ├── classToC.xsl           # 统一格式 → 学院C课程格式
│   │   ├── choiceToA.xsl          # 统一格式 → 学院A选课格式
│   │   ├── choiceToB.xsl          # 统一格式 → 学院B选课格式
│   │   └── choiceToC.xsl          # 统一格式 → 学院C选课格式
│   └── schema/                     # XML Schema验证文件
│       ├── student.xsd
│       ├── class.xsd
│       └── choice.xsd
└── data/                           # 数据库文件目录
    ├── college_a.db                # 学院A数据库
    ├── college_b.db                # 学院B数据库
    └── college_c.db                # 学院C数据库
```

## 异构数据库设计

系统通过不同的表名和列名模拟三个异构DBMS：

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
6. 目标学院解析XML，写入本地数据库，返回结果
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
4. 目标学院XSD验证XML，解析后删除本地选课记录，返回结果
```

### 查询跨院选课记录

```
1. 学生在集成服务器「我的选课」页面输入学号
       │
2. 集成服务器通过XSLT从各学院获取原生选课XML → 转为统一格式
       │
3. 筛选该学生的跨院选课记录（排除本院课程）
       │
4. 补充课程名称等详情后展示给用户
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

## 数据集成技术要点

### XSLT 格式转换

集成服务器通过 XSLT 将各学院的原生 XML 格式（使用各自数据库的实际列名）转换为统一 XML 格式：

| 转换方向 | XSLT 文件 | 说明 |
|----------|-----------|------|
| 学院格式 → 统一 | `formatStudent.xsl` | 将学院 A/B/C 的学生 XML 转为统一格式 |
| 学院格式 → 统一 | `formatClass.xsl` | 将学院 A/B/C 的课程 XML 转为统一格式 |
| 学院格式 → 统一 | `formatChoice.xsl` | 将学院 A/B/C 的选课 XML 转为统一格式 |
| 统一 → 学院格式 | `studentToA.xsl` 等 | 将统一格式转回各学院原生格式 |

### XML Schema 验证

- 统一格式的 XML 数据在 XSLT 转换后、导入目标学院前均经过 XSD Schema 验证
- Schema 文件位于 `integration/schema/`：`student.xsd`、`class.xsd`、`choice.xsd`

### 课程共享标记

- 每门课程包含 `shared`（共享标记）字段
- 值为 1 表示该课程开放跨院选课，0 表示仅限本院
- 集成服务器的「共享课程」页面仅展示标记为共享的课程

## 常见问题

**Q: 启动时提示端口被占用？**
A: 检查是否有其他程序占用了 5000-5003 端口。可在各配置文件中修改端口号。

**Q: 集成服务器显示"离线"？**
A: 确保所有学院服务器都已启动（步骤3的启动日志中会显示四个URL）。

**Q: 选课提示"可能已选过该课程"？**
A: 同一学生不能重复选修同一门课程。如需重新测试，重新生成数据即可。
