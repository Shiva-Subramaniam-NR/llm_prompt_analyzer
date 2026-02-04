# Cleanup Plan for Ai_Eval Folder

## 🗑️ Files/Folders to DELETE (Obsolete/Redundant)

### 1. **Obsolete Test Files** (superseded by v2 tests)
- ❌ `test_alignment_checker.py` - Old unit test (v2 has integrated tests)
- ❌ `test_contradiction_detector.py` - Old unit test (v2 has integrated tests)
- ❌ `test_system_prompt_parser.py` - Old unit test (v2 has integrated tests)
- ❌ `test_verbosity_analyzer.py` - Old unit test (v2 has integrated tests)
- ❌ `test_case_1.py` - Obsolete, replaced by `test_case_1_with_artifacts.py`
- ❌ `test_case_2.py` - Obsolete, replaced by `test_llm_analyzer.py`

### 2. **Obsolete Configuration**
- ❌ `config/` directory - Old v1 config, v2 uses `v2/config/`
- ❌ `design/` directory - Design docs not needed in production

### 3. **Phase Documentation** (keep final status only)
- ❌ `PHASE_1_COMPLETE.md` - Superseded by PROJECT_STATUS.md
- ❌ `PHASE_2_DESIGN.md` - Superseded by PROJECT_STATUS.md

### 4. **Miscellaneous**
- ❌ `claudecode_instr.txt` - Temporary instruction file
- ❌ `nul` - Empty junk file
- ❌ `__pycache__/` - Compiled Python cache (root level)

---

## ✅ Files/Folders to KEEP (Active/Production)

### Core Application
- ✅ `v2/` - Main application code (Tier 1 + Tier 2)
- ✅ `web/` - Web UI (Flask + HTML/CSS/JS)

### Entry Points
- ✅ `run_analyzer.py` - CLI entry point
- ✅ `interactive_analyzer.py` - Interactive CLI

### Tests (Keep Relevant Ones)
- ✅ `test_prompt_quality_analyzer.py` - Main orchestrator test
- ✅ `test_case_1_with_artifacts.py` - Artifact support test
- ✅ `test_llm_analyzer.py` - Tier 2 LLM test
- ✅ `test_web_api.py` - Web UI API test

### Documentation
- ✅ `README.md` - Main documentation
- ✅ `USER_GUIDE.md` - User manual
- ✅ `WEB_UI_GUIDE.md` - Web UI documentation
- ✅ `PROJECT_STATUS.md` - Current status
- ✅ `CLAUDE.md` - Project instructions for Claude Code

### Configuration
- ✅ `.env` - API keys (gitignored)
- ✅ `.env.example` - Template for API keys
- ✅ `.gitignore` - Git ignore rules
- ✅ `requirements.txt` - Core dependencies
- ✅ `requirements-web.txt` - Web UI dependencies

### Directories
- ✅ `.git/` - Git repository
- ✅ `.venv/` - Virtual environment
- ✅ `.claude/` - Claude Code settings
- ✅ `outputs/` - Analysis results

---

## 📊 Cleanup Summary

**Files to delete:** 13 files + 3 directories
**Files to keep:** 17 files + 5 directories
**Estimated space saved:** ~250 KB (mostly obsolete test files)

---

## 🚀 Execution Plan

### Option A: Safe Cleanup (Recommended)
Create a backup folder before deletion:
```bash
mkdir cleanup_backup
cp test_alignment_checker.py cleanup_backup/
cp test_contradiction_detector.py cleanup_backup/
# ... (copy all files to be deleted)
```

### Option B: Direct Cleanup (If confident)
```bash
# Delete obsolete test files
rm test_alignment_checker.py test_contradiction_detector.py test_system_prompt_parser.py test_verbosity_analyzer.py test_case_1.py test_case_2.py

# Delete obsolete docs
rm PHASE_1_COMPLETE.md PHASE_2_DESIGN.md

# Delete obsolete config/design
rm -rf config/ design/

# Delete junk files
rm claudecode_instr.txt nul

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

---

## ✨ After Cleanup

The folder structure will be clean and production-ready:

```
Ai_Eval/
├── v2/                          # Core application
├── web/                         # Web UI
├── run_analyzer.py              # CLI entry
├── interactive_analyzer.py      # Interactive CLI
├── test_*.py                    # Relevant tests (4 files)
├── README.md                    # Main docs
├── USER_GUIDE.md                # User manual
├── WEB_UI_GUIDE.md              # Web UI docs
├── PROJECT_STATUS.md            # Status
├── CLAUDE.md                    # Project instructions
├── requirements*.txt            # Dependencies
├── .env, .env.example           # Configuration
└── outputs/                     # Results
```

**Ready to proceed?** Choose Option A (safe) or Option B (direct).
