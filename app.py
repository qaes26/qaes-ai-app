from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import google.generativeai as genai
import fitz
import requests

app = Flask(__name__)
CORS(app)

# --- ✨ التعديل الأمني هنا: قراءة المفاتيح من بيئة التشغيل (Environment Variables) ✨ ---
try:
    # سيقرأ المفتاح من الإعدادات التي سنضعها في Render
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("✅ تم تهيئة Google Gemini API بنجاح.")
except Exception as e:
    print(f"❌ فشل تهيئة Google Gemini API. تأكد من وضع المفتاح في Environment Variables على Render.")
    gemini_model = None

# --- إعدادات الاتصال بـ API التلخيص ---
# سيقرأ المفتاح من الإعدادات التي سنضعها في Render
HF_API_TOKEN = os.environ.get('HF_API_TOKEN')
# نضيف "Bearer " تلقائياً هنا
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"} 
SUMMARIZATION_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

def query_hf_api(payload):
    response = requests.post(SUMMARIZATION_API_URL, headers=headers, json=payload)
    return response.json()

# ... (بقية الكود لا تتغير) ...
@app.route('/')
def serve_index(): return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path): return send_from_directory('.', path)

@app.route('/summarize', methods=['POST'])
def summarize_text():
    # ... الكود هنا لا يتغير ...
    pass # للتوضيح فقط

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf_file():
    # ... الكود هنا لا يتغير ...
    pass # للتوضيح فقط

@app.route('/chat', methods=['POST'])
def chat_with_gemini():
    # ... الكود هنا لا يتغير ...
    pass # للتوضيح فقط


if __name__ == '__main__':
    app.run(debug=False, port=5000) # تم تغيير debug إلى False للنشر