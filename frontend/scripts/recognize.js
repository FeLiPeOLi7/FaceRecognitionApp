document.addEventListener('DOMContentLoaded', () => {
  const socket = io();
  const video = document.getElementById('video');
  const canvas = document.getElementById('canvas');
  const processed = document.getElementById('processed');
  const status = document.getElementById('status');
  const startBtn = document.getElementById('start');
  const stopBtn = document.getElementById('stop');
  let stream = null;
  let timerId = null;
  let frameInFlight = false;
  const fps = 5;
  const intervalMs = Math.max(1000 / fps, 120);

  function setStatus(text) {
    if (status) {
      status.textContent = text;
    }
  }

  function stopCapture() {
    if (timerId) clearInterval(timerId);
    timerId = null;
    frameInFlight = false;

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }

    setStatus('Parado');
  }

  async function startCapture() {
    if (stream) return;

    setStatus('Iniciando câmera...');
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720, facingMode: 'user' },
      audio: false,
    });

    video.srcObject = stream;
    canvas.width = 1280;
    canvas.height = 720;
    const ctx = canvas.getContext('2d');
    setStatus(`Capturando a ${fps} fps`);

    timerId = setInterval(() => {
      if (!stream || frameInFlight || video.readyState < 2) return;

      frameInFlight = true;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (!blob) {
          frameInFlight = false;
          return;
        }
          const reader = new FileReader();
          reader.onloadend = () => {
            const result = String(reader.result || '');
            const base64 = result.includes(',') ? result.split(',')[1] : '';
            socket.emit('frame', { image_b64: base64 });
            frameInFlight = false;
          };

          reader.readAsDataURL(blob);
          }, 'image/jpeg', 0.85);
    }, intervalMs);
  }

  startBtn.addEventListener('click', () => {
    startCapture().catch((err) => {
      console.error(err);
      setStatus('Erro ao iniciar câmera');
      stopCapture();
    });
  });

  stopBtn.addEventListener('click', () => stopCapture());

  socket.on('processed', (data) => {
    const blob = new Blob([data], { type: 'image/jpeg' });
    processed.src = URL.createObjectURL(blob);
  });

  socket.on('connect_error', (err) => {
    console.error('Socket.IO connection error:', err);
    setStatus('Erro no Socket.IO');
  });

  window.startCapture = startCapture;
  window.stopCapture = stopCapture;
});
