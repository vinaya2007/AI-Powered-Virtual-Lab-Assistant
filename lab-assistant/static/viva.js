let selectedExperiment = "";
let vivaStarted = false;

let currentQuestion = "";

// 🧠 Start Viva when page loads
window.onload = function () {
    let chatbox = document.getElementById("chatbox");
    if (!chatbox) return;

    showBotMessage("🎤 Viva Practice\n\nWhich experiment do you want to practice?");
};


// 🎯 Get new question
function getNewQuestion() {
    let experiments = [
        "pn junction diode",
        "half wave rectifier",
        "full wave rectifier"
    ];
    let randomExp = experiments[Math.floor(Math.random() * experiments.length)];

    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: `viva ${randomExp}`
        })
    })
    .then(res => res.json())
    .then(data => {
        currentQuestion = data.text;
        showBotMessage(currentQuestion);
    });
}


// 🧑 Submit answer
function sendAnswer() {
    let input = document.getElementById("userInput");
    let answer = input.value.trim();

    if (answer === "") return;

    showUserMessage(answer);
    input.value = "";

    // 🔥 STEP 1: If viva NOT started → treat input as experiment
    if (!vivaStarted) {
        selectedExperiment = answer.toLowerCase();
        vivaStarted = true;

        showBotMessage(`Starting viva for ${selectedExperiment}...`);

        getNewQuestion();
        return;
    }

    // 🔥 STEP 2: Normal viva flow
    showBotMessage("Evaluating your answer...");

    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: `Question: ${currentQuestion}. Student answer: ${answer}. Evaluate briefly and give correct explanation.`
        })
    })
    .then(res => res.json())
    .then(data => {
        showBotMessage(data.text);

        setTimeout(() => {
            getNewQuestion();
        }, 2000);
    })
    .catch(() => {
        showBotMessage("⚠️ Error evaluating answer.");
    });
}

// 💬 UI helpers
function showUserMessage(msg) {
    let chatbox = document.getElementById("chatbox");

    let div = document.createElement("div");
    div.className = "message user";
    div.innerText = msg;

    chatbox.appendChild(div);
    scrollToBottom();
}

function showBotMessage(msg) {
    let chatbox = document.getElementById("chatbox");

    let div = document.createElement("div");
    div.className = "message bot";
    div.innerText = msg;

    chatbox.appendChild(div);
    scrollToBottom();
}


// 🔽 Smooth scroll
function scrollToBottom() {
    let chatbox = document.getElementById("chatbox");

    chatbox.scrollTo({
        top: chatbox.scrollHeight,
        behavior: "smooth"
    });
}


// ⌨️ Enter key support
let inputField = document.getElementById("userInput");
if (inputField) {
    inputField.addEventListener("keypress", function(e) {
        if (e.key === "Enter") {
            sendAnswer();
        }
    });
}