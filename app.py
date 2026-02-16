import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# ดึงค่า Config จาก Environment Variables (ที่เราจะไปตั้งใน Render)
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# ตั้งค่า Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- ใส่ System Instruction ของคุณตรงนี้ ---
system_instruction = """
คุณคือ "One OS Assistant" ผู้ช่วยส่วนตัวของผู้ใช้งาน 
คุณมีความเชี่ยวชาญด้าน Python, Flow Logic, และการวิเคราะห์ความปลอดภัย 
คุณต้องตอบคำถามด้วยความเฉลียวฉลาด กระชับ และเป็นกันเองเหมือนคู่หู 
หากผู้ใช้ส่งเบอร์โทรศัพท์มา ให้วิเคราะห์ความเป็นไปได้ว่าเป็นเบอร์จากประเทศอะไรและค่ายไหน
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=system_instruction
)

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    
    # ส่งข้อความให้ Gemini วิเคราะห์
    try:
        response = model.generate_content(user_text)
        reply_text = response.text
    except Exception as e:
        reply_text = f"ขออภัยครับ เกิดข้อผิดพลาด: {str(e)}"

    # ตอบกลับไปที่ LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
