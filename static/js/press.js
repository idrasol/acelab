document.addEventListener('DOMContentLoaded', function () {
  // ========== 1. 부처 버튼 동적 삽입 ==========
  const ministryContainer = document.getElementById('ministry-buttons-container');
  if (ministryContainer) {
    fetch('/static/ministry-buttons.html')
      .then(response => response.text())
      .then(html => {
        ministryContainer.innerHTML = html;

        const buttons = document.querySelectorAll('.ministry-btn');
        const input = document.getElementById('ministry-input');
        const newsList = document.getElementById('latest-news-list');
        const dummyNews = (ministry) => Array.from({ length: 10 }, (_, i) => ({
          title: `${ministry} 관련 뉴스 제목 ${i + 1}`,
          url: `#${ministry}-news-${i + 1}`
        }));

        buttons.forEach(btn => {
          btn.addEventListener('click', function () {
            buttons.forEach(b => b.classList.remove('!bg-blue-600', '!text-white', '!border-blue-600', 'ring-2', 'ring-blue-400'));
            btn.classList.add('!bg-blue-600', '!text-white', '!border-blue-600', 'ring-2', 'ring-blue-400');
            input.value = btn.textContent;
            const news = dummyNews(btn.textContent);
            newsList.innerHTML = `<ul class='list-decimal pl-6 space-y-1'>` +
              news.map(n => `<li><a href='${n.url}' class='text-blue-700 hover:underline' target='_blank'>${n.title}</a></li>`).join('') +
              `</ul>`;
          });
        });
      });
  }

  // ========== 2. 파일 업로드 관련 ==========
  const fileInput = document.getElementById('file-input');
  const fileListDiv = document.getElementById('file-list');
  const resetBtn = document.getElementById('reset-files');
  let selectedFiles = [];

  function updateFileList() {
    if (!fileListDiv) return;
    fileListDiv.innerHTML = "";

    if (selectedFiles.length > 0) {
      selectedFiles.forEach((file, idx) => {
        const container = document.createElement('div');
        container.className = "flex flex-col px-3 py-2 bg-blue-50 border border-blue-200 rounded-md mt-1";

        const topRow = document.createElement('div');
        topRow.className = "flex items-center gap-2";
        topRow.innerHTML = `<span class="text-blue-600">📄</span><span class="text-sm text-blue-900 truncate">${file.name}</span>`;

        const removeBtn = document.createElement('button');
        removeBtn.className = "ml-auto bg-red-500 hover:bg-red-600 text-white text-xs px-3 py-1 rounded shadow-sm transition";
        removeBtn.innerText = "삭제";
        removeBtn.addEventListener('click', () => {
          selectedFiles.splice(idx, 1);
          updateFileList();
        });

        container.appendChild(topRow);
        container.appendChild(removeBtn);
        fileListDiv.appendChild(container);
      });
    } else {
      fileListDiv.innerHTML = '<span class="text-blue-400">아직 파일이 없습니다.</span>';
    }
  }

  if (fileInput) {
    fileInput.addEventListener('change', function (e) {
      Array.from(e.target.files).forEach(file => {
        if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
          selectedFiles.push(file);
        }
      });
      updateFileList();
      fileInput.value = "";
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      selectedFiles = [];
      updateFileList();
    });
  }

  // ========== 3. 보도자료 제출 처리 ==========
  const pressForm = document.querySelector('#press-form');
  const previewContent = document.getElementById('preview-content');
  if (pressForm && previewContent) {
    pressForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const formData = new FormData(pressForm);
      selectedFiles.forEach(file => formData.append('files', file));

      previewContent.textContent = '⏳ GPT 생성 중...';

      try {
        const res = await fetch(`${window.location.origin}/generate-with-pdf`, {
          method: 'POST',
          body: formData,
        });
        const json = await res.json();
        previewContent.textContent = json.reply || '(생성 결과 없음)';

        selectedFiles = [];
        updateFileList();
        const ministryInput = document.getElementById('ministry-input');
        if (ministryInput) ministryInput.value = '';
        const buttons = document.querySelectorAll('.ministry-btn');
        buttons.forEach(b => b.classList.remove('!bg-blue-600', '!text-white', '!border-blue-600', 'ring-2', 'ring-blue-400'));
      } catch (err) {
        previewContent.textContent = '❌ 오류가 발생했습니다.';
        console.error("❌ fetch 오류:", err);
      }
    });
    updateFileList();
  }
});

// ✅ TXT로 내보내기
const exportTxtBtn = document.getElementById('export-txt');
if (exportTxtBtn) {
  exportTxtBtn.addEventListener('click', function () {
    const content = document.getElementById('preview-content')?.innerText ||
      document.getElementById('speech-preview')?.innerText || '';
    const blob = new Blob([content], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = '생성결과.txt';
    link.click();
    URL.revokeObjectURL(link.href);
  });
}

// ✅ Word(doc)로 내보내기
const exportDocxBtn = document.getElementById('export-docx');
if (exportDocxBtn) {
  exportDocxBtn.addEventListener('click', function () {
    const content = document.getElementById('preview-content')?.innerText ||
      document.getElementById('speech-preview')?.innerText || '';
    const html =
      `<html xmlns:o='urn:schemas-microsoft-com:office:office' 
             xmlns:w='urn:schemas-microsoft-com:office:word' 
             xmlns='http://www.w3.org/TR/REC-html40'>
        <head><meta charset='utf-8'></head>
        <body>${content.replace(/\n/g, "<br>")}</body>
      </html>`;
    const blob = new Blob([html], { type: 'application/msword' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = '생성결과.doc';
    link.click();
    URL.revokeObjectURL(link.href);
  });
}
