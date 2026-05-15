import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def send_newsletter(subject, html_content, subscriber_list=None):
    gmail_user = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_password:
        print("⚠️ 缺少 Gmail 登入資訊 (GMAIL_ADDRESS 或 GMAIL_APP_PASSWORD)，跳過寄發電子報。")
        return False
        
    if not subscriber_list: 
        subscriber_file = "subscribers.txt"
        if os.path.exists(subscriber_file):
            with open(subscriber_file, "r", encoding="utf-8") as f:
                subscriber_list = [line.strip() for line in f if line.strip() and "@" in line]
        else:
            print("⚠️ 找不到 subscribers.txt，且未傳入訂閱者名單。跳過寄發。")
            return False

    if not subscriber_list:
        print("⚠️ 訂閱者名單為空，跳過寄發。")
        return False

    print(f"📧 準備發送電子報給 {len(subscriber_list)} 位訂閱者...")

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)

        for recipient in subscriber_list:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"越南晨間快訊 Good Morning Vietnam <{gmail_user}>"
            msg['To'] = recipient

            part = MIMEText(html_content, 'html')
            msg.attach(part)

            server.send_message(msg)
            print(f"  ✔️ 已發送至 {recipient}")

        server.quit()
        print("✅ 電子報發送完畢！")
        return True

    except Exception as e:
        print(f"❌ 寄信時發生錯誤: {e}")
        return False
