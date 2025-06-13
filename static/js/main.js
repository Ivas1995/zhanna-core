let socket = new WebSocket("ws://" + window.location.host + "/ws");
let mediaRecorder;
let audioContext = new (window.AudioContext || window.webkitAudioContext)();
const translations = {
    uk: {
        online: "Онлайн",
        offline: "Офлайн",
        response: "Відповідь Сакури",
        error: "Помилка",
        voice: "Голос",
        send: "Надіслати",
        scan: "Сканувати",
        trades: "Угоди",
        music: "Музика"
    }
};

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    const responseDiv = document.getElementById("response");
    if (data.response) {
        responseDiv.innerHTML += `<p class="text-blue-400 animate-pulse">${translations.uk.response}: ${data.response}</p>`;
        responseDiv.scrollTop = responseDiv.scrollHeight;
        if (data.type === "text") {
            speak(data.response);
        }
    } else if (data.error) {
        responseDiv.innerHTML += `<p class="text-red-500">${translations.uk.error}: ${data.error}</p>`;
    }
};

function sendCommand(command) {
    if (command) {
        socket.send(JSON.stringify({ command }));
        document.getElementById("commandInput").value = "";
    }
}

function startVoice() {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        setTimeout(() => {
            mediaRecorder.stop();
            stream.getTracks().forEach(track => track.stop());
        }, 5000);
        mediaRecorder.ondataavailable = function(e) {
            socket.send(JSON.stringify({ command: "voice" }));
        }
    }).catch(err => {
        console.error("Microphone access error:", err);
    });
}

function speak(text) {
    fetch("/speak?text=" + encodeURIComponent(text))
        .then(response => response.arrayBuffer())
        .then(buffer => audioContext.decodeAudioData(buffer))
        .then(decodedData => {
            const source = audioContext.createBufferSource();
            source.buffer = decodedData;
            source.connect(audioContext.destination);
            source.start();
        })
        .catch(err => console.error("TTS error:", err));
}

function checkOnlineStatus() {
    fetch("/static/ping")
        .then(response => {
            if (response.ok) {
                document.getElementById("online-status").textContent = translations.uk.online;
                document.getElementById("online-status").classList.remove("text-red-700");
                document.getElementById("online-status").classList.add("text-green-700");
            }
        })
        .catch(() => {
            document.getElementById("online-status").textContent = translations.uk.offline;
            document.getElementById("online-status").classList.remove("text-green-700");
            document.getElementById("online-status").classList.add("text-red-700");
        });
}

function updateChart() {
    fetch("/api/market-data?symbol=ALL")
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById("marketChart").getContext("2d");
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: data.symbols.map(symbol => ({
                        label: symbol.name,
                        data: symbol.prices,
                        borderColor: `#${Math.floor(Math.random()*16777215).toString(16)}`,
                        backgroundColor: `rgba(0, 255, 204, 0.2)`,
                        fill: true
                    }))
                },
                options: {
                    responsive: true,
                    scales: {
                        x: { display: true, title: { display: true, text: 'Час' } },
                        y: { display: true, title: { display: true, text: 'Ціна (USD)' } }
                    },
                    plugins: {
                        legend: { display: true, position: 'top' },
                        tooltip: { enabled: true }
                    }
                }
            });
        })
        .catch(err => console.error("Chart error:", err));
}

function toggleTheme() {
    document.body.classList.toggle("light-theme");
    localStorage.setItem("theme", document.body.classList.contains("light-theme") ? "light" : "dark");
}

document.addEventListener("DOMContentLoaded", () => {
    if (localStorage.getItem("theme") === "light") {
        document.body.classList.add("light-theme");
    }
    setInterval(checkOnlineStatus, 10000);
    checkOnlineStatus();
    updateChart();
});