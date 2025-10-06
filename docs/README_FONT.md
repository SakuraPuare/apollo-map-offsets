# 字体设置说明

## 中文字体问题

在 Docker 环境中，matplotlib 可能无法正确显示中文，导致可视化图表中的中文显示为方块。

## 解决方案

### 方案 1: 使用本地 simhei.ttf（推荐）

1. 将 `simhei.ttf` 文件放到当前目录：
   ```bash
   cp /path/to/simhei.ttf /apollo_workspace/utils/apollo-map-offsets/
   ```

2. pipeline 会自动检测并使用这个字体文件

### 方案 2: 安装系统字体

如果没有 simhei.ttf，可以安装系统字体：

```bash
sudo apt-get update
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei
fc-cache -fv
rm -rf ~/.cache/matplotlib
```

## 测试字体

运行以下命令测试字体是否正常工作：

```bash
python3 test_font.py
```

如果生成的 `/tmp/test_chinese.png` 中文字正常显示，说明字体配置成功。

## 字体文件获取

### Windows 用户
从 `C:\Windows\Fonts\` 目录复制 `simhei.ttf`（黑体）

### macOS 用户
从 `/Library/Fonts/` 或 `/System/Library/Fonts/` 复制中文字体

### Linux 用户
```bash
# 安装字体包
sudo apt-get install fonts-wqy-zenhei
# 字体位置: /usr/share/fonts/truetype/wqy/
```

## 常见问题

**Q: 为什么要用 simhei.ttf 而不是系统字体？**

A: simhei.ttf 是单文件字体，方便移植。系统字体（如 Noto Sans CJK）通常是 TTC 格式，matplotlib 加载时可能遇到问题。

**Q: 可以用其他中文字体吗？**

A: 可以！只要是 TTF 格式的中文字体都可以，将文件重命名为 `simhei.ttf` 放到当前目录即可。

**Q: 运行 pipeline 时字体相关的警告可以忽略吗？**

A: 可以。警告不影响功能，只是说明 matplotlib 在使用后备字体。图表会正常生成，只是中文可能显示为方块。
