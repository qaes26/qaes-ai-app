document.addEventListener('DOMContentLoaded', () => {
    // --- تعريف العناصر ---
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const uploadBtn = document.getElementById('upload-btn');
    const pdfUploadInput = document.getElementById('pdf-upload-input');
    const fileInfoDiv = document.getElementById('file-attachment-info');
    // ✨ إضافة جديدة: تعريف زر المحادثة الجديدة والرسالة الترحيبية ✨
    const newChatBtn = document.getElementById('new-chat-btn');
    const welcomeMessageHTML = document.getElementById('welcome-message').outerHTML;
    
    const { jsPDF } = window.jspdf;
    const BACKEND_URL = 'https://qaes-ai-app.onrender.com';
    let attachedFile = null;

    // --- وظيفة مسح المحادثة ---
    const startNewChat = () => {
        // قم بإزالة كل الرسائل ما عدا الرسالة الترحيبية الأصلية
        chatMessages.innerHTML = welcomeMessageHTML;
        userInput.value = '';
        attachedFile = null;
        if(fileInfoDiv) fileInfoDiv.style.display = 'none';
        adjustTextareaHeight();
    };

    // --- بقية الوظائف تبقى كما هي ---
    const adjustTextareaHeight = () => { /* ... لا تغيير ... */ };
    const addMessage = (text, type, fileContent = null) => { /* ... لا تغيير ... */ };
    const displayFileInfo = () => { /* ... لا تغيير ... */ };
    const sendMessage = async () => { /* ... لا تغيير ... */ };
    
    // --- ربط الأحداث ---
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
    uploadBtn.addEventListener('click', () => pdfUploadInput.click());
    pdfUploadInput.addEventListener('change', (e) => { if (e.target.files.length > 0) { attachedFile = e.target.files[0]; displayFileInfo(); } });
    userInput.addEventListener('input', adjustTextareaHeight);
    
    // ✨ إضافة جديدة: ربط الحدث لزر المحادثة الجديدة ✨
    newChatBtn.addEventListener('click', startNewChat);

    // -- (نسخ لصق للوظائف التي لم تتغير لتسهيل الأمر عليك) --
    adjustTextareaHeight = () => { userInput.style.height = 'auto'; userInput.style.height = (userInput.scrollHeight) + 'px'; };
    addMessage = (text, type, fileContent = null) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${type}-message`);
        const messageAvatar = document.createElement('div');
        messageAvatar.classList.add('message-avatar');
        const avatarIcon = document.createElement('i');
        avatarIcon.classList.add('fas', type === 'user' ? 'fa-user' : 'fa-robot');
        messageAvatar.appendChild(avatarIcon);
        const messageContentDiv = document.createElement('div');
        messageContentDiv.classList.add('message-content');
        const paragraph = document.createElement('p');
        paragraph.innerHTML = text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        messageContentDiv.appendChild(paragraph);
        if (fileContent && type === 'system') {
            const downloadBtn = document.createElement('button');
            downloadBtn.classList.add('download-pdf-btn-in-message');
            downloadBtn.innerHTML = '<i class="fas fa-file-pdf"></i> تنزيل الملخص كـ PDF';
            downloadBtn.onclick = () => {
                const doc = new jsPDF();
                doc.setR2L(true); doc.setFont("Helvetica");
                const lines = doc.splitTextToSize(fileContent, 180);
                doc.text(lines, 200, 20, { align: 'right' });
                doc.save('Qaes_Ai_Summary.pdf');
            };
            messageContentDiv.appendChild(downloadBtn);
        }
        messageDiv.appendChild(messageContentDiv);
        messageDiv.appendChild(messageAvatar);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };
    displayFileInfo = () => { if (attachedFile) { fileInfoDiv.style.display = 'block'; fileInfoDiv.innerHTML = `<span><button id="remove-file-btn">×</button> الملف المرفق: ${attachedFile.name}</span>`; document.getElementById('remove-file-btn').addEventListener('click', () => { attachedFile = null; pdfUploadInput.value = ''; fileInfoDiv.style.display = 'none'; }); } };
    sendMessage = async () => { const text = userInput.value.trim(); if (!text && !attachedFile) return; addMessage(attachedFile ? `تلخيص الملف: ${attachedFile.name}` : text, 'user'); userInput.value = ''; adjustTextareaHeight(); addMessage("<strong>Qaes Ai</strong> يفكر...", 'system'); const thinkingMessage = chatMessages.querySelector('.system-message:last-child'); try { let response; const isSummaryRequest = attachedFile || text.split(' ').length > 30; if (isSummaryRequest) { let endpoint = attachedFile ? '/summarize_pdf' : '/summarize'; let options = { method: 'POST' }; if (attachedFile) { const formData = new FormData(); formData.append('pdf_file', attachedFile); options.body = formData; } else { options.headers = { 'Content-Type': 'application/json' }; options.body = JSON.stringify({ text: text }); } response = await fetch(`${BACKEND_URL}${endpoint}`, options); } else { response = await fetch(`${BACKEND_URL}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text }) }); } attachedFile = null; if (fileInfoDiv) fileInfoDiv.style.display = 'none'; if (thinkingMessage) thinkingMessage.remove(); const data = await response.json(); if (response.ok) { if (data.response_type === "summary") { addMessage(`**الملخص جاهز:**<br>${data.text}`, 'system', data.text); } else { addMessage(data.text, 'system'); } } else { addMessage(`حدث خطأ: ${data.error || response.statusText}`, 'system'); } } catch (error) { if (thinkingMessage) thinkingMessage.remove(); addMessage(`لا يمكن الاتصال بالخادم. تأكد من أن الموقع يعمل أو حاول مرة أخرى لاحقاً.`, 'system'); console.error('Error:', error); } };
});