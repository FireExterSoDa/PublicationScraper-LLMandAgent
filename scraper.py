import arxiv
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

def fetch_arxiv_papers():
    print("开始从 arXiv 获取最新论文...")
    try:
        # 配置官方客户端，自带延迟重试，完美避开 429 和 400 报错
        client = arxiv.Client(
            page_size=5,
            delay_seconds=3,
            num_retries=3
        )
        
        # 自由组合你想要的关键词
        search = arxiv.Search(
            query='all:"Large Language Model" OR all:"LLM" OR all:"Autonomous Agent"',
            max_results=5,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        papers = []
        # 直接遍历对象，不再需要自己去解析 XML
        for result in client.results(search):
            title = result.title.replace('\n', ' ')
            summary = result.summary.replace('\n', ' ')
            link = result.entry_id
            
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
            print("⚠️ API 响应正常，但未找到匹配的论文。")
            return None
            
    except Exception as e:
        print(f"❌ 获取论文失败: {e}")
        return None

def send_email(content):
    print("准备发送邮件...")
    sender_email = os.environ.get('EMAIL_SENDER')
    password = os.environ.get('EMAIL_PASSWORD')
    receiver_email = "mohq6@mail2.sysu.edu.cn"
    
    # 邮箱 SMTP 服务器 (默认为 QQ 邮箱)
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
