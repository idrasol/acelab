document.addEventListener('DOMContentLoaded', function () {
  // ========== 4. 인사말씀 제출 처리 ==========
  const speechForm = document.getElementById('speech-form');
  const speechPreview = document.getElementById('speech-preview');

  if (speechForm && speechPreview) {
    speechForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      speechPreview.textContent = '⏳ GPT 인사말씀 생성 중입니다...';

      const formData = new FormData(speechForm);

      try {
        const res = await fetch('/generate-greeting', {
          method: 'POST',
          body: formData,
        });

        const json = await res.json();
        speechPreview.textContent = json.result || '⚠️ 생성된 인사말이 없습니다.';
      } catch (err) {
        console.error("❌ 오류 발생:", err);
        speechPreview.textContent = '❌ 오류가 발생했습니다. 다시 시도해주세요.';
      }
    });
  }
});
