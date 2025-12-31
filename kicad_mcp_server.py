#!/usr/bin/env python3
"""
KiCad MCP Server v3.4
KiCad 9.x 专用，完整功能版

功能:
- DRC/ERC 检查
- Zone 填充
- 板子信息查询
- Gerber/钻孔/BOM/位置文件导出
- 3D 渲染
- 原理图 PDF/SVG 导出
- 网表导出
- JLCPCB 完整包
- FreeRouting 自动布线 (异步支持)
"""

import json
import sys
import os
import subprocess
import base64
import glob
import shutil
from datetime import datetime

PROJECTS_BASE = "/root/pcb/projects"
KICAD_CLI = "kicad-cli"
FREEROUTING_JAR = "/opt/freerouting.jar"
JAVA_CMD = "java"

# KiCad Python API
try:
    import pcbnew
    HAS_PCBNEW = True
except ImportError:
    HAS_PCBNEW = False

def log(msg):
    print(f"[MCP] {msg}", file=sys.stderr)

def run_cmd(cmd, cwd=None, use_xvfb=False):
    if use_xvfb:
        cmd = ["xvfb-run", "-a"] + cmd
    log(f"执行: {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=300)
        return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

def find_pcb(d):
    f = glob.glob(os.path.join(d, "*.kicad_pcb"))
    return f[0] if f else None

def find_sch(d):
    f = glob.glob(os.path.join(d, "*.kicad_sch"))
    return f[0] if f else None

def ensure_dirs(d):
    for x in ["output/gerber", "output/bom", "output/3d", "output/reports", 
              "output/jlcpcb", "output/docs", "output/images", "output/netlist"]:
        os.makedirs(os.path.join(d, x), exist_ok=True)

# ============================================================
# 工具实现
# ============================================================

def tool_list_projects():
    """列出所有项目"""
    projects = []
    if os.path.exists(PROJECTS_BASE):
        for n in os.listdir(PROJECTS_BASE):
            p = os.path.join(PROJECTS_BASE, n)
            if os.path.isdir(p) and not n.startswith('.'):
                pcb = find_pcb(p)
                sch = find_sch(p)
                projects.append({
                    "name": n,
                    "has_pcb": pcb is not None,
                    "has_sch": sch is not None,
                    "pcb_file": os.path.basename(pcb) if pcb else None
                })
    return {"projects": projects, "count": len(projects)}

def tool_run_drc(project):
    """DRC 设计规则检查"""
    d = os.path.join(PROJECTS_BASE, project)
    pcb = find_pcb(d)
    if not pcb:
        return {"error": f"PCB 文件未找到: {project}"}
    ensure_dirs(d)
    out = os.path.join(d, "output/reports/drc_report.json")
    
    r = run_cmd([KICAD_CLI, "pcb", "drc", pcb, "--severity-all", "--format", "json", "--output", out])
    
    if r["success"] and os.path.exists(out):
        with open(out) as f:
            data = json.load(f)
        v = data.get("violations", [])
        return {
            "success": True,
            "violations": len(v),
            "file": out,
            "summary": [{"type": x.get("type"), "desc": x.get("description")} for x in v[:10]]
        }
    return {"success": False, "error": r.get("stderr", r.get("error"))}

def tool_run_erc(project):
    """ERC 原理图电气检查"""
    d = os.path.join(PROJECTS_BASE, project)
    sch = find_sch(d)
    if not sch:
        return {"error": f"原理图文件未找到: {project}"}
    ensure_dirs(d)
    out = os.path.join(d, "output/reports/erc_report.json")
    
    r = run_cmd([KICAD_CLI, "sch", "erc", sch, "--severity-all", "--format", "json", "--output", out])
    
    if r["success"] and os.path.exists(out):
        with open(out) as f:
            data = json.load(f)
        v = data.get("violations", data.get("errors", []))
        return {
            "success": True,
            "violations": len(v) if isinstance(v, list) else 0,
            "file": out,
            "summary": [{"type": x.get("type"), "desc": x.get("description")} for x in (v[:10] if isinstance(v, list) else [])]
        }
    return {"success": False, "error": r.get("stderr", r.get("error"))}

def tool_fill_zones(project):
    """填充所有 Zone (铜皮)"""
    if not HAS_PCBNEW:
        return {"error": "pcbnew 模块不可用"}
    
    d = os.path.join(PROJECTS_BASE, project)
    pcb_file = find_pcb(d)
    if not pcb_file:
        return {"error": f"PCB 文件未找到: {project}"}
    
    try:
        board = pcbnew.LoadBoard(pcb_file)
        zones = board.Zones()
        zone_count = zones.size() if hasattr(zones, 'size') else len(list(zones))
        
        if zone_count == 0:
            return {"success": True, "message": "没有 Zone 需要填充", "zones": 0}
        
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(board.Zones())
        pcbnew.SaveBoard(pcb_file, board)
        
        return {
            "success": True,
            "message": f"已填充 {zone_count} 个 Zone",
            "zones": zone_count,
            "file": pcb_file
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================
# 异步任务系统
# ============================================================

TASKS_DIR = "/root/pcb/tasks"

def get_task_file(task_id):
    return os.path.join(TASKS_DIR, f"{task_id}.json")

def save_task(task_id, data):
    os.makedirs(TASKS_DIR, exist_ok=True)
    with open(get_task_file(task_id), 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_task(task_id):
    tf = get_task_file(task_id)
    if os.path.exists(tf):
        with open(tf) as f:
            return json.load(f)
    return None

def tool_auto_route(project, max_passes=100, async_mode=True):
    """FreeRouting 自动布线 (默认异步)"""
    if not HAS_PCBNEW:
        return {"error": "pcbnew 模块不可用"}
    
    if not os.path.exists(FREEROUTING_JAR):
        return {"error": f"FreeRouting 未安装: {FREEROUTING_JAR}"}
    
    d = os.path.join(PROJECTS_BASE, project)
    pcb_file = find_pcb(d)
    if not pcb_file:
        return {"error": f"PCB 文件未找到: {project}"}
    
    ensure_dirs(d)
    
    # 创建备份
    backup_dir = os.path.join(d, "output/backup")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"before_autoroute_{timestamp}.kicad_pcb")
    shutil.copy(pcb_file, backup_file)
    
    # 临时文件
    dsn_file = os.path.join(d, "output/temp_route.dsn")
    ses_file = os.path.join(d, "output/temp_route.ses")
    
    # 导出 DSN
    try:
        board = pcbnew.LoadBoard(pcb_file)
        pcbnew.ExportSpecctraDSN(board, dsn_file)
        log(f"DSN 导出完成: {dsn_file}")
    except Exception as e:
        return {"success": False, "error": f"DSN 导出失败: {e}"}
    
    if async_mode:
        # 异步模式：后台执行
        task_id = f"route_{project}_{timestamp}"
        
        # 创建后台脚本
        script = f'''#!/bin/bash
cd {d}
echo "started" > /root/pcb/tasks/{task_id}.status

xvfb-run -a java -jar {FREEROUTING_JAR} -de {dsn_file} -do {ses_file} -mp {max_passes} > /root/pcb/tasks/{task_id}.log 2>&1

if [ -f "{ses_file}" ]; then
    python3 << 'PYEOF'
import pcbnew
board = pcbnew.LoadBoard("{pcb_file}")
pcbnew.ImportSpecctraSES(board, "{ses_file}")
pcbnew.SaveBoard("{pcb_file}", board)
print("SES imported")
PYEOF
    rm -f {dsn_file} {ses_file}
    echo "completed" > /root/pcb/tasks/{task_id}.status
else
    echo "failed" > /root/pcb/tasks/{task_id}.status
fi
'''
        script_file = f"/root/pcb/tasks/{task_id}.sh"
        os.makedirs(TASKS_DIR, exist_ok=True)
        with open(script_file, 'w') as f:
            f.write(script)
        os.chmod(script_file, 0o755)
        
        # 保存任务信息
        save_task(task_id, {
            "id": task_id,
            "type": "auto_route",
            "project": project,
            "status": "running",
            "started_at": timestamp,
            "backup": backup_file,
            "pcb": pcb_file
        })
        
        # 后台启动
        subprocess.Popen(
            ["nohup", "bash", script_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        return {
            "success": True,
            "async": True,
            "task_id": task_id,
            "message": f"自动布线任务已启动，使用 get_task_status 查询进度",
            "backup": backup_file
        }
    
    else:
        # 同步模式（保留，但有超时风险）
        try:
            cmd = [
                "xvfb-run", "-a",
                JAVA_CMD, "-jar", FREEROUTING_JAR,
                "-de", dsn_file,
                "-do", ses_file,
                "-mp", str(max_passes)
            ]
            
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if not os.path.exists(ses_file):
                return {"success": False, "error": "FreeRouting 未生成 SES 文件"}
            
            board = pcbnew.LoadBoard(pcb_file)
            pcbnew.ImportSpecctraSES(board, ses_file)
            pcbnew.SaveBoard(pcb_file, board)
            
            os.remove(dsn_file) if os.path.exists(dsn_file) else None
            os.remove(ses_file) if os.path.exists(ses_file) else None
            
            return {
                "success": True,
                "message": "自动布线完成",
                "backup": backup_file,
                "pcb": pcb_file
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "自动布线超时 (>10分钟)，建议使用异步模式"}
        except Exception as e:
            return {"success": False, "error": str(e)}

def tool_get_task_status(task_id):
    """查询异步任务状态"""
    task = load_task(task_id)
    if not task:
        return {"error": f"任务不存在: {task_id}"}
    
    status_file = os.path.join(TASKS_DIR, f"{task_id}.status")
    log_file = os.path.join(TASKS_DIR, f"{task_id}.log")
    
    # 读取状态
    status = "unknown"
    if os.path.exists(status_file):
        with open(status_file) as f:
            status = f.read().strip()
    
    # 读取日志尾部
    log_tail = ""
    if os.path.exists(log_file):
        with open(log_file) as f:
            lines = f.readlines()
            log_tail = ''.join(lines[-10:])
    
    task["status"] = status
    task["log_tail"] = log_tail
    
    if status == "completed":
        task["message"] = "自动布线完成！PCB 文件已更新"
    elif status == "failed":
        task["message"] = "自动布线失败，查看日志了解详情"
    elif status == "started":
        task["message"] = "正在布线中..."
    
    return task

def tool_list_tasks():
    """列出所有任务"""
    if not os.path.exists(TASKS_DIR):
        return {"tasks": [], "count": 0}
    
    tasks = []
    for f in os.listdir(TASKS_DIR):
        if f.endswith('.json'):
            task_id = f[:-5]
            task = load_task(task_id)
            if task:
                status_file = os.path.join(TASKS_DIR, f"{task_id}.status")
                if os.path.exists(status_file):
                    with open(status_file) as sf:
                        task["status"] = sf.read().strip()
                tasks.append(task)
    
    return {"tasks": tasks, "count": len(tasks)}

def tool_get_board_info(project):
    """获取板子信息"""
    if not HAS_PCBNEW:
        return {"error": "pcbnew 模块不可用"}
    
    d = os.path.join(PROJECTS_BASE, project)
    pcb_file = find_pcb(d)
    if not pcb_file:
        return {"error": f"PCB 文件未找到: {project}"}
    
    try:
        board = pcbnew.LoadBoard(pcb_file)
        
        # 板子尺寸
        bbox = board.GetBoardEdgesBoundingBox()
        width_mm = bbox.GetWidth() / 1000000.0
        height_mm = bbox.GetHeight() / 1000000.0
        
        # 层数
        layer_count = board.GetCopperLayerCount()
        
        # 元件统计
        footprints = board.GetFootprints()
        fp_count = len(footprints)
        
        smd_count = 0
        tht_count = 0
        for fp in footprints:
            if fp.GetAttributes() & pcbnew.FP_SMD:
                smd_count += 1
            elif fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE:
                tht_count += 1
        
        # 网络数
        netinfo = board.GetNetInfo()
        net_count = netinfo.GetNetCount()
        
        # Zone 数
        zones = board.Zones()
        zone_count = zones.size() if hasattr(zones, 'size') else len(list(zones))
        
        # 过孔数
        tracks = board.GetTracks()
        via_count = sum(1 for t in tracks if t.GetClass() == "PCB_VIA")
        
        return {
            "success": True,
            "board": {
                "width_mm": round(width_mm, 2),
                "height_mm": round(height_mm, 2),
                "area_mm2": round(width_mm * height_mm, 2),
                "layers": layer_count
            },
            "components": {
                "total": fp_count,
                "smd": smd_count,
                "tht": tht_count
            },
            "nets": net_count,
            "zones": zone_count,
            "vias": via_count
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def tool_export_gerber(project):
    """导出 Gerber + 钻孔文件"""
    d = os.path.join(PROJECTS_BASE, project)
    pcb = find_pcb(d)
    if not pcb:
        return {"error": f"PCB 文件未找到: {project}"}
    ensure_dirs(d)
    out = os.path.join(d, "output/gerber")
    
    r1 = run_cmd([KICAD_CLI, "pcb", "export", "gerbers", "--output", out + "/", pcb])
    r2 = run_cmd([KICAD_CLI, "pcb", "export", "drill", "--output", out + "/", pcb])
    
    if r1["success"] and r2["success"]:
        files = os.listdir(out)
        return {"success": True, "dir": out, "files": files, "count": len(files)}
    return {"success": False, "error": (r1.get("stderr", "") + " " + r2.get("stderr", "")).strip()}

def tool_export_bom(project):
    """导出 BOM"""
    d = os.path.join(PROJECTS_BASE, project)
    sch = find_sch(d)
    if not sch:
        return {"error": f"原理图文件未找到: {project}"}
    ensure_dirs(d)
    out = os.path.join(d, "output/bom/bom.csv")
    
    r = run_cmd([KICAD_CLI, "sch", "export", "bom", "--output", out, sch])
    
    if r["success"] and os.path.exists(out):
        with open(out) as f:
            lines = f.readlines()
        return {"success": True, "file": out, "lines": len(lines), "preview": lines[:5]}
    return {"success": False, "error": r.get("stderr", r.get("error"))}

def tool_export_netlist(project, format="kicadxml"):
    """导出网表"""
    d = os.path.join(PROJECTS_BASE, project)
    sch = find_sch(d)
    if not sch:
        return {"error": f"原理图文件未找到: {project}"}
    ensure_dirs(d)
    
    ext_map = {"kicadxml": "xml", "cadstar": "cir", "orcadpcb2": "net", "spice": "cir"}
    ext = ext_map.get(format, "net")
    out = os.path.join(d, f"output/netlist/netlist.{ext}")
    
    r = run_cmd([KICAD_CLI, "sch", "export", "netlist", "--format", format, "--output", out, sch])
    
    if r["success"] and os.path.exists(out):
        return {"success": True, "file": out, "format": format}
    return {"success": False, "error": r.get("stderr", r.get("error"))}

def tool_export_sch_pdf(project):
    """导出原理图 PDF"""
    d = os.path.join(PROJECTS_BASE, project)
    sch = find_sch(d)
    if not sch:
        return {"error": f"原理图文件未找到: {project}"}
    ensure_dirs(d)
    out = os.path.join(d, "output/docs/schematic.pdf")
    
    r = run_cmd([KICAD_CLI, "sch", "export", "pdf", "--output", out, sch])
    
    if r["success"] and os.path.exists(out):
        return {"success": True, "file": out}
    return {"success": False, "error": r.get("stderr", r.get("error"))}

def tool_export_sch_svg(project):
    """导出原理图 SVG"""
    d = os.path.join(PROJECTS_BASE, project)
    sch = find_sch(d)
    if not sch:
        return {"error": f"原理图文件未找到: {project}"}
    ensure_dirs(d)
    out_dir = os.path.join(d, "output/images")
    
    r = run_cmd([KICAD_CLI, "sch", "export", "svg", "--output", out_dir + "/", sch])
    
    if r["success"]:
        svg_files = glob.glob(os.path.join(out_dir, "*.svg"))
        return {"success": True, "files": svg_files}
    return {"success": False, "error": r.get("stderr", r.get("error"))}

def tool_export_3d(project, view="top"):
    """3D 渲染"""
    d = os.path.join(PROJECTS_BASE, project)
    pcb = find_pcb(d)
    if not pcb:
        return {"error": f"PCB 文件未找到: {project}"}
    ensure_dirs(d)
    out_dir = os.path.join(d, "output/3d")
    
    views_config = {
        "top": {"side": "top", "rotate": None},
        "bottom": {"side": "bottom", "rotate": None},
        "front": {"side": "front", "rotate": None},
        "back": {"side": "back", "rotate": None},
        "iso": {"side": "top", "rotate": "30,0,-45"},
        "iso_back": {"side": "bottom", "rotate": "30,0,135"}
    }
    
    if view == "all":
        views_to_render = ["top", "bottom", "iso"]
    elif view in views_config:
        views_to_render = [view]
    else:
        return {"error": f"未知视图: {view}，可选: top, bottom, front, back, iso, iso_back, all"}
    
    results = {}
    for v in views_to_render:
        cfg = views_config[v]
        out_file = os.path.join(out_dir, f"pcb_{v}.png")
        
        cmd = [
            KICAD_CLI, "pcb", "render",
            "--output", out_file,
            "--width", "1920",
            "--height", "1080",
            "--side", cfg["side"],
            "--quality", "high",
            "--background", "opaque",
            "--perspective"
        ]
        
        if cfg.get("rotate"):
            cmd.extend(["--rotate", cfg["rotate"]])
        
        cmd.append(pcb)
        
        r = run_cmd(cmd, cwd=d, use_xvfb=True)
        success = r["success"] and os.path.exists(out_file)
        
        results[v] = {
            "success": success,
            "file": out_file if success else None,
            "size": f"{os.path.getsize(out_file)/1024:.1f}KB" if success else None,
            "error": r.get("stderr") if not success else None
        }
    
    success_count = sum(1 for r in results.values() if r["success"])
    files = [r["file"] for r in results.values() if r["file"]]
    
    return {
        "success": success_count > 0,
        "results": results,
        "files": files,
        "message": f"生成 {success_count}/{len(views_to_render)} 个 3D 渲染图"
    }

def tool_export_svg(project, view="all"):
    """导出 PCB SVG 图片"""
    d = os.path.join(PROJECTS_BASE, project)
    pcb = find_pcb(d)
    if not pcb:
        return {"error": f"PCB 文件未找到: {project}"}
    ensure_dirs(d)
    out_dir = os.path.join(d, "output/images")
    
    views_config = {
        "top": {"layers": "F.Cu,F.SilkS,F.Mask,Edge.Cuts", "mirror": False},
        "bottom": {"layers": "B.Cu,B.SilkS,B.Mask,Edge.Cuts", "mirror": True}
    }
    
    if view == "all":
        views_to_render = list(views_config.keys())
    elif view in views_config:
        views_to_render = [view]
    else:
        return {"error": f"未知视图: {view}，可选: top, bottom, all"}
    
    results = {}
    for v in views_to_render:
        cfg = views_config[v]
        out_file = os.path.join(out_dir, f"pcb_{v}.svg")
        
        cmd = [
            KICAD_CLI, "pcb", "export", "svg",
            "--output", out_file,
            "--layers", cfg["layers"],
            "--page-size-mode", "2",
            "--exclude-drawing-sheet"
        ]
        
        if cfg["mirror"]:
            cmd.append("--mirror")
        
        cmd.append(pcb)
        
        r = run_cmd(cmd, cwd=d)
        success = r["success"] and os.path.exists(out_file)
        results[v] = {"success": success, "file": out_file if success else None}
    
    files = [r["file"] for r in results.values() if r["file"]]
    return {"success": len(files) > 0, "files": files, "results": results}

def tool_export_pdf(project, layers="all"):
    """导出 PCB PDF"""
    d = os.path.join(PROJECTS_BASE, project)
    pcb = find_pcb(d)
    if not pcb:
        return {"error": f"PCB 文件未找到: {project}"}
    ensure_dirs(d)
    
    layer_sets = {
        "top": "F.Cu,F.SilkS,F.Mask,Edge.Cuts",
        "bottom": "B.Cu,B.SilkS,B.Mask,Edge.Cuts",
        "all": "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
    }
    
    layer_str = layer_sets.get(layers, layers)
    out_file = os.path.join(d, f"output/docs/pcb_{layers}.pdf")
    
    r = run_cmd([KICAD_CLI, "pcb", "export", "pdf", "--output", out_file, "--layers", layer_str, pcb])
    
    if r["success"] and os.path.exists(out_file):
        return {"success": True, "file": out_file}
    return {"success": False, "error": r.get("stderr", r.get("error"))}

def tool_export_step(project):
    """导出 STEP 3D 模型"""
    d = os.path.join(PROJECTS_BASE, project)
    pcb = find_pcb(d)
    if not pcb:
        return {"error": f"PCB 文件未找到: {project}"}
    ensure_dirs(d)
    out_file = os.path.join(d, "output/3d/pcb.step")
    
    r = run_cmd([KICAD_CLI, "pcb", "export", "step", "--output", out_file, "--subst-models", pcb])
    
    if r["success"] and os.path.exists(out_file):
        size = os.path.getsize(out_file)
        return {"success": True, "file": out_file, "size": f"{size/1024/1024:.1f}MB"}
    return {"success": False, "error": r.get("stderr", r.get("error"))}

def tool_export_jlcpcb(project):
    """JLCPCB 完整制造包"""
    d = os.path.join(PROJECTS_BASE, project)
    pcb = find_pcb(d)
    sch = find_sch(d)
    if not pcb:
        return {"error": f"PCB 文件未找到: {project}"}
    
    jd = os.path.join(d, "output/jlcpcb")
    os.makedirs(jd, exist_ok=True)
    
    results = {}
    
    r1 = run_cmd([KICAD_CLI, "pcb", "export", "gerbers", "--output", jd + "/", pcb])
    r2 = run_cmd([KICAD_CLI, "pcb", "export", "drill", "--output", jd + "/", pcb])
    results["gerber"] = r1["success"] and r2["success"]
    
    if sch:
        bom_file = os.path.join(jd, "bom.csv")
        r3 = run_cmd([KICAD_CLI, "sch", "export", "bom", "--output", bom_file, sch])
        results["bom"] = r3["success"]
    else:
        results["bom"] = False
    
    pos_file = os.path.join(jd, "position.csv")
    r4 = run_cmd([
        KICAD_CLI, "pcb", "export", "pos",
        "--output", pos_file,
        "--format", "csv",
        "--units", "mm",
        "--side", "both",
        "--smd-only",
        pcb
    ])
    results["position"] = r4["success"] and os.path.exists(pos_file)
    
    files = os.listdir(jd) if os.path.exists(jd) else []
    
    return {
        "success": results["gerber"],
        "results": results,
        "dir": jd,
        "files": files,
        "count": len(files),
        "message": "JLCPCB 文件包已生成"
    }

def tool_export_all(project):
    """导出所有文件"""
    results = {}
    
    results["drc"] = tool_run_drc(project)
    results["erc"] = tool_run_erc(project)
    results["gerber"] = tool_export_gerber(project)
    results["bom"] = tool_export_bom(project)
    results["3d"] = tool_export_3d(project, "all")
    results["svg"] = tool_export_svg(project, "all")
    results["sch_pdf"] = tool_export_sch_pdf(project)
    
    d = os.path.join(PROJECTS_BASE, project, "output")
    total_files = sum(len(files) for _, _, files in os.walk(d)) if os.path.exists(d) else 0
    
    return {
        "success": True,
        "results": results,
        "total_files": total_files,
        "output_dir": d
    }

def tool_get_files(project):
    """获取输出文件列表"""
    d = os.path.join(PROJECTS_BASE, project, "output")
    if not os.path.exists(d):
        return {"files": [], "error": "输出目录不存在"}
    
    files = []
    for root, _, fnames in os.walk(d):
        for f in fnames:
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, d)
            size = os.path.getsize(fp)
            files.append({
                "name": f,
                "path": rel,
                "full_path": fp,
                "size": f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
            })
    return {"files": files, "count": len(files)}

def tool_read_file(filepath):
    """读取文件内容"""
    if not os.path.exists(filepath):
        return {"error": f"文件不存在: {filepath}"}
    
    size = os.path.getsize(filepath)
    if size > 10 * 1024 * 1024:
        return {"error": "文件过大 (>10MB)"}
    
    ext = os.path.splitext(filepath)[1].lower()
    binary_exts = {'.png', '.jpg', '.jpeg', '.gif', '.zip', '.pdf', '.step', '.glb'}
    
    if ext in binary_exts:
        with open(filepath, 'rb') as f:
            content = base64.b64encode(f.read()).decode()
        return {"encoding": "base64", "content": content, "size": size}
    else:
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
        return {"encoding": "utf-8", "content": content, "size": size}

def tool_version():
    """获取版本信息"""
    r = run_cmd([KICAD_CLI, "--version"])
    freerouting_ok = os.path.exists(FREEROUTING_JAR)
    return {
        "kicad": r["stdout"].strip() if r["success"] else "未安装",
        "pcbnew_api": HAS_PCBNEW,
        "freerouting": freerouting_ok,
        "mcp_server": "3.4",
        "features": [
            "drc", "erc", "fill_zones", "board_info", 
            "auto_route_async", "task_status",
            "gerber", "drill", "bom", "netlist", "pos",
            "3d_render", "svg", "pdf", "step",
            "sch_pdf", "sch_svg"
        ]
    }

# ============================================================
# MCP 协议
# ============================================================

TOOLS = {
    "list_projects": {
        "desc": "列出所有项目",
        "schema": {"type": "object", "properties": {}, "required": []}
    },
    "run_drc": {
        "desc": "DRC 设计规则检查 (PCB)",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "run_erc": {
        "desc": "ERC 电气规则检查 (原理图)",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "fill_zones": {
        "desc": "填充所有 Zone (铜皮/覆铜)",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "auto_route": {
        "desc": "FreeRouting 自动布线 (默认异步，会备份原文件)",
        "schema": {"type": "object", "properties": {
            "project": {"type": "string"},
            "max_passes": {"type": "integer", "default": 100, "description": "最大布线尝试次数"},
            "async_mode": {"type": "boolean", "default": True, "description": "异步模式（推荐）"}
        }, "required": ["project"]}
    },
    "get_task_status": {
        "desc": "查询异步任务状态",
        "schema": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}
    },
    "list_tasks": {
        "desc": "列出所有异步任务",
        "schema": {"type": "object", "properties": {}, "required": []}
    },
    "get_board_info": {
        "desc": "获取板子信息 (尺寸/层数/元件数)",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "export_gerber": {
        "desc": "导出 Gerber + 钻孔文件",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "export_bom": {
        "desc": "导出 BOM (CSV)",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "export_netlist": {
        "desc": "导出网表 (kicadxml/spice)",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}, "format": {"type": "string", "enum": ["kicadxml", "spice", "cadstar", "orcadpcb2"], "default": "kicadxml"}}, "required": ["project"]}
    },
    "export_3d": {
        "desc": "3D 渲染图 (top/bottom/iso/all)",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}, "view": {"type": "string", "enum": ["top", "bottom", "front", "back", "iso", "iso_back", "all"], "default": "top"}}, "required": ["project"]}
    },
    "export_svg": {
        "desc": "导出 PCB SVG 图片",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}, "view": {"type": "string", "enum": ["top", "bottom", "all"], "default": "all"}}, "required": ["project"]}
    },
    "export_pdf": {
        "desc": "导出 PCB PDF",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}, "layers": {"type": "string", "default": "all"}}, "required": ["project"]}
    },
    "export_sch_pdf": {
        "desc": "导出原理图 PDF",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "export_sch_svg": {
        "desc": "导出原理图 SVG",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "export_step": {
        "desc": "导出 STEP 3D 模型文件",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "export_jlcpcb": {
        "desc": "JLCPCB/嘉立创 完整制造包",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "export_all": {
        "desc": "导出所有文件",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "get_output_files": {
        "desc": "列出项目输出文件",
        "schema": {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
    },
    "read_file": {
        "desc": "读取文件内容",
        "schema": {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}
    },
    "get_version": {
        "desc": "查看版本信息",
        "schema": {"type": "object", "properties": {}, "required": []}
    }
}

def handle(req):
    m = req.get("method", "")
    p = req.get("params", {})
    rid = req.get("id")
    
    if m == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "kicad-mcp", "version": "3.4"}
        }}
    
    if m == "notifications/initialized":
        return None
    
    if m == "tools/list":
        tools = [{"name": n, "description": t["desc"], "inputSchema": t["schema"]} for n, t in TOOLS.items()]
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": tools}}
    
    if m == "tools/call":
        n = p.get("name", "")
        a = p.get("arguments", {})
        log(f"调用: {n}, 参数: {a}")
        
        try:
            if n == "list_projects":
                r = tool_list_projects()
            elif n == "run_drc":
                r = tool_run_drc(a["project"])
            elif n == "run_erc":
                r = tool_run_erc(a["project"])
            elif n == "fill_zones":
                r = tool_fill_zones(a["project"])
            elif n == "auto_route":
                r = tool_auto_route(a["project"], a.get("max_passes", 100), a.get("async_mode", True))
            elif n == "get_task_status":
                r = tool_get_task_status(a["task_id"])
            elif n == "list_tasks":
                r = tool_list_tasks()
            elif n == "get_board_info":
                r = tool_get_board_info(a["project"])
            elif n == "export_gerber":
                r = tool_export_gerber(a["project"])
            elif n == "export_bom":
                r = tool_export_bom(a["project"])
            elif n == "export_netlist":
                r = tool_export_netlist(a["project"], a.get("format", "kicadxml"))
            elif n == "export_3d":
                r = tool_export_3d(a["project"], a.get("view", "top"))
            elif n == "export_svg":
                r = tool_export_svg(a["project"], a.get("view", "all"))
            elif n == "export_pdf":
                r = tool_export_pdf(a["project"], a.get("layers", "all"))
            elif n == "export_sch_pdf":
                r = tool_export_sch_pdf(a["project"])
            elif n == "export_sch_svg":
                r = tool_export_sch_svg(a["project"])
            elif n == "export_step":
                r = tool_export_step(a["project"])
            elif n == "export_jlcpcb":
                r = tool_export_jlcpcb(a["project"])
            elif n == "export_all":
                r = tool_export_all(a["project"])
            elif n == "get_output_files":
                r = tool_get_files(a["project"])
            elif n == "read_file":
                r = tool_read_file(a["filepath"])
            elif n == "get_version":
                r = tool_version()
            else:
                r = {"error": f"未知工具: {n}"}
            
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": json.dumps(r, ensure_ascii=False, indent=2)}]
            }}
        except Exception as e:
            log(f"错误: {e}")
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": str(e)}}
    
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Unknown: {m}"}}

def main():
    log("KiCad MCP Server v3.4 启动 (KiCad 9.x)")
    log(f"pcbnew API: {'可用' if HAS_PCBNEW else '不可用'}")
    log(f"FreeRouting: {'可用' if os.path.exists(FREEROUTING_JAR) else '不可用'}")
    log(f"异步任务目录: {TASKS_DIR}")
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            r = handle(json.loads(line))
            if r:
                print(json.dumps(r), flush=True)
        except Exception as e:
            log(f"处理错误: {e}")

if __name__ == "__main__":
    main()
