# 暗链检测工具

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一款智能化的网站暗链检测工具，支持多策略反爬虫绕过和自动关键词检测。

## 功能特性

- 🕵️‍♂️ 深度爬取网站所有链接（可配置深度）
- 🔍 智能检测赌博/色情/盗版等违规内容
- 🛡️ 多重反爬虫绕过策略：
  - 动态User-Agent轮换
  - 请求频率随机化
  - 自动Selenium回退
  - 代理IP支持
- 📊 生成详细检测报告
- 📢 企业微信实时告警
- ⚡ 多线程加速检测

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基础使用

```bash
python dark_link_detector.py https://example.com --depth 3 --workers 5
```

### 参数说明

| 参数          | 默认值 | 说明                                  |
| :------------ | :----- | :------------------------------------ |
| URL           | 必填   | 要检测的起始URL                       |
| --depth       | 5      | 爬取深度（1-10）                      |
| --workers     | 5      | 并发线程数（1-20）                    |
| --proxy       | 无     | 代理服务器（如：http://1.2.3.4:8080） |
| --no-selenium | False  | 禁用Selenium回退功能                  |

## 高级配置

编辑脚本开头的配置区域：

```python
# 企业微信机器人配置
WECHAT_WEBHOOK = "YOUR_WEBHOOK_URL"

# 白名单域名（自动跳过检测）
WHITELIST_DOMAINS = {'gov.cn', 'edu.cn'}

# 黑名单关键词（支持正则表达式）
BLACKLIST = {
    '赌博': ['赌场', '百家乐'],
    '色情': ['成人视频', '裸聊']
}

# 跳过检测的文件类型
SKIP_EXTENSIONS = {'pdf', 'jpg', 'mp4'}
```

## 检测报告示例

```text
检测时间: 2023-08-20 14:25:30
来源页面: https://example.com/page1
黑链URL: https://malicious.com/gambling
类型: 赌博
关键词: 赌场, 百家乐
==========================================
```

## 反爬策略说明

1. **基础防御绕过**：
   - 随机User-Agent
   - 动态请求延迟（0.5-2.5秒）
   - 自动重试机制（最多3次）
2. **高级防御绕过**：
   - TLS指纹伪装
   - 浏览器指纹模拟
   - 动态Cookie生成
3. **终极方案**：
   - 无头浏览器渲染（Chrome）
   - 鼠标移动模拟
   - 页面滚动行为模拟

## 常见问题

### Q: 遇到SSL证书错误怎么办？

A: 尝试添加 `--no-verify` 参数：

```bash
python dark_link_detector.py https://example.com --no-verify
```

### Q: 如何提高检测速度？

1. 增加 `--workers` 数量
2. 在配置中缩小 `BLACKLIST` 范围
3. 添加更多域名到 `WHITELIST_DOMAINS`

### Q: 企业微信通知不工作？

检查：

1. Webhook地址是否正确
2. 网络是否能访问企业微信服务器
3. 消息内容是否超过限制长度

```
dark-link-detector/
├── dark_link_detector.py # 主程序
├── README.md # 本文档
├── requirements.txt # 依赖文件
└── samples/ # 示例报告
└── report_20230820.txt
```

