# -*- coding: utf-8 -*-
import argparse
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import tldextract
from collections import deque
import re
import time
import random
from datetime import datetime
import json
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
import os
import html
from selenium.webdriver.chrome.service import Service

urllib3.disable_warnings()

# ==================== 配置区域 ====================
# 企业微信机器人配置（需替换为实际Webhook地址）
WECHAT_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx"

# 白名单域名
WHITELIST_DOMAINS = {
    'gov.cn', 'org.cn', 'mil.cn', 'ac.cn', 'bj.cn', 'sh.cn', 'qq.com', '163.com', 'bilibili.com', 'weixin.qq.com',
    'ifeng.com', 'sohu.com', 'b23.tv', 'sougou.com', 'vers.cqvip.com', 'xinhuanet.com', 'baidu.com'
}

# 黑名单关键词（分类更全面）
BLACKLIST = {
    '赌博': ['赌场', '百家乐', '轮盘', '下注', '赌博', '体育投注', '真人娱乐',
           '老虎机', '博彩', '赌球', '澳门赌场', '线上赌场', '赌钱', '押注', '六合彩', '新澳免费资料', '六合皇', '单双中特', '澳门彩正版', '精准一码', '澳门玄机',
           '精准单双', '精准四不像', '三肖三码', '平特心水', '澳门四不像', '跑狗图', '二四六免费资料', '天天彩免费资料', '挑码助手', '49澳门', '刘伯温精选四肖', '另版跑狗图',
           '管家婆资料大全', '特马资料', '一肖一码', '七尾中特', '六肖十八码', '四不像中特', '天天好彩', '澳门精准资料', '澳门论坛资料', '玄机图', '肖中特', '马会传真',
           '精准管家婆', '一波中特', '三码期期准', '六合彩开奖', '平特一肖', '澳门六开彩', '澳门精准单双', '特码诗', '绝杀二肖', '正版挂牌', '白小姐三肖', '中欧体育',
           '凯时KB88', '凯时k66', '利来国际', '千赢国际', '龙八国际', 'k8凯发', 'w66利来', '凯发国际', '尊龙凯时', 'Bwin必赢', '凯时国际', '利来w66',
           'B体育平台', 'B体育登录', 'FB体育', 'KB体育', 'bb贝博', 'bet体育', 'b体育app', 'b体育官方', 'b体育官网', 'yb体育', '爱游戏app', '爱游戏ayx',
           '贝博app', '贝博体育', 'OB体育', '乐鱼体育', 'TG纸飞机'],
    '色情': ['色情', '情色', '性爱', '裸聊', '成人视频', '成人小说',
           '约炮', '一夜情', '偷拍', '自拍', '夫妻交友', '国产黄色', '换妻', '小姐', '上门服务', '午夜无码', '大杳蕉', '无码久久', '色综合久久', 'Av麻豆', '国产麻豆', '在线av',
           '无码一区', '免费无码', '颜射', '黑丝诱惑', '第4色', '精品久久', '大尺度私拍', '无毛白虎', '直播做爱', '肉便器', '蚊香社', '亚洲无码', '人妻熟女'],
    '盗版': ['盗版', '破解版', '盗版资源', '枪版','生活影院','高清电影','在线手机免费播放',
           '电影下载', '免VIP', '蓝光破解', 'BT下载', '磁力链接', '网盘资源', '星空影院', '青苹果影院', '青苹果乐园影院', '秋葵视频', '芭乐视频', '青鸟影院', '四虎影院', '星辰影视',
           '星辰影院', '秋霞电影网', '草民影院', '光棍影院', '丝瓜直播app', '大色窝', '成人短视频app', '茄子视频app', '豆奶短视频', '香蕉91', '奇米影视', '策驰影院',
           '麻花影视']
}

# 需要跳过的文件扩展名（小写）
SKIP_EXTENSIONS = {
    # 静态资源
    'css', 'js', 'json', 'xml', 'csv',
    # 图片
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'ico', 'webp',
    # 文档
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
    # 压缩包
    'zip', 'rar', '7z', 'tar', 'gz',
    # 音视频
    'mp3', 'wav', 'mp4', 'avi', 'mov', 'flv'
}

USER_AGENTS = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    
    # Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
    
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
]

# 创建output目录
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(output_dir, exist_ok=True)

# 预编译正则表达式
BLACKLIST_REGEX = {
    category: re.compile('|'.join([rf'\b{re.escape(kw.lower())}\b' for kw in keywords]), re.IGNORECASE)
    for category, keywords in BLACKLIST.items()
}

# 死链状态码列表
DEAD_LINK_STATUS_CODES = {400, 403, 404, 500, 502, 503, 504}
# 死链重试次数
DEAD_LINK_RETRIES = 2


# ==================== 工具函数 ====================
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def print_with_time(message):
    print(f"[{get_current_time()}] {message}")


def is_whitelist(url):
    extracted = tldextract.extract(url)
    domain_suffix = f"{extracted.domain}.{extracted.suffix}"
    # 检查完整域名是否在白名单中（包括子域名）
    full_domain = f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}".lstrip('.')
    return any(full_domain.endswith(f'.{d}') or full_domain == d for d in WHITELIST_DOMAINS)


def check_black_keywords(text):
    text = html.unescape(text)  # 解码 &#xxxx; 格式的内容
    found = {}
    text_lower = text.lower()
    for category, pattern in BLACKLIST_REGEX.items():
        matches = pattern.findall(text_lower)
        if matches:
            found[category] = list(set(matches))[:5]
    return found


def get_output_filename(url):
    """根据URL生成输出文件名"""
    extracted = tldextract.extract(url)
    domain = f"{extracted.domain}_{extracted.suffix}".replace('.', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 修改为输出到output目录
    return os.path.join(output_dir, f"dark_links_{domain}_{timestamp}.txt")


# ==================== 通知功能 ====================
def send_wechat_alert(content, is_final_report=False):
    """发送企业微信机器人通知"""
    try:
        if is_final_report:
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"**扫描完成报告**\n>时间: {get_current_time()}\n"
                               f">扫描结果: {content}"
                }
            }
        else:
            source_url = content['source_url']
            dark_url = content['dark_url']
            keywords = content['keywords']
            keyword_str = "\n".join([f"{k}: {','.join(v)}" for k, v in keywords.items()])
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"**暗链警报**\n>时间: {get_current_time()}\n"
                               f">来源页面: [{source_url}]({source_url})\n"
                               f">黑链地址: [{dark_url}]({dark_url})\n"
                               f"**关键词检测**:\n{keyword_str}"
                }
            }
        requests.post(WECHAT_WEBHOOK, json=message, timeout=5)
    except Exception as e:
        print_with_time(f"企业微信通知失败: {str(e)}")


def write_to_file(filename, source_url, dark_url, keywords):
    """记录到文件并发送通知"""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"检测时间: {get_current_time()}\n")
        f.write(f"来源页面: {source_url}\n")
        f.write(f"黑链URL: {dark_url}\n")
        for cat, words in keywords.items():
            f.write(f"类型: {cat}\n关键词: {', '.join(words)}\n")
        f.write("\n" + "=" * 50 + "\n\n")
    send_wechat_alert({'source_url': source_url, 'dark_url': dark_url, 'keywords': keywords})


# ==================== 改进的fetch_url ====================
def fetch_url(url, headers=None, verify=False, retry_with_selenium=True):
    """增强版请求函数，支持死链检测"""
    dead_link_reason = None

    try:
        # 原有请求逻辑...
        response = requests.get(url, headers=headers, timeout=30, verify=verify)

        # 检查状态码
        if response.status_code in DEAD_LINK_STATUS_CODES:
            dead_link_reason = f"HTTP {response.status_code}"
            raise requests.exceptions.RequestException(dead_link_reason)

        return response

    except Exception as e:
        if retry_with_selenium:
            # 先记录原始错误
            dead_link_reason = str(e)

            # 尝试Selenium
            try:
                html = fetch_with_selenium(url)
                if html:
                    fake_response = requests.models.Response()
                    fake_response.status_code = 200
                    fake_response._content = html.encode('utf-8')
                    return fake_response
                dead_link_reason = "Selenium获取失败"
            except Exception as selenium_error:
                dead_link_reason = f"Selenium错误: {str(selenium_error)}"

        # 返回统一错误对象
        error_response = requests.models.Response()
        error_response.status_code = 999  # 自定义错误码
        error_response.dead_link_reason = dead_link_reason
        return error_response


# ==================== 改进的process_dark_link ====================
def process_dark_link(source_url, dark_url, headers, output_file):
    """改进的暗链处理函数"""
    try:
        # 先尝试常规请求
        response = fetch_url(dark_url, headers)

        if not response:
            print_with_time(f"全部获取方式失败: {dark_url}")
            return 0

        if response.status_code == 200:
            found = check_black_keywords(response.text)
            if found:
                write_to_file(output_file, source_url, dark_url, found)
                return 1
    except Exception as e:
        print_with_time(f"暗链检测异常: {dark_url} - {str(e)}")
    return 0

def extract_urls_from_text(text):
    """用正则提取文本中的 URL"""
    return re.findall(r'https?://[^\s<>"\']+', text)


# 改进后的正则生成函数
def build_regex(keywords):
    pattern = '|'.join([rf'{re.escape(kw)}' for kw in keywords])  # 移除 \b
    return re.compile(pattern, re.IGNORECASE)


# 生成新的正则规则
BLACKLIST_REGEX = {
    category: build_regex(keywords)
    for category, keywords in BLACKLIST.items()
}


def should_skip_url(url):
    """判断URL是否应该跳过检测"""
    parsed = urlparse(url)

    # 检查扩展名
    path = parsed.path.lower()
    if any(path.endswith(f'.{ext}') for ext in SKIP_EXTENSIONS):
        return True

    # 检查常见静态资源路径
    if '/static/' in path or '/assets/' in path or '/uploads/' in path:
        return True

    return False


# ==================== Selenium配置 ====================
def init_selenium_driver():
    """初始化Selenium WebDriver（完整修复版）"""
    # 确保导入所需库
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService  # 新版本
        from selenium.webdriver.common.service import Service as LegacyService  # 旧版本
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        import random
        # print(webdriver.__version__)
    except ImportError as e:
        raise ImportError(f"Required packages not found: {e}")

    # 检查全局 USER_AGENTS 是否存在
    if not globals().get('USER_AGENTS'):
        raise ValueError("USER_AGENTS list not defined in global scope")

    chrome_options = Options()
    
    # 基础反检测配置
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # 反自动化检测配置
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 随机选择User-Agent
    selected_ua = random.choice(USER_AGENTS)
    chrome_options.add_argument(f'user-agent={selected_ua}')
    
    try:

        # 自动管理ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 移除navigator.webdriver属性
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {"
            "get: () => undefined,"
            "enumerable: true"
            "})"
        )
        
        return driver
    except Exception as e:
        raise RuntimeError(f"Selenium初始化失败: {str(e)}")


def fetch_with_selenium(url, timeout=30):
    """使用Selenium获取页面（增加错误处理）"""
    try:
        driver = init_selenium_driver()
        driver.get(url)
        
        # 模拟人类操作
        time.sleep(random.uniform(1, 3))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2)")
        time.sleep(random.uniform(0.5, 1.5))
        
        return driver.page_source
    except Exception as e:
        # print_with_time(f"Selenium获取失败: {str(e)}")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()


def record_dead_link(filename, source_url, dead_url, reason, status_code=None):
    """记录死链到单独文件"""
    # 确保文件名也指向output目录
    if not filename.startswith(output_dir):
        filename = os.path.join(output_dir, os.path.basename(filename))

    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"检测时间: {get_current_time()}\n")
        f.write(f"来源页面: {source_url}\n")
        f.write(f"死链URL: {dead_url}\n")
        f.write(f"错误类型: {reason}\n")
        if status_code:
            f.write(f"状态码: {status_code}\n")
        f.write("\n" + "=" * 50 + "\n\n")

def process_link(source_url, target_url, headers, dark_file, dead_file):
    """处理链接（同时检测暗链和死链）"""
    try:
        response = fetch_url(target_url, headers)

        # === 死链检测 ===
        if response.status_code == 999:  # 我们的自定义错误码
            record_dead_link(
                dead_file,
                source_url,
                target_url,
                getattr(response, 'dead_link_reason', '未知错误'),
                getattr(response, 'status_code', None)
            )
            return (0, 1)  # (暗链计数, 死链计数)

        # === 暗链检测 ===
        if response.status_code == 200:
            found = check_black_keywords(response.text)
            if found:
                write_to_file(dark_file, source_url, target_url, found)
                print_with_time(f"页面: {source_url} 存在暗链 {target_url}")
                return (1, 0)  # 发现暗链

        return (0, 0)  # 正常链接
    except Exception as e:
        print_with_time(f"链接处理失败: {target_url} - {str(e)}")
        return (0, 0)

def main():
    # 参数解析
    parser = argparse.ArgumentParser(description='暗链检测工具')
    parser.add_argument('url', help='起始URL，例如：https://www.xxmu.edu.cn/')
    parser.add_argument('--depth', type=int, default=5, help='最大爬取深度（默认5）')
    parser.add_argument('--workers', type=int, default=5, help='并发工作线程数（默认5）')
    args = parser.parse_args()

    # 初始化配置
    start_url = args.url.strip().lower()
    if not start_url.startswith(('http://', 'https://')):
        print_with_time('错误：URL必须以http://或https://开头')
        return


    # 新增死链文件初始化（放在 output_file 初始化之后）
    dead_links_file = os.path.join(output_dir, f"dead_links_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    print_with_time(f"死链报告将保存至: {dead_links_file}")
    dead_link_count = 0  # 初始化死链计数器

    extracted = tldextract.extract(start_url)
    main_domain = f"{extracted.domain}.{extracted.suffix}"
    output_file = get_output_filename(start_url)
    print_with_time(f"开始扫描主域名: {main_domain}")
    print_with_time(f"结果将保存至: {output_file}")

    # 检测过的URL，避免重复检测
    processed_urls = set()

    # 爬取队列
    visited = set()
    queue = deque([(start_url, 0)])
    MAX_DEPTH = args.depth
    dark_link_count = 0  # 记录检测到的暗链数量

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'close'  # 避免连接池问题
    }

    # 使用线程池处理暗链检测
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = []

        # 开始扫描
        while queue or futures:
            # 处理已完成的任务
            for future in as_completed(futures[:]):
                try:
                    dark_inc, dead_inc = future.result() or (0, 0)
                    dark_link_count += dark_inc
                    dead_link_count += dead_inc
                except Exception as e:
                    print_with_time(f"任务处理异常: {str(e)}")
                futures.remove(future)

            if not queue:
                continue

            current_url, depth = queue.popleft()

            if depth > MAX_DEPTH:
                continue

            if current_url in visited:
                continue

            visited.add(current_url)
            print_with_time(f"扫描(深度{depth}): {current_url}")

            try:
                # 获取页面内容
                response = fetch_url(current_url, headers)
                if not response or 'text/html' not in response.headers.get('Content-Type', ''):
                    continue

                # 解析链接
                soup = BeautifulSoup(response.text, 'lxml')
                tags = ['a', 'area', 'link']
                elements = soup.find_all(tags, href=True)  # 同时查找a和area标签
                for element in elements:
                    href = element.get('href', '').strip()
                    if not href:
                        continue

                    # 特殊处理相对路径
                    if not href.startswith(('http://', 'https://')):
                        if not href.startswith('/'):
                            href = '/' + href
                    absolute_url = urljoin(current_url, href)

                    # 检查是否已经处理过这个URL
                    if absolute_url in processed_urls:
                        continue
                    processed_urls.add(absolute_url)

                    # ============ 新增跳过检查 ============
                    if should_skip_url(absolute_url):
                        #print_with_time(f"跳过资源文件: {absolute_url}")
                        continue
                    # ====================================

                    parsed = urlparse(absolute_url)
                    if parsed.scheme not in ('http', 'https'):
                        continue

                    # 域名判断
                    target_extracted = tldextract.extract(absolute_url)
                    target_domain = f"{target_extracted.domain}.{target_extracted.suffix}"
                    target_full_domain = f"{target_extracted.subdomain}.{target_extracted.domain}.{extracted.suffix}".lstrip(
                        '.')

                    if is_whitelist(absolute_url):
                        continue  # 白名单域名，直接跳过
                    elif target_domain != main_domain:
                        # 非白名单 & 外部域名 → 进入黑链检测
                        # 提交链接检测任务
                        future = executor.submit(
                            process_link,  # 改名为更通用的处理函数
                            current_url,
                            absolute_url,
                            headers,
                            output_file,
                            dead_links_file  # 传入死链文件路径
                        )
                        futures.append(future)
                    else:
                        # 同域名，继续爬取
                        if absolute_url not in visited:
                            queue.append((absolute_url, depth + 1))

                # 2. 新增处理纯文本中的URL
                text_elements = soup.find_all(text=True)
                url_pattern = re.compile(
                    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

                for text in text_elements:
                    urls = extract_urls_from_text(text)
                    for href in urls:
                        href = href.strip()
                        if not href:
                            continue

                        # 对于文本中的URL已经是绝对路径，不需要拼接
                        absolute_url = href

                        # 检查是否已经处理过这个URL
                        if absolute_url in processed_urls:
                            continue
                        processed_urls.add(absolute_url)

                        # 跳过检查
                        if should_skip_url(absolute_url):
                            continue

                        parsed = urlparse(absolute_url)
                        if parsed.scheme not in ('http', 'https'):
                            continue

                        # 域名判断
                        target_extracted = tldextract.extract(absolute_url)
                        target_domain = f"{target_extracted.domain}.{target_extracted.suffix}"
                        target_full_domain = f"{target_extracted.subdomain}.{target_extracted.domain}.{extracted.suffix}".lstrip(
                            '.')

                        if is_whitelist(absolute_url):
                            continue  # 白名单域名，直接跳过
                        elif target_domain != main_domain:
                            # 非白名单 & 外部域名 → 进入黑链检测
                            future = executor.submit(
                                process_link,
                                current_url,
                                absolute_url,
                                headers,
                                output_file,
                                dead_links_file
                            )
                            futures.append(future)
                        else:
                            # 同域名，继续爬取
                            if absolute_url not in visited:
                                queue.append((absolute_url, depth + 1))
                # 控制爬取速度
                time.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                print_with_time(f"页面处理异常: {current_url} - {str(e)}")

    # 扫描完成报告
    scan_result = (
        f"扫描完成！\n"
        f"总扫描页面: {len(visited)}\n"
        f"发现暗链: {dark_link_count}\n"
        f"发现死链: {dead_link_count}\n"
        f"暗链报告: {os.path.abspath(output_file)}\n"
        f"死链报告: {os.path.abspath(dead_links_file)}"
    )
    print_with_time(scan_result)


    # 发送企业微信总结通知
    send_wechat_alert(scan_result, is_final_report=True)

    # 打开结果文件所在目录
    try:
        if os.name == 'nt':  # Windows
            os.startfile(output_dir)
        elif os.name == 'posix':  # macOS/Linux
            os.system(f'open "{output_dir}"')
    except:
        pass


if __name__ == "__main__":
    main()
