# 1. ابدأ من صورة بايثون رسمية وخفيفة
FROM python:3.9-slim

# 2. قم بإنشاء مجلد عمل داخل الحاوية
WORKDIR /app

# 3. انسخ ملف المتطلبات أولاً
COPY requirements.txt .

# 4. قم بتثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# 5. انسخ كل ملفات المشروع الباقية
COPY . .

# 6. حدد المنفذ الذي سيعمل عليه التطبيق
EXPOSE 5000

# 7. الأمر النهائي لتشغيل الخادم
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]