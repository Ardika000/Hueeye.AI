// async function initCamera() {
//     try {
//         const video = document.getElementById('camera-feed');
//         const stream = await navigator.mediaDevices.getUserMedia({ 
//             video: { 
//                 facingMode: 'environment',
//                 width: { ideal: 1280 },
//                 height: { ideal: 720 }
//             } 
//         });
//         video.srcObject = stream;
//     } catch (err) {
//         console.error('Error accessing camera:', err);
//         alert('Could not access camera. Please ensure camera permissions are granted.');
//     }
// }

// document.addEventListener('DOMContentLoaded', initCamera);


// async function initCamera() {
//     try {
//         const video = document.getElementById('camera-feed');
//         // Gunakan video feed dari Flask
//         video.src = "/video_feed";
//     } catch (err) {
//         console.error('Error accessing camera:', err);
//         alert('Could not access camera. Please ensure camera permissions are granted.');
//     }
// }

// // Fungsi untuk mendapatkan warna saat ini
// async function getCurrentColor() {
//     try {
//         const response = await fetch('/get_color');
//         const data = await response.json();
//         document.querySelector('.color-indicator').textContent = data.color;
//     } catch (error) {
//         console.error('Error getting color:', error);
//     }
// }

// // Panggil getCurrentColor secara berkala
// setInterval(getCurrentColor, 1000); // Update setiap detik

// document.addEventListener('DOMContentLoaded', initCamera);




const video = document.getElementById('camera');
const canvas = document.getElementById('canvas');
const colorDisplay = document.getElementById('color-display');

if (!canvas) {
  console.error("Canvas element tidak ditemukan di DOM!");
}

const ctx = canvas ? canvas.getContext('2d') : null;

// Aktifkan kamera browser
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
  })
  .catch(err => {
    console.error("Error accessing camera:", err);
    colorDisplay.textContent = "KAMERA TIDAK TERSEDIA";
  });

// Kirim snapshot ke server
async function sendFrame() {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  if (!ctx) return;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  
  const dataURL = canvas.toDataURL('image/jpeg');
  
  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataURL })
    });
    
    const result = await res.json();
    colorDisplay.textContent = result.color || "ERROR";
  } catch (err) {
    console.error("Error:", err);
  }
}

// Loop prediksi tiap 500ms
setInterval(sendFrame, 500);




