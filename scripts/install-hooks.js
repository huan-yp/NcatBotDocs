import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Git hooks 安装脚本
function installGitHooks() {
  const hooksDir = path.join(__dirname, '../.git/hooks');
  const preCommitPath = path.join(hooksDir, 'pre-commit');
  
  console.log('🔧 安装 Git hooks...');
  
  // 检查 .git/hooks 目录是否存在
  if (!fs.existsSync(hooksDir)) {
    console.error('❌ 错误: .git/hooks 目录不存在');
    console.error('请确保在 Git 仓库中运行此脚本');
    process.exit(1);
  }
  
  // Pre-commit 钩子内容
  const preCommitContent = `#!/bin/sh

# NcatBotDocs Pre-commit Hook
# 在提交前自动生成 AI 可读文档

echo "运行 pre-commit 钩子: 生成 AI 可读文档..."

# 检查是否在正确的目录
if [ ! -f "scripts/concat-md.js" ]; then
    echo "错误: 未找到 scripts/concat-md.js 文件"
    exit 1
fi

# 运行文档生成脚本
echo "正在生成文档..."
if node scripts/concat-md.js; then
    echo "✅ 文档生成完成"
    
    # 检查是否生成了新的 LLM.md 文件
    if [ -f "LLM.md" ]; then
        echo "📝 将 LLM.md 添加到提交中..."
        git add LLM.md
        echo "✅ LLM.md 已添加到提交中"
    fi
    
    echo "🚀 Pre-commit 钩子执行完成"
    exit 0
else
    echo "❌ 错误: 文档生成失败"
    echo "请检查 scripts/concat-md.js 是否正常工作"
    exit 1
fi`;

  try {
    // 创建 pre-commit 钩子
    fs.writeFileSync(preCommitPath, preCommitContent);
    
    // 在 Windows 上，我们还需要确保文件可执行
    // Git for Windows 会自动处理这个问题
    
    console.log('✅ Pre-commit 钩子安装成功');
    console.log(`📍 钩子位置: ${preCommitPath}`);
    
    // 测试钩子是否可以运行
    console.log('🧪 测试钩子...');
    if (fs.existsSync(path.join(__dirname, '../scripts/concat-md.js'))) {
      console.log('✅ 钩子测试通过');
      console.log('');
      console.log('🎉 安装完成！');
      console.log('');
      console.log('💡 使用说明:');
      console.log('  - 每次 git commit 时会自动生成 LLM.md');
      console.log('  - 手动生成: npm run generate:docs');
      console.log('  - 手动生成(详细): npm run generate:docs-manual');
      console.log('  - 如需禁用钩子: git commit --no-verify');
    } else {
      console.warn('⚠️  警告: 未找到 scripts/concat-md.js 文件');
      console.warn('钩子已安装但可能无法正常工作');
    }
    
  } catch (error) {
    console.error('❌ 安装失败:', error.message);
    process.exit(1);
  }
}

// 运行安装
installGitHooks();