from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import google.generativeai as genai
import fitz
import requests

app = Flask(__name__)
CORS(app)

# --- قراءة المفاتيح من بيئة التشغيل (Environment Variables) في Render ---
try:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("✅ تم تهيئة Google Gemini API بنجاح.")
except Exception as e:
    print(f"❌ فشل تهيئة Google Gemini API. السبب: {e}")
    gemini_model = None

HF_API_TOKEN = os.environ.get('HF_API_TOKEN')
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
SUMMARIZATION_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

def query_hf_api(payload):
    response = requests.post(SUMMARIZATION_API_URL, headers=headers, json=payload)
    return response.json()

# --- المسارات (Endpoints) ---

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# ✨ تم إرجاع الكود الصحيح هنا ✨
@app.route('/summarize', methods=['POST'])
def summarize_text():
    data = request.json
    text_to_summarize = data.get('text', '')
    if not text_to_summarize:
        return jsonify({"error": "لم يتم تقديم نص لتلخيصه"}), 400
    try:
        api_response = query_hf_api({"inputs": text_to_summarize})
        if isinstance(api_response, list) and 'summary_text' in api_response[0]:
            return jsonify({"response_type": "summary", "text": api_response[0]['summary_text']})
        else:
            if isinstance(api_response, dict) and 'error' in api_response:
                if 'currently loading' in api_response['error']:
                    return jsonify({"error": "نموذج التلخيص يتم تحميله على الخادم، يرجى المحاولة مرة أخرى خلال دقيقة."}), 503
                return jsonify({"error": f"خطأ من API التلخيص: {api_response['error']}"}), 500
            return jsonify({"error": "استقبلنا رداً غير متوقع."}), 500
    except Exception as e:
        return jsonify({"error": f"حدث خطأ أثناء الاتصال بالـ API: {str(e)}"}), 500

# ✨ تم إرجاع الكود الصحيح هنا ✨
@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf_file():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "لم يتم العثور على ملف PDF"}), 400
    file = request.files['pdf_file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "الرجاء رفع ملف بصيغة PDF فقط"}), 400
    try:
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        full_text = "".join(page.get_text() for page in pdf_document)
        pdf_document.close()
        if not full_text.strip():
            return jsonify({"error": "لم يتمكن النظام من استخراج أي نص من الملف."}), 400
        # نرسل النص المستخرج إلى نفس وظيفة API التلخيص
        return summarize_text_from_content(full_text)
    except Exception as e:
        return jsonify({"error": f"حدث خطأ أثناء معالجة ملف PDF: {str(e)}"}), 500
        
# وظيفة مساعدة لتجنب تكرار الكود
def summarize_text_from_content(content):
    api_response = query_hf_api({"inputs": content})
    if isinstance(api_response, list) and 'summary_text' in api_response[0]:
        return jsonify({"response_type": "summary", "text": api_response[0]['summary_text']})
    elif isinstance(api_response, dict) and 'error' in api_response:
        if 'currently loading' in api_response['error']:
            return jsonify({"error": "نموذج التلخيص يتم تحميله، يرجى المحاولة مرة أخرى خلال دقيقة."}), 503
        return jsonify({"error": f"خطأ من API التلخيص: {api_response['error']}"}), 500
    return jsonify({"error": "استقبلنا رداً غير متوقع."}), 500

# ✨ تم إرجاع الكود الصحيح هنا ✨
@app.route('/chat', methods=['POST'])
def chat_with_gemini():
    data = request.json
    user_message = data.get('message')
    if not user_message:
        return jsonify({"error": "الرجاء تقديم رسالة"}), 400
    if gemini_model is None:
        return jsonify({"error": "خدمة الذكاء الاصطناعي (Gemini) غير متاحة."}), 503
    
    lower_message = user_message.lower()
    if "ما اسمك" in lower_message or "من انت" in lower_message:
        return jsonify({"response_type": "chat", "text": "أنا Qaes Ai، نموذج ذكاء صناعي تم تطويره بواسطة قيس طلال الجازي."})
    if "معلومات عن المطور قيس" in lower_message:
        return jsonify({"response_type": "chat", "text": "قيس طلال غالب الجازي طالب MIS في جامعة إربد الأهلية."})
    if "ابن عمة قيس محمد" in lower_message or "علول" in lower_message:
        return jsonify({"response_type": "chat", "text": "محمد علول شخصية معروفة بحب الدعابة والجواكر."})
        
    try:
        response = gemini_model.generate_content(user_message)
        return jsonify({"response_type": "chat", "text": response.text})
    except Exception as e:
        return jsonify({"error": f"حدث خطأ أثناء الاتصال بـ Gemini: {str(e)}"}), 500

# تم تغيير debug إلى False لأنه لم يعد ضرورياً في بيئة الإنتاج
if __name__ == '__main__':
    # Render يحدد المنفذ تلقائياً، هذا السطر للتشغيل المحلي فقط
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))