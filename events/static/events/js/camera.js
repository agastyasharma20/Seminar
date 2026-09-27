(() => {
  const form = document.querySelector('#scanForm');
  const start = document.querySelector('#startCamera');
  const video = document.querySelector('#cameraPreview');
  const canvas = document.querySelector('#captureCanvas');
  const input = document.querySelector('#cardInput');
  const status = document.querySelector('#cameraStatus');
  if (!form || !start || !video || !canvas || !input || !status || !navigator.mediaDevices) return;

  let stream;
  let captureTimer;
  const stopCamera = () => {
    if (captureTimer) window.clearTimeout(captureTimer);
    if (stream) stream.getTracks().forEach((track) => track.stop());
    stream = undefined;
  };
  const capture = () => {
    if (!video.videoWidth || !video.videoHeight) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const transfer = new DataTransfer();
      transfer.items.add(new File([blob], `cardiq-camera-${Date.now()}.jpg`, { type: 'image/jpeg' }));
      input.files = transfer.files;
      status.textContent = 'Card captured. Starting secure processing...';
      stopCamera();
      form.requestSubmit();
    }, 'image/jpeg', 0.92);
  };
  start.addEventListener('click', async () => {
    try {
      status.textContent = 'Requesting camera permission...';
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
      video.srcObject = stream;
      video.classList.add('ready');
      start.disabled = true;
      start.textContent = 'Scanning automatically...';
      status.textContent = 'Frame the business card inside the guide.';
      captureTimer = window.setTimeout(capture, 2500);
    } catch (error) {
      status.textContent = 'Camera unavailable. Upload a photo instead.';
    }
  });
  window.addEventListener('beforeunload', stopCamera);
})();
