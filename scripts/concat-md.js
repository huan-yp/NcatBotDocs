import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const outputFilePath = path.join(__dirname, '../LLM.md');

// 递归查找指定目录下的所有 .md 文件
function findMarkdownFiles(dir) {
  const mdFiles = [];
  
  try {
    const files = fs.readdirSync(dir);
    
    for (const file of files) {
      const fullPath = path.join(dir, file);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        // 递归查找子目录
        mdFiles.push(...findMarkdownFiles(fullPath));
      } else if (stat.isFile() && path.extname(file).toLowerCase() === '.md') {
        // 找到 .md 文件
        mdFiles.push(fullPath);
      }
    }
  } catch (error) {
    console.warn(`无法读取目录 ${dir}: ${error.message}`);
  }
  
  return mdFiles;
}

// 对文件路径进行排序，确保按照文件夹和文件名的字母数字顺序排列
function sortFiles(files) {
  return files.sort((a, b) => {
    // 标准化路径分隔符
    const pathA = a.replace(/\\/g, '/').toLowerCase();
    const pathB = b.replace(/\\/g, '/').toLowerCase();
    
    // 按路径排序
    return pathA.localeCompare(pathB, 'zh-CN', { numeric: true });
  });
}

// docs/notes/guide 目录的路径
const guideDir = path.join(__dirname, '../docs/notes/guide');

// 自动发现所有 .md 文件
const mdFiles = sortFiles(findMarkdownFiles(guideDir));

// 拼接所有 .md 文件内容
function concatMarkdownFiles(mdFiles, outputPath) {
  if (mdFiles.length === 0) {
    console.warn('未找到任何 .md 文件');
    return;
  }
  
  console.log(`找到 ${mdFiles.length} 个 .md 文件:`);
  mdFiles.forEach((file, index) => {
    const relativePath = path.relative(path.join(__dirname, '../docs/notes/guide'), file);
    console.log(`${index + 1}. ${relativePath}`);
  });
  
  const content = "本文档供 AI 阅读. NcatBot 文档 base_url 为 `https://docs.ncatbot.xyz/`, 文档中包含相对链接，为用户生成链接时必须加上这个前缀生成绝对链接。\n\n" + 
    mdFiles.map((file) => {
      try {
        const fileContent = fs.readFileSync(file, 'utf-8');
        const relativePath = path.relative(path.join(__dirname, '../docs/notes/guide'), file);
        return `# 文件: ${relativePath}\n\n${fileContent}`;
      } catch (error) {
        console.warn(`无法读取文件 ${file}: ${error.message}`);
        return `# 文件: ${file}\n\n[无法读取文件内容: ${error.message}]`;
      }
    }).join('\n\n---\n\n');
  
  fs.writeFileSync(outputPath, content);
}

// 主程序
if (fs.existsSync(guideDir)) {
  concatMarkdownFiles(mdFiles, outputFilePath);
  console.log(`\n所有 .md 文件已拼接到 ${outputFilePath}`);
} else {
  console.error(`目录不存在: ${guideDir}`);
  process.exit(1);
}