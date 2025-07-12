document.addEventListener('DOMContentLoaded', function () {
  const congratsForm = document.getElementById('congrats-form');
  const congratsPreview = document.getElementById('congrats-preview');

  // 청중 기타 입력 필드 토글
  const audienceSelect = document.getElementById('audience-select');
  const audienceEtcInput = document.getElementById('audience-etc-input');
  audienceSelect.addEventListener('change', function () {
    audienceEtcInput.classList.toggle('hidden', this.value !== '기타');
  });

  // 문체 기타 입력 필드 토글
  const styleSelect = document.getElementById('style-select');
  const styleEtcInput = document.getElementById('style-etc-input');
  styleSelect.addEventListener('change', function () {
    styleEtcInput.classList.toggle('hidden', this.value !== '기타');
  });

  // 분량 기타 입력 필드 토글
  const lengthSelect = document.getElementById('length-select');
  const lengthEtcInput = document.getElementById('length-etc-input');
  lengthSelect.addEventListener('change', function () {
    lengthEtcInput.classList.toggle('hidden', this.value !== '기타');
  });

  // 축사 생성 요청
  if (congratsForm && congratsPreview) {
    congratsForm.addEventListener('submit', async function (e) {
      e.preventDefault();

      congratsPreview.classList.remove('hidden');
      congratsPreview.textContent = '⏳ GPT 축사 생성 중입니다...';

      const formData = new FormData(congratsForm);

      try {
        const res = await fetch('https://3a400c992d08.ngrok-free.app/generate-congrats', {
          method: 'POST',
          body: formData,
        });

        const json = await res.json();
        congratsPreview.textContent = json.result || '⚠️ 생성된 축사가 없습니다.';
      } catch (err) {
        console.error("❌ 축사 생성 오류:", err);
        congratsPreview.textContent = '❌ 오류가 발생했습니다. 다시 시도해주세요.';
      }
    });
  }
});
