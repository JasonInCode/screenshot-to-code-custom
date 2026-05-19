"""一键启动脚本：先 kill 占用端口的进程，再在新 Terminal 中启动前后端

用法：
  python start.py            # 默认前端 5173，后端 7001
  python start.py --frontend-port 3000 --backend-port 8000
"""

import argparse
import subprocess
import os
import sys

FRONTEND_PORT = 5173
BACKEND_PORT = 7001
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def kill_port(port: int) -> None:
    """🛑 Kill 占用指定端口的所有进程"""
    # 使用 PowerShell 查找占用端口的 PID（兼容 IPv4/IPv6 格式）
    result = subprocess.run(
        [
            "powershell", "-Command",
            f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue "
            f"| Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique",
        ],
        capture_output=True, text=True,
    )
    pids = set()
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line.isdigit() and line != "0":
            pids.add(int(line))

    if not pids:
        print(f"✅ 端口 {port} 无占用进程")
        return

    for pid in pids:
        print(f"🛑 Kill PID {pid} (占用端口 {port})")
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
        )

    print(f"✅ 端口 {port} 已释放")


def open_terminals(tabs: list[tuple[str, str, str]]) -> None:
    """🚀 在同一 Windows Terminal 窗口中以多 tab 方式启动命令"""
    # tabs: [(title, command, cwd), ...]
    wt_available = subprocess.run(
        "where wt", shell=True, capture_output=True,
    ).returncode == 0

    if wt_available:
        # wt 单条命令：第一个 new-tab 创建窗口，后续 new-tab 添加 tab
        cmd = ["wt", "-w", "new"]
        for i, (title, command, cwd) in enumerate(tabs):
            if i > 0:
                cmd.append(";")
            cmd.extend([
                "new-tab",
                "--title", title,
                "-d", cwd,
                "powershell", "-NoExit", "-Command", command,
            ])
        subprocess.Popen(cmd)
    else:
        # fallback: 使用 cmd start 命令（每个 tab 单独一个窗口）
        for title, command, cwd in tabs:
            subprocess.Popen([
                "cmd", "/c", "start",
                f"\"{title}\"",
                "powershell", "-NoExit", "-Command",
                f"cd \"{cwd}\"; {command}",
            ])


def main():
    parser = argparse.ArgumentParser(description="一键启动前后端")
    parser.add_argument("--frontend-port", type=int, default=FRONTEND_PORT)
    parser.add_argument("--backend-port", type=int, default=BACKEND_PORT)
    args = parser.parse_args()

    fp = args.frontend_port
    bp = args.backend_port

    print("=" * 50)
    print("🚀 Screenshot to Code - 一键启动")
    print("=" * 50)

    # 🛑 Kill 占用端口的进程
    print(f"\n🛑 清理端口 {fp} 和 {bp}...")
    kill_port(fp)
    kill_port(bp)

    # 🚀 启动前后端（同一窗口两个 tab）
    backend_dir = os.path.join(PROJECT_DIR, "backend")
    frontend_dir = os.path.join(PROJECT_DIR, "frontend")
    print(f"\n🚀 启动后端 (端口 {bp}) + 前端 (端口 {fp})...")
    open_terminals([
        (f"Backend (:{bp})", f"python start.py --port {bp}", backend_dir),
        (f"Frontend (:{fp})", f"pnpm run dev -- --port {fp}", frontend_dir),
    ])

    print(f"\n✅ 启动完成！")
    print(f"   🌐 前端: http://localhost:{fp}")
    print(f"   🔧 后端: http://localhost:{bp}")
    print("=" * 50)


if __name__ == "__main__":
    main()