# Web UI Guide - LLM Prompt Quality Analyzer

## 🚀 Quick Start

### Installation

```bash
# Install core dependencies
pip install -r requirements.txt

# Install web UI dependencies
pip install -r requirements-web.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Running the Web UI

```bash
# Navigate to web directory
cd web

# Start the Flask server
python app.py
```

The server will start at **http://localhost:5000**

Open your browser and navigate to that URL!

---

## 📖 Features

### **1. Prompt Input**
- **System Prompt** (Mandatory): The instructions for your AI
- **User Prompt** (Optional): Sample user input to test against
- **Character counters**: Real-time character count

### **2. Artifact Upload**
- Drag & drop or click to upload
- Supported formats: PDF, TXT, MD, JSON, CSV, JPG, PNG, GIF
- Max file size: 16MB
- Files validated for existence and referenced in prompts

### **3. Analysis Modes**

#### **Tier 1 Only** (Recommended, FREE)
- ⚡ Fast (300-800ms)
- 🎯 Structured results
- 🔄 Deterministic
- Detects: Contradictions, verbosity, missing parameters, artifact issues

#### **Tier 1 + Tier 2** (LLM Deep Analysis, ~$0.0006)
- 🧠 Semantic understanding
- 🛡️ Safety risk detection
- 🔒 Security threat identification
- 💬 Natural language explanations
- Requires: Gemini API key in `.env` file

### **4. Results Display**

**Overall Score Card:**
- Score out of 10
- Quality rating (EXCELLENT, GOOD, FAIR, POOR, CRITICAL)
- Visual progress bar
- Fulfillability status

**Component Scores:**
- Alignment
- Consistency
- Verbosity
- Completeness

**Issues List:**
- Severity-coded (Critical, High, Moderate, Low)
- Detailed descriptions
- Actionable recommendations
- Confidence scores

**Tier 2 Results** (if LLM enabled):
- Semantic impossibility analysis
- Primary risk type (Safety, Security, Semantic, None)
- Cost tracking (tokens and $)

### **5. Export**
- Download results as JSON
- Includes all analysis data
- Timestamp in filename

---

## 🎨 UI Features

### **Real-time Validation**
- Character count updates as you type
- Minimum length warnings
- Form validation before submission

### **File Management**
- Upload progress indicators
- File size display
- One-click removal

### **Responsive Design**
- Works on desktop, tablet, mobile
- Clean, modern interface
- Intuitive layout

### **Visual Feedback**
- Loading states during analysis
- Color-coded severity levels
- Animated score bars
- Icon-based navigation

---

## 🔧 API Endpoints

The Flask backend exposes these REST APIs:

### **GET /api/health**
Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "message": "LLM Prompt Analyzer API is running"
}
```

### **POST /api/analyze**
Analyze prompt quality

**Request:**
```json
{
  "system_prompt": "...",
  "user_prompt": "...",  // optional
  "artifacts": {"name": "file_id"},  // optional
  "use_llm": true,  // optional
  "verbose": false  // optional
}
```

**Response:**
```json
{
  "tier1": {
    "overall_score": 8.5,
    "quality_rating": "good",
    "is_fulfillable": true,
    "scores": { ... },
    "issues": { ... }
  },
  "tier2": {  // if use_llm=true
    "semantic_impossibility": { ... },
    "cost": { ... }
  }
}
```

### **POST /api/upload**
Upload artifact file

**Request:** multipart/form-data with `file` field

**Response:**
```json
{
  "file_id": "abc123_document.pdf",
  "filename": "document.pdf",
  "size": 12345
}
```

### **DELETE /api/delete-upload/<file_id>**
Delete uploaded file

**Response:**
```json
{
  "message": "File deleted"
}
```

---

## 🛠️ Customization

### **Port Configuration**
Edit `web/app.py`:
```python
app.run(debug=True, host='127.0.0.1', port=5000)  # Change port here
```

### **File Upload Limits**
Edit `web/app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

### **Allowed File Types**
Edit `web/app.py`:
```python
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'json', 'csv', 'jpg', 'jpeg', 'png', 'gif'}
```

---

## 🐛 Troubleshooting

### **Server won't start**
```bash
# Check if port 5000 is already in use
netstat -an | findstr :5000

# Kill existing process
taskkill /F /PID <pid>
```

### **LLM analysis fails**
- Check `.env` file exists with valid `GEMINI_API_KEY`
- Ensure `google-generativeai` package is installed
- Check internet connection

### **File upload fails**
- Check file size (max 16MB)
- Verify file extension is allowed
- Check `web/uploads/` directory exists and is writable

---

## 📊 Performance

### **Tier 1 Analysis**
- Average time: 300-800ms
- Memory usage: ~200MB
- CPU usage: Low-moderate

### **Tier 2 Analysis**
- Average time: 5-25 seconds (LLM call)
- Cost: ~$0.0006 per analysis
- Requires internet connection

---

## 🔒 Security

### **Local Only**
- Server binds to `127.0.0.1` (localhost only)
- No external access by default
- Files stored in local `uploads/` directory

### **File Validation**
- Extension whitelist
- Secure filename sanitization
- Size limits enforced

### **API Key Protection**
- `.env` file in `.gitignore`
- Never exposed to client
- Server-side only

---

## 📦 Project Structure

```
web/
├── app.py                 # Flask backend
├── templates/
│   └── index.html        # Main UI template
├── static/
│   └── js/
│       └── app.js        # Frontend JavaScript
└── uploads/              # Temporary file storage
```

---

## 🚀 Production Deployment

### **Not Recommended for Production**
This Web UI is designed for local development and testing. For production:

1. **Use HTTPS**: Add SSL certificates
2. **Authentication**: Add user authentication
3. **Rate Limiting**: Prevent abuse
4. **WSGI Server**: Use Gunicorn instead of Flask dev server
5. **Database**: Store analysis history
6. **Caching**: Add Redis for performance

---

## 🤝 Contributing

To add new features:

1. **Backend**: Edit `web/app.py` (Flask routes)
2. **Frontend**: Edit `web/templates/index.html` (UI)
3. **JavaScript**: Edit `web/static/js/app.js` (logic)

---

## 📄 License

Same as main project - see repository LICENSE file.

---

## 🆘 Support

- GitHub Issues: https://github.com/Shiva-Subramaniam-NR/llm_prompt_analyzer/issues
- Documentation: README.md in root directory
