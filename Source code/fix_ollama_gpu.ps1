# =====================================================================
#  fix_ollama_gpu.ps1 — paksa Ollama memakai GPU NVIDIA (RTX 4050)
#
#  Ollama 0.30.x di laptop hybrid (AMD iGPU + NVIDIA dGPU) kadang gagal
#  mendeteksi GPU NVIDIA setelah restart/reboot -> model jalan 100% CPU ->
#  generasi lambat -> timeout -> HTTP 500 di chatbot.
#
#  Jalankan skrip ini kapan saja chat terasa lambat / kena 500.
#  Cek hasil: 'ollama ps' harus menampilkan GPU (mis. 18%/82% CPU/GPU),
#  bukan '100% CPU'.
# =====================================================================

Write-Host "1) Membangunkan GPU NVIDIA (nvidia-smi)..." -ForegroundColor Cyan
try { nvidia-smi --query-gpu=name,memory.free --format=csv,noheader } catch {}

Write-Host "2) Menghentikan semua proses Ollama..." -ForegroundColor Cyan
Get-Process ollama* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "3) Mengaktifkan runner CUDA + menjalankan ulang Ollama..." -ForegroundColor Cyan
$env:OLLAMA_LLM_LIBRARY = "cuda_v12"   # paksa runner CUDA
# permanenkan untuk proses mendatang (sekali set sudah cukup, aman diulang)
setx OLLAMA_LLM_LIBRARY cuda_v12 | Out-Null

# jalankan serve di jendela terpisah supaya tetap hidup
Start-Process powershell -ArgumentList @(
  "-NoExit","-Command",
  "`$env:OLLAMA_LLM_LIBRARY='cuda_v12'; Write-Host 'Ollama serve (GPU) - biarkan jendela ini terbuka' -ForegroundColor Green; ollama serve"
)

Start-Sleep -Seconds 6
Write-Host "4) Memuat qwen ke GPU & verifikasi..." -ForegroundColor Cyan
try {
  Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -TimeoutSec 90 -Body (@{
    model = "qwen2.5:7b-instruct"; prompt = "hi"; stream = $false
    options = @{ num_ctx = 4096; num_predict = 5 }
  } | ConvertTo-Json) -ContentType "application/json" | Out-Null
} catch { Write-Host "  (warm-up gagal, lanjut cek status)" -ForegroundColor Yellow }

Write-Host "`n=== STATUS (PROCESSOR harus ada GPU) ===" -ForegroundColor Green
ollama ps
Write-Host "`nJika masih '100% CPU': coba reboot laptop, lalu jalankan skrip ini lagi." -ForegroundColor Yellow
