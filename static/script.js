// Run only when page loads
window.onload = function () {
    let chatbox = document.getElementById("chatbox");

    if (!chatbox) return;

    let welcomeDiv = document.createElement("div");
    welcomeDiv.className = "message bot";
    welcomeDiv.innerText =
        "👋 Welcome!\n\nEnter the experiment name to get details.\n\nExample:\n• Monostable Multivibrator\n• Astable Multivibrator\n\nYou can also ask:\n• Show diagram\n• Show graph";

    chatbox.appendChild(welcomeDiv);
};


// Enter key support
let inputField = document.getElementById("userInput");
if (inputField) {
    inputField.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
}


// 💬 Send message
function sendMessage() {
    let input = document.getElementById("userInput");
    let chatbox = document.getElementById("chatbox");

    if (!input || !chatbox) return;

    let message = input.value.trim();
    if (message === "") return;

    // 🧑 User message
    let userDiv = document.createElement("div");
    userDiv.className = "message user";
    userDiv.innerText = message;
    chatbox.appendChild(userDiv);

    input.value = "";

    // 🤖 Typing animation (FIXED)
    let typingDiv = document.createElement("div");
    typingDiv.className = "message bot";
    typingDiv.id = "typing";
    chatbox.appendChild(typingDiv);

    let dots = 0;
    let typingInterval = setInterval(() => {
        dots = (dots + 1) % 4;
        typingDiv.innerText = "Typing" + ".".repeat(dots);
    }, 500);

    scrollToBottom();

    // 🔄 API call
    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: message })
    })
        .then(res => res.json())
        .then(data => {

            clearInterval(typingInterval);
            typingDiv.remove();

            let botDiv = document.createElement("div");
            botDiv.className = "message bot";

            // Text
            let text = document.createElement("div");
            text.innerText = data.text;
            botDiv.appendChild(text);

            // 🔥 IMAGE (Drive + fallback link)
            if (data.image) {
                let img = document.createElement("img");
                img.src = data.image;

                img.style.width = "100%";
                img.style.maxHeight = "300px";
                img.style.objectFit = "contain";
                img.style.marginTop = "10px";
                img.style.borderRadius = "10px";

                // ❌ If image fails → show link
                img.onerror = function () {
                    img.remove();

                    let link = document.createElement("a");
                    link.href = data.image;
                    link.target = "_blank";
                    link.innerText = "🔗 Open Circuit Diagram";
                    link.className = "download-btn";

                    botDiv.appendChild(link);
                };

                botDiv.appendChild(img);
            }

            // 🔥 GRAPH (same logic)
            if (data.graph) {
                let img = document.createElement("img");
                img.src = data.graph;

                img.style.width = "100%";
                img.style.maxHeight = "300px";
                img.style.objectFit = "contain";
                img.style.marginTop = "10px";
                img.style.borderRadius = "10px";

                img.onerror = function () {
                    img.remove();

                    let link = document.createElement("a");
                    link.href = data.graph;
                    link.target = "_blank";
                    link.innerText = "🔗 Open Graph";
                    link.className = "download-btn";

                    botDiv.appendChild(link);
                };

                botDiv.appendChild(img);
            }

            // 🔥 PDF DOWNLOAD (FIXED)
            if (data.pdf) {
                let link = document.createElement("a");

                // Convert Drive link to download format
                let fileIdMatch = data.pdf.match(/id=([^&]+)/);
                if (fileIdMatch) {
                    link.href = `https://drive.google.com/uc?export=download&id=${fileIdMatch[1]}`;
                } else {
                    link.href = data.pdf;
                }

                link.className = "download-btn";
                link.innerText = "Download PDF 📄";
                link.setAttribute("download", "");
                link.target = "_blank";

                botDiv.appendChild(link);
            }

            chatbox.appendChild(botDiv);
            scrollToBottom();
        })
        .catch(err => {
            console.error(err);

            clearInterval(typingInterval);
            typingDiv.remove();

            let errorDiv = document.createElement("div");
            errorDiv.className = "message bot";
            errorDiv.innerText = "⚠️ Server error.";
            chatbox.appendChild(errorDiv);

            scrollToBottom();
        });
}


// 🔽 Scroll
function scrollToBottom() {
    let chatbox = document.getElementById("chatbox");
    if (!chatbox) return;

    chatbox.scrollTo({
        top: chatbox.scrollHeight,
        behavior: "smooth"
    });
}


// 🎤 Voice input
function startVoice() {
    if (!('webkitSpeechRecognition' in window)) {
        alert("Voice recognition not supported");
        return;
    }

    let recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";

    let btn = document.querySelector(".mic-btn");

    if (btn) btn.classList.add("listening");

    recognition.start();

    recognition.onresult = function (event) {
        if (btn) btn.classList.remove("listening");

        let transcript = event.results[0][0].transcript;
        document.getElementById("userInput").value = transcript;
        sendMessage();
    };

    recognition.onerror = function () {
        if (btn) btn.classList.remove("listening");
        alert("Voice error");
    };
}


// ⚡ Quick send
function quickSend(text) {
    let input = document.getElementById("userInput");
    if (!input) return;

    input.value = text;
    sendMessage();
}