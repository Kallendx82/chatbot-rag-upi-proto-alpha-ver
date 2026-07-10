# =====================================================================
#  run_knowledge_layer.ps1  —  reliable launcher for the UPI knowledge layer
#
#  Use this instead of the VS Code Run button (the Run button passes NO
#  arguments, so it would only make ~160 questions and could overwrite your
#  current dataset).
#
#  HOW TO RUN:
#    In a PowerShell terminal, from anywhere:
#        D:\Project\RAG_UPI\run_knowledge_layer.ps1
#    or right-click the file -> "Run with PowerShell".
#
#  EDIT $Target BELOW to choose how many questions you want.
#  Make sure Ollama is running first:  ollama serve
# =====================================================================

# --- settings you can edit -------------------------------------------
$Python  = "C:\Users\Rajih Nibras M\AppData\Local\Programs\Python\Python312\python.exe"
$Script  = "D:\Project\RAG_UPI\knowledge_layer_builder.py"
$Target  = 1600        # grow the existing dataset up to this many questions
$Topics  = 200         # must match the original run that built your dataset
$PerTopic = 8
# ---------------------------------------------------------------------

Write-Host "Launching knowledge-layer top-up -> target $Target questions" -ForegroundColor Cyan
Write-Host "(uses your existing dataset; only generates what's missing)`n" -ForegroundColor DarkGray

& $Python $Script --topics $Topics --questions-per-topic $PerTopic --target $Target

Write-Host "`nDone. Output in D:\Project\RAG_UPI\knowledge_layer" -ForegroundColor Green
