from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import google.generativeai as genai
import fitz
import requests # مكتبة لإجراء طلبات الإنترنت

app = Flask(__name__)
CORS(app)

# --- تهيئة Gemini API ---
try:
    # ⚠️ تذكر: هذا المفتاح مكشوف. قم بتغييره لاحقاً.
    GEMINI_API_KEY = "AIzaSyBigvIW-N4aHPAvebs__w4l1Mbur0AIQ8A"
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("✅ تم تهيئة Google Gemini API بنجاح.")
except Exception as e:
    print(f"❌ فشل تهيئة Google Gemini API: {e}")
    gemini_model = None

# --- ✨ التعديل الجذري: إعدادات الاتصال بـ API التلخيص ✨ ---
# ⚠️ مهم: استبدل "hf_YOUR_TOKEN_HERE" بالمفتاح الذي نسخته من Hugging Face
HF_API_TOKEN = "Bearer hf_YOUR_TOKEN_HERE" 
SUMMARIZATION_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": HF_API_TOKEN}

def query_hf_api(payload):
    """وظيفة لإرسال طلب إلى API الخاص بـ Hugging Face"""
    response = requests.post(SUMMARIZATION_API_URL, headers=headers, json=payload)
    return response.json()

# --- المسارات (Endpoints) ---

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/summarize', methods=['POST'])
def summarize_text():
    data = request.json
    text_to_summarize = data.get('text', '').replace('لخص', '').replace('تلخيص', '').replace('ملخص', '').strip()
    if not text_to_summarize:
        return jsonify({"error": "لم يتم تقديم نص لتلخيصه"}), 400
    
    try:
        api_response = query_hf_api({"inputs": text_to_summarize})
        
        if isinstance(api_response, list) and 'summary_text' in api_response[0]:
            summary = api_response[0]['summary_text']
            return jsonify({"response_type": "summary", "text": summary})
        elif 'error' in api_response:
             # إذا كان النموذج يحتاج لوقت ليحمل، نعطي رسالة واضحة
            if 'is currently loading' in api_response['error']:
                return jsonify({"error": "نموذج التلخيص يتم تحميله على الخادم، يرجى المحاولة مرة أخرى خلال دقيقة."}), 503
            return jsonify({"error": f"خطأ من API التلخيص: {api_response['error']}"}), 500
        else:
            return jsonify({"error": "استقبلنا رداً غير متوقع من خدمة التلخيص."}), 500

    except Exception as e:
        return jsonify({"error": f"حدث خطأ أثناء الاتصال بـ API: {str(e)}"}), 500

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
            return jsonify({"error": "لم يتمكن النظام من استخراج أي نص من ملف الـ PDF."}), 400
        
        api_response = query_hf_api({"inputs": full_text})

        if isinstance(api_response, list) and 'summary_text' in api_response[0]:
            summary = api_response[0]['summary_text']
            return jsonify({"response_type": "summary", "text": summary})
        elif 'error' in api_response:
            if 'is currently loading' in api_response['error']:
                return jsonify({"error": "نموذج التلخيص يتم تحميله على الخادم، يرجى المحاولة مرة أخرى خلال دقيقة."}), 503
            return jsonify({"error": f"خطأ من API التلخيص: {api_response['error']}"}), 500
        else:
            return jsonify({"error": "استقبلنا رداً غير متوقع من خدمة التلخيص."}), 500
            
    except Exception as e:
        return jsonify({"error": f"حدث خطأ أثناء معالجة ملف PDF: {str(e)}"}), 500

# مسار الدردشة مع Gemini لا يتغير
@app.route('/chat', methods=['POST'])
def chat_with_gemini():
    data = request.json
    user_message = data.get('message')
    if not user_message:
        return jsonify({"error": "الرجاء تقديم رسالة"}), 400
    lower_message = user_message.lower()
    if "ما اسمك" in lower_message or "من انت" in lower_message:
        return jsonify({"response_type": "chat", "text": "أنا Qaes Ai..."})
    if "معلومات عن المطور قيس" in lower_message:
        return jsonify({"response_type": "chat", "text": "قيس طلال غالب الجازي..."})
    if "ابن عمة قيس محمد" in lower_message or "علول" in lower_message:
        return jsonify({"response_type": "chat", "text": "محمد علول هو شخصية..."})
    if gemini_model is None:
        return jsonify({"error": "خدمة الذكاء الاصطناعي (Gemini) غير متاحة."}), 503
    try:
        response = gemini_model.generate_content(user_message)
        return jsonify({"response_type": "chat", "text": response.text})
    except Exception as e:
        return jsonify({"error": f"حدث خطأ أثناء الاتصال بـ Gemini: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)