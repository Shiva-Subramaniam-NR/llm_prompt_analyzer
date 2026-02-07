"""
Flask Backend for LLM Prompt Quality Analyzer Web UI
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add parent directory to path to import analyzer
sys.path.insert(0, str(Path(__file__).parent.parent))

from v2.prompt_quality_analyzer import PromptQualityAnalyzer
from v2.llm_analyzer import LLMAnalyzer

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'json', 'csv', 'jpg', 'jpeg', 'png', 'gif'}

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global analyzer instance (initialized once to avoid reloading embeddings)
print("Initializing analyzers (this may take ~30 seconds on first run)...")
global_analyzer = PromptQualityAnalyzer(verbose=False)
global_llm_analyzer = None  # Initialize lazily when needed
print("Analyzers ready!")


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'LLM Prompt Analyzer API is running'
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_prompt():
    """
    Analyze prompt quality

    Expected JSON:
    {
        "system_prompt": "...",
        "user_prompt": "...",  // optional
        "artifacts": {"name": "file_id", ...},  // optional
        "use_llm": true/false,  // optional
        "verbose": true/false  // optional
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        system_prompt = data.get('system_prompt', '').strip()
        if not system_prompt:
            return jsonify({'error': 'System prompt is required'}), 400

        user_prompt = data.get('user_prompt', '').strip() or None
        use_llm = data.get('use_llm', False)
        verbose = data.get('verbose', False)

        # Handle artifacts
        artifacts = {}
        artifact_files = data.get('artifacts', {})
        if artifact_files:
            for name, file_id in artifact_files.items():
                file_path = UPLOAD_FOLDER / file_id
                if file_path.exists():
                    artifacts[name] = str(file_path)

        # Use global analyzer instance (already initialized)
        # This avoids reloading embeddings on every request
        report = global_analyzer.analyze(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            artifacts=artifacts if artifacts else None
        )

        # Prepare response
        response = {
            'tier1': {
                'overall_score': report.overall_score,
                'quality_rating': report.quality_rating.value,
                'is_fulfillable': report.is_fulfillable,
                'scores': {
                    'alignment': report.alignment_score,
                    'consistency': report.consistency_score,
                    'verbosity': report.verbosity_score,
                    'completeness': report.completeness_score
                },
                'issues': {
                    'total': report.total_issues,
                    'critical': report.critical_count,
                    'high': report.high_count,
                    'moderate': report.moderate_count,
                    'low': report.low_count,
                    'details': [
                        {
                            'category': issue.category,
                            'severity': issue.severity,
                            'title': issue.title,
                            'description': issue.description,
                            'recommendation': issue.recommendation,
                            'confidence': issue.confidence
                        }
                        for issue in report.all_issues
                    ]
                }
            }
        }

        # Run Tier 2 LLM analysis if requested
        if use_llm and user_prompt:
            try:
                # Initialize LLM analyzer lazily (only when needed)
                global global_llm_analyzer
                if global_llm_analyzer is None:
                    global_llm_analyzer = LLMAnalyzer(verbose=verbose)
                llm_analyzer = global_llm_analyzer

                # Semantic impossibility detection
                tier1_issues = [
                    {
                        'category': issue.category,
                        'severity': issue.severity,
                        'title': issue.title,
                        'description': issue.description,
                        'confidence': issue.confidence
                    }
                    for issue in report.all_issues
                ]

                impossibility_result = llm_analyzer.analyze_semantic_impossibility(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    tier1_issues=tier1_issues
                )

                response['tier2'] = {
                    'semantic_impossibility': {
                        'is_impossible': impossibility_result.is_impossible,
                        'score': impossibility_result.impossibility_score,
                        'primary_risk_type': impossibility_result.primary_risk_type,
                        'explanation': impossibility_result.explanation,
                        'recommendation': impossibility_result.recommendation,
                        'confidence': impossibility_result.confidence
                    },
                    'cost': {
                        'input_tokens': llm_analyzer.cost_tracker.total_input_tokens,
                        'output_tokens': llm_analyzer.cost_tracker.total_output_tokens,
                        'total_cost': llm_analyzer.cost_tracker.get_session_cost()
                    }
                }

            except Exception as e:
                response['tier2'] = {
                    'error': str(e),
                    'message': 'LLM analysis failed. Tier 1 results are still available.'
                }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'error': 'Analysis failed',
            'details': str(e)
        }), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload artifact file

    Returns: {"file_id": "...", "filename": "...", "size": ...}
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Generate unique file ID
            import uuid
            file_id = f"{uuid.uuid4().hex}_{filename}"
            file_path = UPLOAD_FOLDER / file_id

            file.save(str(file_path))

            return jsonify({
                'file_id': file_id,
                'filename': filename,
                'size': file_path.stat().st_size
            })

        return jsonify({'error': 'File type not allowed'}), 400

    except Exception as e:
        return jsonify({
            'error': 'Upload failed',
            'details': str(e)
        }), 500


@app.route('/api/delete-upload/<file_id>', methods=['DELETE'])
def delete_upload(file_id):
    """Delete uploaded artifact file"""
    try:
        file_path = UPLOAD_FOLDER / file_id
        if file_path.exists():
            file_path.unlink()
            return jsonify({'message': 'File deleted'})
        return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        return jsonify({
            'error': 'Delete failed',
            'details': str(e)
        }), 500


if __name__ == '__main__':
    print("="*60)
    print("LLM Prompt Quality Analyzer - Web UI")
    print("="*60)
    print("\nServer starting at: http://localhost:5000")
    print("\nFeatures available:")
    print("  - Tier 1: Fast, free prompt analysis")
    print("  - Tier 2: Optional LLM deep analysis")
    print("  - Artifact upload support")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
