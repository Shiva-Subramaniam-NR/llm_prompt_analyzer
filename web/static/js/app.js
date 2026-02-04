/**
 * LLM Prompt Quality Analyzer - Frontend JavaScript
 */

// Global state
const state = {
    uploadedFiles: {},
    lastAnalysisResult: null
};

// DOM Elements
const elements = {
    systemPrompt: document.getElementById('systemPrompt'),
    userPrompt: document.getElementById('userPrompt'),
    systemCharCount: document.getElementById('systemCharCount'),
    userCharCount: document.getElementById('userCharCount'),
    fileInput: document.getElementById('fileInput'),
    uploadArea: document.getElementById('uploadArea'),
    uploadedFiles: document.getElementById('uploadedFiles'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    clearBtn: document.getElementById('clearBtn'),
    exportBtn: document.getElementById('exportBtn'),
    resultsSection: document.getElementById('resultsSection'),
    loadingState: document.getElementById('loadingState'),
    resultsDisplay: document.getElementById('resultsDisplay')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    updateCharCounts();
});

function setupEventListeners() {
    // Character counters
    elements.systemPrompt.addEventListener('input', updateCharCounts);
    elements.userPrompt.addEventListener('input', updateCharCounts);

    // File upload
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    elements.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.add('border-blue-400', 'bg-blue-50');
    });

    elements.uploadArea.addEventListener('dragleave', () => {
        elements.uploadArea.classList.remove('border-blue-400', 'bg-blue-50');
    });

    elements.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.remove('border-blue-400', 'bg-blue-50');
        handleFileSelect({ target: { files: e.dataTransfer.files } });
    });

    // Buttons
    elements.analyzeBtn.addEventListener('click', analyzePrompt);
    elements.clearBtn.addEventListener('click', clearForm);
    elements.exportBtn.addEventListener('click', exportResults);
}

function updateCharCounts() {
    const systemCount = elements.systemPrompt.value.length;
    const userCount = elements.userPrompt.value.length;

    elements.systemCharCount.textContent = `${systemCount} characters`;
    elements.userCharCount.textContent = `${userCount} characters`;
}

async function handleFileSelect(event) {
    const files = Array.from(event.target.files);

    for (const file of files) {
        await uploadFile(file);
    }

    // Reset file input
    elements.fileInput.value = '';
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();

        // Store file info
        state.uploadedFiles[data.filename] = data.file_id;

        // Display file
        displayUploadedFile(data.filename, data.file_id, data.size);

    } catch (error) {
        alert(`Failed to upload ${file.name}: ${error.message}`);
    }
}

function displayUploadedFile(filename, fileId, size) {
    const fileDiv = document.createElement('div');
    fileDiv.className = 'flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg';
    fileDiv.dataset.fileId = fileId;

    const sizeKB = (size / 1024).toFixed(1);

    fileDiv.innerHTML = `
        <div class="flex items-center space-x-3">
            <i class="fas fa-file text-blue-600"></i>
            <div>
                <p class="text-sm font-medium text-gray-800">${filename}</p>
                <p class="text-xs text-gray-500">${sizeKB} KB</p>
            </div>
        </div>
        <button onclick="removeFile('${fileId}')" class="text-red-500 hover:text-red-700">
            <i class="fas fa-times"></i>
        </button>
    `;

    elements.uploadedFiles.appendChild(fileDiv);
}

async function removeFile(fileId) {
    try {
        await fetch(`/api/delete-upload/${fileId}`, { method: 'DELETE' });

        // Remove from DOM
        const fileDiv = document.querySelector(`[data-file-id="${fileId}"]`);
        if (fileDiv) fileDiv.remove();

        // Remove from state
        for (const [filename, id] of Object.entries(state.uploadedFiles)) {
            if (id === fileId) {
                delete state.uploadedFiles[filename];
                break;
            }
        }
    } catch (error) {
        console.error('Failed to delete file:', error);
    }
}

async function analyzePrompt() {
    const systemPrompt = elements.systemPrompt.value.trim();

    if (!systemPrompt || systemPrompt.length < 10) {
        alert('Please enter a system prompt (minimum 10 characters)');
        return;
    }

    const userPrompt = elements.userPrompt.value.trim();
    const analysisMode = document.querySelector('input[name="analysisMode"]:checked').value;
    const useLLM = analysisMode === 'tier2';

    // Prepare request
    const requestData = {
        system_prompt: systemPrompt,
        user_prompt: userPrompt || null,
        artifacts: state.uploadedFiles,
        use_llm: useLLM,
        verbose: false
    };

    // Show loading state
    elements.resultsSection.classList.remove('hidden');
    elements.loadingState.classList.remove('hidden');
    elements.resultsDisplay.classList.add('hidden');
    elements.analyzeBtn.disabled = true;
    elements.analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...';

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) throw new Error('Analysis failed');

        const data = await response.json();
        state.lastAnalysisResult = data;

        // Display results
        displayResults(data);

        // Enable export
        elements.exportBtn.disabled = false;

    } catch (error) {
        alert(`Analysis failed: ${error.message}`);
        elements.resultsSection.classList.add('hidden');
    } finally {
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>Analyze Prompt';
    }
}

function displayResults(data) {
    const tier1 = data.tier1;

    // Hide loading, show results
    elements.loadingState.classList.add('hidden');
    elements.resultsDisplay.classList.remove('hidden');

    // Overall score
    document.getElementById('overallScore').textContent = tier1.overall_score.toFixed(1);
    document.getElementById('overallScoreBar').style.width = `${tier1.overall_score * 10}%`;

    // Quality badge
    const badge = document.getElementById('qualityBadge');
    const rating = tier1.quality_rating.toUpperCase();
    badge.textContent = rating;
    badge.className = `px-4 py-2 rounded-full text-sm font-semibold ${getQualityBadgeClass(rating)}`;

    // Fulfillable status
    const fulfillable = document.getElementById('fulfillableStatus');
    if (tier1.is_fulfillable) {
        fulfillable.innerHTML = '<i class="fas fa-check-circle text-green-500 mr-2"></i>Can fulfill request';
    } else {
        fulfillable.innerHTML = '<i class="fas fa-times-circle text-red-500 mr-2"></i>Cannot fulfill request';
    }

    // Component scores
    displayComponentScores(tier1.scores);

    // Issues
    displayIssues(tier1.issues);

    // Tier 2 results
    if (data.tier2) {
        displayTier2Results(data.tier2);
    } else {
        document.getElementById('tier2Results').classList.add('hidden');
    }
}

function displayComponentScores(scores) {
    const container = document.getElementById('componentScores');
    container.innerHTML = '';

    const components = [
        { name: 'Alignment', score: scores.alignment, icon: 'fa-sync-alt' },
        { name: 'Consistency', score: scores.consistency, icon: 'fa-check-double' },
        { name: 'Verbosity', score: scores.verbosity, icon: 'fa-text-height' },
        { name: 'Completeness', score: scores.completeness, icon: 'fa-puzzle-piece' }
    ];

    components.forEach(comp => {
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between';
        div.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas ${comp.icon} text-gray-600"></i>
                <span class="font-medium text-gray-800">${comp.name}</span>
            </div>
            <div class="flex items-center space-x-4">
                <div class="w-32 bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full ${getScoreColor(comp.score)}" style="width: ${comp.score * 10}%"></div>
                </div>
                <span class="font-semibold text-gray-800 w-12 text-right">${comp.score.toFixed(1)}</span>
            </div>
        `;
        container.appendChild(div);
    });
}

function displayIssues(issues) {
    const countSpan = document.getElementById('issuesCount');
    countSpan.textContent = `${issues.total} total (${issues.critical} critical, ${issues.high} high, ${issues.moderate} moderate, ${issues.low} low)`;

    const container = document.getElementById('issuesList');
    container.innerHTML = '';

    if (issues.total === 0) {
        container.innerHTML = '<p class="text-green-600 font-medium"><i class="fas fa-check-circle mr-2"></i>No issues found! Your prompt looks great.</p>';
        return;
    }

    issues.details.forEach(issue => {
        const div = document.createElement('div');
        div.className = `border-l-4 ${getSeverityBorderClass(issue.severity)} bg-gray-50 p-4 rounded-r-lg`;
        div.innerHTML = `
            <div class="flex items-start justify-between mb-2">
                <h4 class="font-semibold text-gray-800">
                    <span class="inline-block px-2 py-1 text-xs rounded ${getSeverityBadgeClass(issue.severity)} mr-2">
                        ${issue.severity.toUpperCase()}
                    </span>
                    ${issue.title}
                </h4>
                <span class="text-xs text-gray-500">${(issue.confidence * 100).toFixed(0)}% confidence</span>
            </div>
            <p class="text-sm text-gray-700 mb-2">${issue.description}</p>
            <div class="bg-blue-50 border-l-2 border-blue-400 p-2 text-sm text-blue-800 mt-2">
                <strong>💡 Recommendation:</strong> ${issue.recommendation}
            </div>
        `;
        container.appendChild(div);
    });
}

function displayTier2Results(tier2) {
    const container = document.getElementById('tier2Content');
    const results = document.getElementById('tier2Results');
    results.classList.remove('hidden');

    if (tier2.error) {
        container.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                ${tier2.message || tier2.error}
            </div>
        `;
        return;
    }

    const impossibility = tier2.semantic_impossibility;

    container.innerHTML = `
        <div class="space-y-4">
            <div class="bg-white rounded-lg p-4 shadow">
                <h4 class="font-semibold text-gray-800 mb-3">Semantic Analysis</h4>
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <span class="text-sm text-gray-600">Impossibility Score</span>
                        <p class="text-2xl font-bold text-purple-600">${impossibility.score.toFixed(1)}/10</p>
                    </div>
                    <div>
                        <span class="text-sm text-gray-600">Primary Risk Type</span>
                        <p class="text-lg font-semibold ${getRiskTypeClass(impossibility.primary_risk_type)}">
                            ${impossibility.primary_risk_type.toUpperCase()}
                        </p>
                    </div>
                </div>

                ${impossibility.is_impossible ? `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                        <h5 class="font-semibold text-red-800 mb-2">⚠️ Request is Impossible or High-Risk</h5>
                        <p class="text-sm text-red-700">${impossibility.explanation}</p>
                    </div>
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h5 class="font-semibold text-blue-800 mb-2">💡 Recommendation</h5>
                        <p class="text-sm text-blue-700">${impossibility.recommendation}</p>
                    </div>
                ` : `
                    <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                        <p class="text-green-800"><i class="fas fa-check-circle mr-2"></i>No semantic impossibility detected</p>
                    </div>
                `}
            </div>

            <div class="bg-white rounded-lg p-4 shadow">
                <h4 class="font-semibold text-gray-800 mb-2">Cost Summary</h4>
                <div class="grid grid-cols-3 gap-4 text-sm">
                    <div>
                        <span class="text-gray-600">Input Tokens</span>
                        <p class="font-semibold">${tier2.cost.input_tokens}</p>
                    </div>
                    <div>
                        <span class="text-gray-600">Output Tokens</span>
                        <p class="font-semibold">${tier2.cost.output_tokens}</p>
                    </div>
                    <div>
                        <span class="text-gray-600">Total Cost</span>
                        <p class="font-semibold text-purple-600">$${tier2.cost.total_cost.toFixed(4)}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function clearForm() {
    elements.systemPrompt.value = '';
    elements.userPrompt.value = '';
    updateCharCounts();

    // Clear uploaded files
    for (const fileId of Object.values(state.uploadedFiles)) {
        removeFile(fileId);
    }

    // Hide results
    elements.resultsSection.classList.add('hidden');
    elements.exportBtn.disabled = true;

    // Reset state
    state.lastAnalysisResult = null;
}

function exportResults() {
    if (!state.lastAnalysisResult) return;

    const dataStr = JSON.stringify(state.lastAnalysisResult, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `prompt_analysis_${Date.now()}.json`;
    link.click();

    URL.revokeObjectURL(url);
}

// Utility functions
function getQualityBadgeClass(rating) {
    const classes = {
        'EXCELLENT': 'bg-green-100 text-green-800',
        'GOOD': 'bg-blue-100 text-blue-800',
        'FAIR': 'bg-yellow-100 text-yellow-800',
        'POOR': 'bg-orange-100 text-orange-800',
        'CRITICAL': 'bg-red-100 text-red-800'
    };
    return classes[rating] || 'bg-gray-100 text-gray-800';
}

function getScoreColor(score) {
    if (score >= 8) return 'bg-green-500';
    if (score >= 6) return 'bg-blue-500';
    if (score >= 4) return 'bg-yellow-500';
    return 'bg-red-500';
}

function getSeverityBorderClass(severity) {
    const classes = {
        'critical': 'border-red-500',
        'high': 'border-orange-500',
        'moderate': 'border-yellow-500',
        'low': 'border-blue-500'
    };
    return classes[severity] || 'border-gray-500';
}

function getSeverityBadgeClass(severity) {
    const classes = {
        'critical': 'bg-red-100 text-red-800',
        'high': 'bg-orange-100 text-orange-800',
        'moderate': 'bg-yellow-100 text-yellow-800',
        'low': 'bg-blue-100 text-blue-800'
    };
    return classes[severity] || 'bg-gray-100 text-gray-800';
}

function getRiskTypeClass(type) {
    const classes = {
        'safety': 'text-red-600',
        'security': 'text-orange-600',
        'semantic': 'text-purple-600',
        'none': 'text-green-600'
    };
    return classes[type] || 'text-gray-600';
}
