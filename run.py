#!/usr/bin/env python3
"""Startup script for the Integrated Educational Management System.

Launches all four servers:
  - Integration Server (port 5000)
  - College A (SQL Server simulation, port 5001)
  - College B (Oracle simulation, port 5002)
  - College C (MySQL simulation, port 5003)
"""

import os
import sys
import time
import threading
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def run_college(config_path, port):
    """Run a college Flask app."""
    from college.app import create_college_app
    app = create_college_app(config_path)
    print(f'[{config_path.split("_")[-1].replace(".json","").upper()}] '
          f'启动于 http://127.0.0.1:{port}')
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


def run_integration():
    """Run the integration server."""
    from integration.app import app
    print(f'[集成服务器] 启动于 http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


def main():
    """Start all four servers in separate threads."""
    print('=' * 60)
    print('  集成教务管理系统 — 启动中...')
    print('  基于XML数据集成技术')
    print('=' * 60)
    print()

    # Check if data needs to be generated
    db_path_a = os.path.join(BASE_DIR, 'data', 'college_a.db')
    if not os.path.exists(db_path_a):
        print('[系统] 首次运行，正在生成测试数据...')
        from college.data_generator import generate_college_data
        generate_college_data()
        print()

    # Start college servers in threads
    configs = [
        (os.path.join(BASE_DIR, 'college', 'configs', 'college_a.json'), 5001),
        (os.path.join(BASE_DIR, 'college', 'configs', 'college_b.json'), 5002),
        (os.path.join(BASE_DIR, 'college', 'configs', 'college_c.json'), 5003),
    ]

    threads = []
    for config_path, port in configs:
        t = threading.Thread(target=run_college, args=(config_path, port), daemon=True)
        t.start()
        threads.append(t)

    # Run integration server in main thread
    run_integration()


if __name__ == '__main__':
    main()
