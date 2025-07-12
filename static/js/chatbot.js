const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatBox = document.getElementById("chat-box");
const fileInput = document.getElementById("file-input");
const fileStatus = document.getElementById("file-status");

let selectedFiles = [];

// ✅ 파일 선택 시 중복 방지 및 표시
fileInput.addEventListener("change", () => {
  Array.from(fileInput.files).forEach(file => {
    if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
      selectedFiles.push(file);
    }
  });
  updateFileDisplay();
  fileInput.value = ""; // 동일 파일 다시 선택 가능하도록 초기화
});

// ✅ 첨부파일 리스트 표시 함수
function updateFileDisplay() {
  fileStatus.innerHTML = "";
  selectedFiles.forEach((file, idx) => {
    const container = document.createElement("div");
    container.className = "flex justify-between items-center bg-blue-50 text-blue-800 px-4 py-1 rounded-md";

    const fileName = document.createElement("span");
    fileName.className = "truncate max-w-[80%]";
    fileName.textContent = `📎 ${file.name}`;

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "text-xs text-white bg-red-500 hover:bg-red-600 px-3 py-1 rounded transition";
    deleteBtn.textContent = "삭제";
    deleteBtn.addEventListener("click", () => {
      selectedFiles.splice(idx, 1);
      updateFileDisplay();
    });

    container.appendChild(fileName);
    container.appendChild(deleteBtn);
    fileStatus.appendChild(container);
  });
}

// ✅ 폼 제출 처리
form.addEventListener("submit", function (e) {
  e.preventDefault();

  const message = input.value.trim();
  if (!message && selectedFiles.length === 0) {
    alert("❗ 메시지나 첨부파일 중 하나는 입력해야 합니다.");
    return;
  }

  if (message) {
    const userMsg = document.createElement("div");
    userMsg.className = "text-right";
    userMsg.innerHTML = `<div class="inline-block bg-blue-500 text-white rounded-lg px-4 py-2">${message}</div>`;
    chatBox.appendChild(userMsg);
  }

  if (selectedFiles.length > 0) {
    selectedFiles.forEach(file => {
      const fileMsg = document.createElement("div");
      fileMsg.className = "text-right";
      fileMsg.innerHTML = `<div class="inline-block bg-blue-100 text-blue-800 rounded-lg px-4 py-2">📎 첨부파일 전송됨: ${file.name}</div>`;
      chatBox.appendChild(fileMsg);
    });
  }

  chatBox.scrollTop = chatBox.scrollHeight;

  const formData = new FormData();
  if (message) formData.append("message", message);
  selectedFiles.forEach(file => formData.append("files", file));

  fetch("https://3a400c992d08.ngrok-free.app/api/chat", {
    method: "POST",
    body: formData,
  })
    .then(async res => {
      const contentType = res.headers.get("content-type") || "";
      const isJson = contentType.includes("application/json");

      const data = isJson ? await res.json() : await res.text();

      if (!res.ok) {
        const errorMsg = isJson
          ? (data?.reply || `❌ 서버 오류: ${res.status}`)
          : data || `❌ 서버 오류: ${res.status}`;
        throw new Error(errorMsg);
      }

      const botMsg = document.createElement("div");
      botMsg.className = "text-left";

      const reply = isJson ? data?.reply : data;
      if (reply && reply.trim()) {
        botMsg.innerHTML = `<div class="inline-block bg-gray-200 text-gray-800 rounded-lg px-4 py-2 whitespace-pre-wrap">${reply}</div>`;
      } else {
        botMsg.innerHTML = `<div class="inline-block bg-red-100 text-red-600 rounded-lg px-4 py-2">❗ GPT 응답이 없습니다.</div>`;
      }

      chatBox.appendChild(botMsg);
      chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {
      const errorMsg = document.createElement("div");
      errorMsg.className = "text-left";
      errorMsg.innerHTML = `<div class="inline-block bg-red-100 text-red-600 rounded-lg px-4 py-2">❌ 오류: ${error.message}</div>`;
      chatBox.appendChild(errorMsg);
    });

  input.value = "";
  selectedFiles = [];
  updateFileDisplay();
});
