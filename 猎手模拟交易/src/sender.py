#!/usr/bin/env python3
"""
持仓汇报发送器 - cron 调用
读取报告文件，通过 OpenClaw MCP API 发送微信消息
"""
import sys, os, json

PORTFOLIO_REPORT = '/root/.openclaw/workspace/猎手模拟交易/持仓报告.md'
PENDING_DIR = '/root/.openclaw/workspace/pending-summaries'
SENDER_ID = 'o9cq801u9_6B8BEUnp-foIPm8pP0@im.wechat'
API_BASE = 'http://localhost:18789'  # OpenClaw gateway API

def send_to_wechat(content):
    """通过 OpenClaw gateway API 发送微信消息"""
    try:
        import urllib.request, urllib.parse
        
        payload = json.dumps({
            'channel': 'openclaw-weixin',
            'to': SENDER_ID,
            'message': content
        }).encode()
        
        req = urllib.request.Request(
            f'{API_BASE}/api/messages/send',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {'error': str(e)}

def main():
    slot = sys.argv[1] if len(sys.argv) > 1 else 'report'
    today = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
    
    # 查找对应的报告文件
    possible_files = [
        f'{PENDING_DIR}/portfolio-{today}-{slot}.md',
        f'{PENDING_DIR}/portfolio-{today}-*.md',
    ]
    
    report_content = None
    report_file = None
    
    import glob
    for pattern in possible_files:
        files = glob.glob(pattern)
        if files:
            report_file = files[0]
            with open(report_file, 'r') as f:
                report_content = f.read()
            break
    
    # 如果没找到slot对应的，读取主报告
    if not report_content and os.path.exists(PORTFOLIO_REPORT):
        with open(PORTFOLIO_REPORT, 'r') as f:
            report_content = f.read()
        report_file = PORTFOLIO_REPORT
    
    if not report_content:
        print('No report found to send')
        return
    
    # 提取摘要发送（微信消息不宜太长）
    # 取前40行作为摘要
    lines = report_content.split('\n')
    summary_lines = []
    char_count = 0
    for line in lines:
        if line.startswith('#') and not summary_lines:
            # 标题行
            summary_lines.append(line)
        elif char_count < 800:
            summary_lines.append(line)
            char_count += len(line)
    
    summary = '\n'.join(summary_lines)
    
    # 发送
    result = send_to_wechat(summary)
    print(f"Send result: {result}")
    
    # 删除已发送的文件
    if report_file and report_file.startswith(PENDING_DIR):
        os.remove(report_file)
        print(f"Deleted: {report_file}")
    else:
        # 只删除pending目录下的，不删主报告
        for f in glob.glob(f'{PENDING_DIR}/portfolio-{today}-*.md'):
            os.remove(f)
            print(f"Deleted: {f}")

if __name__ == '__main__':
    main()
