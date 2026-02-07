# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### 1. "Analysis failed: Failed to fetch" Error

**Symptom:** Web UI shows popup "Analysis failed: Failed to fetch"

**Root Cause:** Flask server not running or taking too long to respond

**Solution:**
```bash
# 1. Make sure server is running
cd web
python app.py

# 2. Wait for "Analyzers ready!" message (30-35 seconds on first run)

# 3. Verify server is responding
curl http://localhost:5000/api/health
# Should return: {"status": "ok", ...}

# 4. Now open browser to http://localhost:5000
```

**Fixed in latest version!** Server now pre-loads models at startup.

---

### 2. Server Takes Forever to Start

**Symptom:** Flask shows "Initializing analyzers..." but hangs

**Root Cause:** Downloading sentence-transformers model from Hugging Face

**Solution:**
```bash
# Pre-download the model
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model downloaded!')
"

# Now start Flask
cd web
python app.py
```

**Storage:** Model is cached in `~/.cache/huggingface/` (~100MB)

---

### 3. ModuleNotFoundError: No module named 'v2'

**Symptom:**
```
ModuleNotFoundError: No module named 'v2'
```

**Root Cause:** Running Flask from wrong directory or Python path issue

**Solution:**
```bash
# Always run from the web/ directory
cd web
python app.py

# NOT from root:
# cd Ai_Eval  # ❌ WRONG
# python web/app.py  # ❌ WRONG
```

**Why:** `app.py` adds parent directory to `sys.path`, but only works when run from `web/`

---

### 4. Port 5000 Already in Use

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Root Cause:** Another Flask instance or app using port 5000

**Solution:**
```bash
# Option 1: Kill existing process (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Option 1: Kill existing process (Mac/Linux)
lsof -ti:5000 | xargs kill -9

# Option 2: Change port in app.py
# Line 255: app.run(..., port=5001)
```

---

### 5. Tier 2 LLM Analysis Not Working

**Symptom:** Selecting "Tier 1 + Tier 2" mode shows error

**Root Cause:** Missing Gemini API key

**Solution:**
```bash
# 1. Get free API key from https://aistudio.google.com/app/apikey

# 2. Copy .env.example to .env
cp .env.example .env

# 3. Edit .env and add your key
# GEMINI_API_KEY=your_actual_key_here

# 4. Restart Flask
cd web
python app.py
```

**Test Tier 2:**
```python
import os
os.environ['GEMINI_API_KEY'] = 'your_key'

from v2.llm_analyzer import LLMAnalyzer
analyzer = LLMAnalyzer()
result = analyzer.analyze_semantic_impossibility(
    "You are helpful",
    "Tell me a joke",
    []
)
print(result.is_impossible)  # Should be False
```

---

### 6. CORS Errors in Browser Console

**Symptom:** Browser console shows "CORS policy blocked"

**Root Cause:** Running HTML file directly instead of through Flask

**Solution:**
```bash
# ❌ WRONG: file:///path/to/index.html
# ✅ CORRECT: http://localhost:5000

# Always access through Flask server
cd web
python app.py
# Then open: http://localhost:5000
```

---

### 7. Uploads Not Working

**Symptom:** File upload fails or "Upload failed" error

**Root Cause:** Missing uploads directory or file too large

**Solution:**
```bash
# 1. Ensure uploads directory exists
mkdir -p web/uploads

# 2. Check file size (max 16MB)
# Large files will be rejected

# 3. Check file type
# Allowed: .pdf, .txt, .md, .json, .csv, .jpg, .png, .gif

# 4. Check server logs
cat web/server_new.log
```

---

### 8. Slow Performance After First Request

**Symptom:** First request fast, but subsequent requests slow

**Root Cause:** Debug mode or old code without global analyzer

**Solution:**
```bash
# Ensure you have latest code with global analyzer
grep "global_analyzer = PromptQualityAnalyzer" web/app.py

# Should see:
# global_analyzer = PromptQualityAnalyzer(verbose=False)

# Also ensure debug=False
grep "app.run" web/app.py
# Should see: app.run(debug=False, ...)
```

---

### 9. Missing Dependencies

**Symptom:**
```
ModuleNotFoundError: No module named 'flask'
ModuleNotFoundError: No module named 'sentence_transformers'
```

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-web.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Verify installation
python -c "import flask, sentence_transformers, spacy; print('All good!')"
```

---

### 10. Server Keeps Restarting

**Symptom:** Flask logs show multiple "Restarting with watchdog" messages

**Root Cause:** Debug mode auto-reload detecting file changes

**Solution:**
```bash
# Edit web/app.py line 255
# Change: app.run(debug=True, ...)
# To:     app.run(debug=False, use_reloader=False, ...)

# Then restart server
cd web
python app.py
```

---

## 🆘 Still Having Issues?

### Check Server Logs
```bash
cat web/server_new.log
# or
tail -f web/server_new.log  # Follow logs in real-time
```

### Test API Directly
```bash
# Health check
curl http://localhost:5000/api/health

# Simple analysis
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "Test", "use_llm": false}'
```

### Check Python Version
```bash
python --version
# Requires: Python 3.8+
```

### Check Dependencies
```bash
pip list | grep -E "(flask|sentence|spacy|torch)"
```

### Fresh Install
```bash
# Create new virtual environment
python -m venv fresh_venv
source fresh_venv/bin/activate  # Mac/Linux
# or
fresh_venv\Scripts\activate  # Windows

# Install from scratch
pip install -r requirements.txt requirements-web.txt
python -m spacy download en_core_web_sm

# Test
cd web && python app.py
```

---

## 📞 Contact

If none of these solutions work:
1. Check GitHub Issues: https://github.com/Shiva-Subramaniam-NR/llm_prompt_analyzer/issues
2. Create new issue with:
   - Error message
   - Server logs
   - Python version
   - Operating system
