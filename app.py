from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import google.generativeai as genai
import fitz
import requests

# ✨ التعديل الوحيد والمهم هنا: نخبر Flask صراحة بمكان الملفات الثابتة ✨
# هذا سيجعل ملفات CSS و JS تعمل على الخادم
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# --- تهيئة Gemini API (لا تغيير هنا) ---
try:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("✅ تم تهيئة Google Gemini API بنجاح.")
except Exception as e:
    print(f"❌ فشل تهيئة Google Gemini API. السبب: {e}")
    gemini_model = None

# --- إعدادات الاتصال بـ API التلخيص (لا تغيير هنا) ---
HF_API_TOKEN = os.environ.get('HF_API_TOKEN')
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
SUMMARIZATION_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

def query_hf_api(payload):
    response = requests.post(SUMMARIZATION_API_URL, headers=headers, json=payload)
    return response.json()

# --- المسارات (Endpoints) ---

# ✨ تم تعديل هذا المسار ليكون أكثر احترافية ويخدم كل الملفات بما فيها index.html ✨
@app.route('/')
@app.route('/<path:path>')
def serve_files(path='index.html'):
    # هذه الوظيفة الآن تخدم index.html عند الطلب الرئيسي، وأي ملف آخر عند طلبه بالاسم
    return send_from_directory('.', path)

# --- بقية الوظائف تبقى كما هي تماماً ---

@app.route('/summarize', methods=['POST'])
def summarize_text():
    data = request.json
    text_to_summarize = data.get('text', '')
    if not text_to_summarize: return jsonify({"error": "لم يتم تقديم نص لتلخيصه"}), 400
    try:
        api_response = query_hf_api({"inputs": text_to_summarize})
        if isinstance(api_response, list) and 'summary_text' in api_response[0]:
            return jsonify({"response_type": "summary", "text": api_response[0]['summary_text']})
        elif 'error' in api_response:
            if 'currently loading' in api_response['error']: return jsonify({"error": "نموذج التلخيص يتم تحميله على الخادم، يرجى المحاولة مرة أخرى خلال دقيقة."}), 503
            return jsonify({"error": f"خطأ من API التلخيص: {api_response['error']}"}), 500
        else: return jsonify({"error": "استقبلنا رداً غير متوقع."}), 500
    except Exception as e: return jsonify({"error": f"حدث خطأ أثناء الاتصال بالـ API: {str(e)}"}), 500

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf_file():
    if 'pdf_file' not in request.files: return jsonify({"error": "لم يتم العثور على ملف PDF"}), 400
    file = request.files['pdf_file']
    if not file.filename.lower().endswith('.pdf'): return jsonify({"error": "الرجاء رفع ملف بصيغة PDF فقط"}), 400
    try:
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        full_text = "".join(page.get_text() for page in pdf_document)
        pdf_document.close()
        if not full_text.strip(): return jsonify({"error": "لم يتمكن النظام من استخراج أي نص من الملف."}), 400
        api_response = query_hf_api({"inputs": full_text})
        if isinstance(api_response, list) and 'summary_text' in api_response[0]:
            return jsonify({"response_type": "summary", "text": api_response[0]['summary_text']})
        elif 'error' in api_response:
            if 'currently loading' in api_response['error']: return jsonify({"error": "نموذج التلخيص يتم تحميله، يرجى المحاولة مرة أخرى خلال دقيقة."}), 503
            return jsonify({"error": f"خطأ من API التلخيص: {api_response['error']}"}), 500
        return jsonify({"error": "استقبلنا رداً غير متوقع."}), 500
    except Exception as e: return jsonify({"error": f"حدث خطأ أثناء معالجة ملف PDF: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
def chat_with_gemini():
    data = request.json
    user_message = data.get('message')
    if not user_message: return jsonify({"error": "الرجاء تقديم رسالة"}), 400
    if gemini_model is None: return jsonify({"error": "خدمة الذكاء الاصطناعي (Gemini) غير متاحة."}), 503
    lower_message = user_message.lower()
    if "ما اسمك" in lower_message or "من انت" in lower_message: return jsonify({"response_type": "chat", "text": "أنا Qaes Ai..."})
    if "معلومات عن المطور قيس" in lower_message: return jsonify({"response_type": "chat", "text": "قيس طلال غالب الجازي..."})
    if "ابن عمة قيس محمد" in lower_message or "علول" in lower_message: return jsonify({"response_type": "chat", "text": "محمد علول هو شخصية..."})
    try:
        response = gemini_model.generate_content(user_message)
        return jsonify({"response_type": "chat", "text": response.text})
    except Exception as e: return jsonify({"error": f"حدث خطأ أثناء الاتصال بـ Gemini: {str(e)}"}), 500

if __name__ == '__main__':
    # Render يحدد المنفذ تلقائياً
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))