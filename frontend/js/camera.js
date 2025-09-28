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




// Variabel untuk kontrol update
let lastUpdateTime = 0;
const updateInterval = 300; // Update setiap 500ms

// Fungsi untuk mendapatkan warna saat ini
async function getCurrentColor() {
    try {
        const response = await fetch('/get_color');
        const data = await response.json();
        document.querySelector('.color-indicator').textContent = data.color;
    } catch (error) {
        console.error('Error getting color:', error);
    }
}

// Fungsi untuk update color dengan throttling
function updateColorWithThrottle() {
    const currentTime = Date.now();
    if (currentTime - lastUpdateTime >= updateInterval) {
        getCurrentColor();
        lastUpdateTime = currentTime;
    }
}

// Gunakan Intersection Observer untuk hanya update ketika tab visible
let isTabVisible = true;

document.addEventListener('visibilitychange', () => {
    isTabVisible = !document.hidden;
});

// Update color secara periodic, tetapi hanya jika tab visible
setInterval(() => {
    if (isTabVisible) {
        updateColorWithThrottle();
    }
}, 100);



