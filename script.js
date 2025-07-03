document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    // عنوان URL للواجهة الخلفية (Flask)
    const BACKEND_URL = 'http://127.0.0.1:5000';

    const adjustTextareaHeight = () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    };

    const addMessage = (text, type, file = null) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${type}-message`);

        const messageAvatar = document.createElement('div');
        messageAvatar.classList.add('message-avatar');
        const avatarIcon = document.createElement('i');
        avatarIcon.classList.add('fas', type === 'user' ? 'fa-user' : 'fa-robot');
        messageAvatar.appendChild(avatarIcon);

        const messageContentDiv = document.createElement('div');
        messageContentDiv.classList.add('message-content');
        
        // ✨ تعديل: استخدام innerHTML مباشرة لمعالجة الـ strong tags وغيرها
        const paragraph = document.createElement('p');
        paragraph.innerHTML = text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        messageContentDiv.appendChild(paragraph);

        if (file) {
            const downloadBtn = document.createElement('a');
            downloadBtn.href = URL.createObjectURL(file);
            downloadBtn.download = file.name;
            downloadBtn.classList.add('download-pdf-btn-in-message');
            downloadBtn.innerHTML = (file.type === 'application/pdf') ? '<i class="fas fa-file-pdf"></i> تنزيل الملخص كـ PDF' : '<i class="fas fa-download"></i> تنزيل الملف';
            messageContentDiv.appendChild(downloadBtn);
        }

        messageDiv.appendChild(messageAvatar);
        messageDiv.appendChild(messageContentDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const sendMessage = async () => {
        const text = userInput.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        userInput.value = '';
        adjustTextareaHeight();

        // ✨ تعديل: اسم موحد ورسالة تفكير أفضل
        addMessage("<strong>Qaes Ai</strong> يفكر...", 'system');

        try {
            let endpoint;
            let body;
            
            if (text.toLowerCase().includes("لخص") || text.toLowerCase().includes("تلخيص") || text.toLowerCase().includes("ملخص")) {
                endpoint = '/summarize';
                body = JSON.stringify({ text: text });
            } else {
                endpoint = '/chat';
                body = JSON.stringify({ message: text });
            }
            
            const response = await fetch(`${BACKEND_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: body
            });
            
            const data = await response.json();

            const thinkingMessage = chatMessages.querySelector('.system-message:last-child');
            if (thinkingMessage && thinkingMessage.textContent.includes("يفكر...")) {
                thinkingMessage.remove();
            }

            if (response.ok) {
                if (data.response_type === "summary") {
                    const summaryText = data.text;
                    // ✨ تعديل: استخدام JSpdf لإنشاء PDF بشكل أفضل (خطوة اختيارية، لكن الكود الحالي يعمل)
                    // حالياً سنبقى على طريقة Blob البسيطة
                    const pdfBlob = new Blob([summaryText], { type: 'application/pdf' });
                    pdfBlob.name = `Qaes_Ai_Summary.pdf`;
                    addMessage(`**الملخص جاهز:**<br>${summaryText}`, 'system', pdfBlob);
                } else { // "chat" أو أي نوع آخر
                    addMessage(data.text, 'system');
                }
            } else {
                addMessage(`حدث خطأ: ${data.error || response.statusText}`, 'system');
            }

        } catch (error) {
            console.error('Error connecting to backend:', error);
            const thinkingMessage = chatMessages.querySelector('.system-message:last-child');
            if (thinkingMessage) thinkingMessage.remove();
            addMessage(`لا يمكن الاتصال بالخادم. تأكد من تشغيل ملف 'app.py' وأنك متصل بالإنترنت.`, 'system');
        }
    };

    userInput.addEventListener('input', adjustTextareaHeight);
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    adjustTextareaHeight();
});