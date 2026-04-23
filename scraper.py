import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

def fetch_arxiv_papers():
    print("开始从 arXiv 获取最新论文...")
    # 构造检索词：大语言模型 或 LLM 或 智能体
    # 修改后的代码（去掉了双引号，并直接使用加号拼接，防止解析错误）：
    query = 'all:LLM+OR+all:agent'
    url = f'http://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=desc&max_results=5'
    
    try:
        # 修改后的代码（添加了浏览器伪装头部）
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', namespace).text.strip().replace('\n', ' ')
            link = entry.find('atom:id', namespace).text
            
            # 排版 HTML 格式
            paper_html = f"""
            <div style='margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee;'>
                <h3 style='color: #2980b9; margin-bottom: 5px;'>{title}</h3>
                <p style='margin: 5px 0;'><b>链接:</b> <a href='{link}'>{link}</a></p>
                <p style='margin: 5px 0; color: #34495e; line-height: 1.5;'><b>摘要:</b> {summary[:350]}...</p>
            </div>
            """
            papers.append(paper_html)
        
        return "".join(papers)
    except Exception as e:
        print(f"获取论文失败: {e}")
        return None

def send_email(content):
    print("准备发送邮件...")
    # 1. 读取环境变量中的发件人配置
    sender_email = os.environ.get('EMAIL_SENDER')
    password = os.environ.get('EMAIL_PASSWORD')
    
    # 接收人设定为您指定的邮箱
    receiver_email = "mohq6@mail2.sysu.edu.cn"
    
    # 2. 邮件服务器配置 
    # 如果您用的发件箱不是 QQ 邮箱，请修改下方的 smtp_server
    # QQ邮箱: smtp.qq.com | 163邮箱: smtp.163.com | Gmail: smtp.gmail.com
    smtp_server = "smtp.qq.com" 
    smtp_port = 465

    if not sender_email or not password:
        print("❌ 错误：未找到发件邮箱或授权码环境变量！")
        return

    # 3. 构造邮件正文
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

    # 4. 发送邮件
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
    else:
        print("未获取到论文内容，取消发送邮件。")
