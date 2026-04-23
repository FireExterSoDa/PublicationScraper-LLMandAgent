import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
import time  # 新增模块：用于控制重试等待时间

def fetch_arxiv_papers():
    print("开始从 arXiv 获取最新论文...")
    # 使用 Python 官方库自动安全编码网址，彻底告别 400 错误
    base_url = 'http://export.arxiv.org/api/query?'
    params = {
        'search_query': 'all:LLM OR all:agent',
        'sortBy': 'submittedDate',
        'sortOrder': 'desc',
        'max_results': 5
    }
    url = base_url + urllib.parse.urlencode(params)
    
    # 终极解法：遵循 arXiv 官方建议，在 User-Agent 中填写真实邮箱，获取信任放行
    headers = {
        'User-Agent': 'DailyPaperScraper/1.0 (mohq6@mail2.sysu.edu.cn)'
    }
    req = urllib.request.Request(url, headers=headers)
    
    # 增加自动重试机制：最多尝试 3 次
    for attempt in range(3):
        try:
            response = urllib.request.urlopen(req)
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            
            papers = []
            for entry in root.findall('atom:entry', namespace):
                title = entry.find('atom:title', namespace).text.strip().replace('\n', ' ')
                summary = entry.find('atom:summary', namespace).text.strip().replace('\n', ' ')
                link = entry.find('atom:id', namespace).text
                
                paper_html = f"""
                <div style='margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee;'>
                    <h3 style='color: #2980b9; margin-bottom: 5px;'>{title}</h3>
                    <p style='margin: 5px 0;'><b>链接:</b> <a href='{link}'>{link}</a></p>
                    <p style='margin: 5px 0; color: #34495e; line-height: 1.5;'><b>摘要:</b> {summary[:350]}...</p>
                </div>
                """
                papers.append(paper_html)
            
            if papers:
                print("✅ 论文获取成功！")
                return "".join(papers)
            else:
                print("⚠️ API 响应正常，但没有解析到论文数据。")
                return None
                
        except urllib.error.HTTPError as e:
            print(f"第 {attempt + 1} 次尝试失败: HTTP Error {e.code}")
            if e.code == 429:
                print("触发频次限制，等待 5 秒后重试...")
                time.sleep(5)
            else:
                break  # 如果是 400 等其他错误，直接跳出重试
        except Exception as e:
            print(f"获取论文时发生未知错误: {e}")
            break
            
    print("❌ 多次尝试后依然获取失败，取消后续操作。")
    return None

def send_email(content):
    print("准备发送邮件...")
    sender_email = os.environ.get('EMAIL_SENDER')
    password = os.environ.get('EMAIL_PASSWORD')
    receiver_email = "mohq6@mail2.sysu.edu.cn"
    
    # 请确保此处的 smtp_server 和你的发件邮箱匹配
    # QQ: smtp.qq.com | 163: smtp.163.com | Gmail: smtp.gmail.com
    smtp_server = "smtp.qq.com" 
    smtp_port = 465

    if not sender_email or not password:
        print("❌ 错误：未找到发件邮箱或授权码环境变量！")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    html_msg = f"""
    <html>
    <body style='font-family: Arial, sans-serif; padding: 20px;'>
        <h2 style='color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px;'>
            🚀 {today} LLM & Agent 论文每日追踪
        </h2>
        {content}
        <p style='color: #7f8c8d; font-size: 12px; margin-top: 30px;'>
            <i>提示：此邮件由 GitHub Actions 自动化定时抓取发送。</i>
        </p>
    </body>
    </html>
    """

    message = MIMEText(html_msg, 'html', 'utf-8')
    message['From'] = Header(f"Paper Bot <{sender_email}>")
    message['To'] = receiver_email
    message['Subject'] = Header(f'Paper Daily: {today} 最新大模型与智能体文献', 'utf-8')

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender_email, password)
        server.sendmail(sender_email, [receiver_email], message.as_string())
        server.quit()
        print(f"✅ 邮件已成功发送至 {receiver_email}！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    content_html = fetch_arxiv_papers()
    if content_html:
        send_email(content_html)
