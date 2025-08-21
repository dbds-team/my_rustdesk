#!/usr/bin/env python3
"""
GitHub Actions 状态检查脚本
用于监控 workflow 运行状态并获取错误日志
"""

import json
import sys
import time
import argparse
from datetime import datetime
import subprocess

def run_command(cmd):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Error running command: {e}")
        return "", 1

def get_workflow_runs(repo="dbds-team/my_rustdesk", limit=5):
    """获取最近的 workflow 运行记录"""
    cmd = f"gh run list --repo {repo} --limit {limit} --json databaseId,name,status,conclusion,createdAt,headBranch,event"
    output, code = run_command(cmd)
    
    if code != 0:
        print(f"错误: 无法获取 workflow 运行记录")
        print("请确保已安装 GitHub CLI (gh) 并已登录")
        return []
    
    try:
        return json.loads(output) if output else []
    except json.JSONDecodeError:
        print(f"错误: 无法解析 JSON 输出")
        return []

def get_workflow_jobs(repo, run_id):
    """获取特定 workflow 运行的所有 jobs"""
    cmd = f"gh run view {run_id} --repo {repo} --json jobs"
    output, code = run_command(cmd)
    
    if code != 0:
        return []
    
    try:
        data = json.loads(output) if output else {}
        return data.get('jobs', [])
    except json.JSONDecodeError:
        return []

def get_job_logs(repo, job_id):
    """获取失败 job 的日志"""
    cmd = f"gh run view --repo {repo} --job {job_id} --log-failed"
    output, code = run_command(cmd)
    return output

def format_time(timestamp):
    """格式化时间戳"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp

def check_latest_runs(repo="dbds-team/my_rustdesk", watch=False, interval=30):
    """检查最新的 workflow 运行状态"""
    
    while True:
        print("\n" + "="*80)
        print(f"GitHub Actions 状态检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        runs = get_workflow_runs(repo)
        
        if not runs:
            print("没有找到 workflow 运行记录")
            if not watch:
                break
            time.sleep(interval)
            continue
        
        # 显示运行摘要
        print(f"\n最近 {len(runs)} 个 workflow 运行:")
        print("-"*80)
        
        for i, run in enumerate(runs, 1):
            status_icon = {
                'completed': '✅' if run['conclusion'] == 'success' else '❌',
                'in_progress': '🔄',
                'queued': '⏳'
            }.get(run['status'], '❓')
            
            print(f"{i}. {status_icon} {run['name']}")
            print(f"   状态: {run['status']} - {run.get('conclusion', 'N/A')}")
            print(f"   分支: {run['headBranch']} | 事件: {run['event']}")
            print(f"   时间: {format_time(run['createdAt'])}")
            print(f"   ID: {run['databaseId']}")
            
            # 如果失败，获取失败的 jobs
            if run['status'] == 'completed' and run['conclusion'] == 'failure':
                jobs = get_workflow_jobs(repo, run['databaseId'])
                failed_jobs = [j for j in jobs if j.get('conclusion') == 'failure']
                
                if failed_jobs:
                    print(f"   ⚠️  失败的 Jobs:")
                    for job in failed_jobs[:3]:  # 只显示前3个失败的job
                        print(f"      - {job['name']}")
                        
                        # 获取最近的失败job的错误日志
                        if i == 1:  # 只显示最新运行的错误
                            print("\n   📋 错误日志摘要:")
                            logs = get_job_logs(repo, job['databaseId'])
                            if logs:
                                # 只显示最后几行错误
                                log_lines = logs.split('\n')
                                error_lines = [l for l in log_lines if 'error' in l.lower() or 'Error' in l][-5:]
                                for line in error_lines:
                                    print(f"      {line[:120]}...")
            print()
        
        # 统计信息
        in_progress = sum(1 for r in runs if r['status'] == 'in_progress')
        successful = sum(1 for r in runs if r['conclusion'] == 'success')
        failed = sum(1 for r in runs if r['conclusion'] == 'failure')
        
        print("-"*80)
        print(f"统计: 🔄 运行中: {in_progress} | ✅ 成功: {successful} | ❌ 失败: {failed}")
        
        if not watch:
            break
            
        print(f"\n下次检查时间: {interval} 秒后... (按 Ctrl+C 退出)")
        time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description='检查 GitHub Actions 运行状态')
    parser.add_argument('--repo', default='dbds-team/my_rustdesk', help='GitHub 仓库 (owner/repo)')
    parser.add_argument('--watch', action='store_true', help='持续监控模式')
    parser.add_argument('--interval', type=int, default=30, help='监控间隔（秒）')
    parser.add_argument('--run-id', help='查看特定运行的详细信息')
    
    args = parser.parse_args()
    
    # 检查 gh 命令是否可用
    _, code = run_command("gh --version")
    if code != 0:
        print("错误: GitHub CLI (gh) 未安装或未配置")
        print("请访问 https://cli.github.com/ 安装并运行 'gh auth login' 登录")
        sys.exit(1)
    
    if args.run_id:
        # 查看特定运行的详细信息
        cmd = f"gh run view {args.run_id} --repo {args.repo}"
        output, _ = run_command(cmd)
        print(output)
    else:
        # 检查最新运行状态
        try:
            check_latest_runs(args.repo, args.watch, args.interval)
        except KeyboardInterrupt:
            print("\n\n监控已停止")

if __name__ == "__main__":
    main()