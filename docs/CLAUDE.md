# PCB 远程设计环境

## 架构

```
本地 Mac (无 EDA 软件)          VPS (KiCad 9.0.6)
┌─────────────────────┐         ┌─────────────────────┐
│  Claude Code        │   MCP   │  MCP Server v3.4    │
│  ~/workdir/pcb/     │◄──SSH──►│  kicad-cli + pcbnew │
└─────────────────────┘         │  + FreeRouting      │
                                │  + 异步任务系统     │
                                └─────────────────────┘
```

## 可用 MCP 工具 (22 个)

### 检查类
| 工具 | 功能 | 示例 |
|------|------|------|
| `run_drc` | DRC 设计规则检查 (PCB) | "检查 DRC" |
| `run_erc` | ERC 电气规则检查 (原理图) | "检查 ERC" |

### 操作类
| 工具 | 功能 | 示例 |
|------|------|------|
| `fill_zones` | 填充所有 Zone (铜皮) | "填充铜皮" |
| `auto_route` | **FreeRouting 自动布线 (异步)** | "自动布线" |

### 异步任务
| 工具 | 功能 | 示例 |
|------|------|------|
| `get_task_status` | 查询任务状态 | "查询任务 xxx" |
| `list_tasks` | 列出所有任务 | "列出任务" |

### 信息类
| 工具 | 功能 | 示例 |
|------|------|------|
| `list_projects` | 列出所有项目 | "列出项目" |
| `get_board_info` | 板子尺寸/层数/元件数 | "板子信息" |
| `get_output_files` | 列出输出文件 | "查看输出" |
| `get_version` | 版本信息 | "查看版本" |

### PCB 导出
| 工具 | 功能 | 示例 |
|------|------|------|
| `export_gerber` | Gerber + 钻孔 | "导出 Gerber" |
| `export_3d` | 3D 渲染图 | "生成 3D" |
| `export_svg` | PCB SVG 图片 | "导出 SVG" |
| `export_pdf` | PCB PDF | "导出 PDF" |
| `export_step` | STEP 3D 模型 | "导出 STEP" |

### 原理图导出
| 工具 | 功能 | 示例 |
|------|------|------|
| `export_bom` | BOM 物料清单 | "导出 BOM" |
| `export_netlist` | 网表导出 | "导出网表" |
| `export_sch_pdf` | 原理图 PDF | "导出原理图" |
| `export_sch_svg` | 原理图 SVG | "原理图 SVG" |

### 生产制造
| 工具 | 功能 | 示例 |
|------|------|------|
| `export_jlcpcb` | JLCPCB 完整包 | "生成嘉立创文件" |
| `export_all` | 导出所有文件 | "导出所有" |

### 文件操作
| 工具 | 功能 |
|------|------|
| `read_file` | 读取文件内容 |

## 自动布线说明 (异步模式)

`auto_route` 默认使用异步模式运行：

### 工作流程
```
1. 调用 auto_route → 立即返回 task_id
2. 后台 FreeRouting 运行 (不受 10 分钟限制)
3. 调用 get_task_status 查询进度
4. 完成后 PCB 文件自动更新
```

### 参数
- `project` - 项目名
- `max_passes` - 最大布线尝试次数 (默认 100)
- `async_mode` - 异步模式 (默认 true)

### 状态查询
```
get_task_status task_id=route_xxx_20241231_123456
```

返回状态：
- `started` - 正在运行
- `completed` - 已完成
- `failed` - 失败

### 备份
自动布线前会备份到 `output/backup/`

## 自动化规则

| 用户说 | 调用工具 |
|--------|----------|
| "列出项目" | `list_projects` |
| "板子信息" / "尺寸" | `get_board_info` |
| "DRC" / "设计检查" | `run_drc` |
| "ERC" / "电气检查" | `run_erc` |
| "填充" / "铜皮" / "Zone" | `fill_zones` |
| "自动布线" / "布线" | `auto_route` |
| "任务状态" / "查询任务" | `get_task_status` |
| "列出任务" | `list_tasks` |
| "Gerber" | `export_gerber` |
| "BOM" / "物料" | `export_bom` |
| "网表" | `export_netlist` |
| "3D" / "渲染" | `export_3d` |
| "SVG" / "图片" | `export_svg` |
| "PDF" | `export_pdf` |
| "原理图" | `export_sch_pdf` |
| "STEP" / "模型" | `export_step` |
| "JLCPCB" / "嘉立创" | `export_jlcpcb` |
| "全部" / "所有" | `export_all` |

## 路径说明

| 位置 | 路径 |
|------|------|
| 本地项目 | `~/workdir/pcb/<project>/` |
| VPS 项目 | `/root/pcb/projects/<project>/` |
| VPS 输出 | `/root/pcb/projects/<project>/output/` |
| VPS 任务 | `/root/pcb/tasks/` |

## 输出目录结构

```
output/
├── gerber/      # Gerber + 钻孔文件
├── bom/         # BOM CSV
├── netlist/     # 网表文件
├── 3d/          # 3D 渲染 PNG + STEP
├── images/      # SVG 图片 (PCB + 原理图)
├── docs/        # PDF 文档 (PCB + 原理图)
├── reports/     # DRC/ERC 报告
├── jlcpcb/      # JLCPCB 完整包
└── backup/      # 自动布线前备份
```

## 同步命令

```bash
# 上传项目到 VPS
pcb-sync push <project>

# 下载结果到本地
pcb-sync pull <project>
```

## 环境信息

- KiCad: 9.0.6
- MCP Server: v3.4
- pcbnew API: 可用
- FreeRouting: 可用 (异步自动布线)
- 异步任务: 支持 (绕过 10 分钟限制)
- 功能: DRC, ERC, Zone 填充, 异步自动布线, 板子信息, 3D 渲染, Gerber, BOM, 网表, PDF, SVG, STEP, JLCPCB
