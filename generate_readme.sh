#!/bin/bash

# 清空README.md
echo "" > README.md

# 添加标题
echo "# GitHub博客主页" >> README.md
echo "" >> README.md

# 遍历根目录下的所有.md文件
for file in *.md; do
  # 跳过README.md本身
  if [ "$file" != "README.md" ]; then
    # 获取文件名（不包含扩展名）
    filename=$(basename -- "$file")
    filename_without_ext="${filename%.*}"
    # 添加文件名和链接
    echo "- [${filename_without_ext}](./${file})" >> README.md
  fi
done
