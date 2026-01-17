#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== Step 1: 初始化 Git 并推送到 GitHub ==="
if [ ! -d ".git" ]; then
    git init
    git remote add origin git@github.com:bunnyf/pcb-mcp.git
    git fetch origin main
    git reset --soft origin/main
fi
git add README.md README_CN.md server.json
git commit -m "Add MCP Registry support

- Add mcp-name identifier to README.md and README_CN.md for PyPI validation
- Add server.json for MCP Registry publishing

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>" || true
git push origin HEAD:main

echo "=== Step 2: 发布到 PyPI ==="
pip3 install twine -q
echo "请输入 PyPI Token:"
read -s PYPI_TOKEN
python3 -m twine upload dist/* -u __token__ -p "$PYPI_TOKEN"

echo "=== 等待 PyPI 索引 (30s) ==="
sleep 30

echo "=== Step 3: 安装 mcp-publisher ==="
if ! command -v mcp-publisher &>/dev/null; then
    curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_darwin_arm64.tar.gz" | tar xz
    sudo mv mcp-publisher /usr/local/bin/
fi

echo "=== Step 4: 登录并发布到 MCP Registry ==="
mcp-publisher login github
mcp-publisher publish

echo "=== 完成! ==="
echo "PyPI: https://pypi.org/project/kicad-mcp-server/"
echo "⚠️  请立即删除 PyPI Token: https://pypi.org/manage/account/"
