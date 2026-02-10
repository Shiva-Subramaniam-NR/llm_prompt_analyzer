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
    const unified = data.unified;

    // Hide loading, show results
    elements.loadingState.classList.add('hidden');
    elements.resultsDisplay.classList.remove('hidden');

    // PRIORITY: Show unified score if available (Tier 2 was run)
    if (unified) {
        displayUnifiedVerdict(unified, tier1);
    } else {
        // Show Tier 1 only
        displayTier1Only(tier1);
    }

    // Component scores (always show)
    displayComponentScores(tier1.scores, unified);

    // Issues
    displayIssues(tier1.issues);

    // Tier 2 results
    if (data.tier2) {
        displayTier2Results(data.tier2, unified);
    } else {
        document.getElementById('tier2Results').classList.add('hidden');
    }
}

function displayUnifiedVerdict(unified, tier1) {
    const container = document.getElementById('overallQuality');

    // Determine visual style based on risk level
    const riskStyles = {
        'critical': {
            bgColor: 'bg-red-100 border-red-500',
            textColor: 'text-red-900',
            barColor: 'bg-red-600',
            icon: 'fa-exclamation-triangle',
            iconColor: 'text-red-600'
        },
        'high': {
            bgColor: 'bg-orange-100 border-orange-500',
            textColor: 'text-orange-900',
            barColor: 'bg-orange-500',
            icon: 'fa-exclamation-circle',
            iconColor: 'text-orange-600'
        },
        'moderate': {
            bgColor: 'bg-yellow-100 border-yellow-500',
            textColor: 'text-yellow-900',
            barColor: 'bg-yellow-500',
            icon: 'fa-exclamation',
            iconColor: 'text-yellow-600'
        },
        'low': {
            bgColor: 'bg-blue-100 border-blue-400',
            textColor: 'text-blue-900',
            barColor: 'bg-blue-500',
            icon: 'fa-info-circle',
            iconColor: 'text-blue-600'
        },
        'none': {
            bgColor: 'bg-green-100 border-green-400',
            textColor: 'text-green-900',
            barColor: 'bg-green-600',
            icon: 'fa-check-circle',
            iconColor: 'text-green-600'
        }
    };

    const style = riskStyles[unified.risk_level] || riskStyles['none'];

    container.innerHTML = `
        <div class="border-4 ${style.bgColor} rounded-lg p-6 mb-6">
            <div class="flex items-center mb-4">
                <i class="fas ${style.icon} ${style.iconColor} text-3xl mr-4"></i>
                <div class="flex-1">
                    <h2 class="text-2xl font-bold ${style.textColor}">FINAL VERDICT</h2>
                    <p class="text-lg font-semibold ${style.textColor} mt-1">${unified.verdict}</p>
                </div>
                <div class="text-right">
                    <div class="text-4xl font-bold ${style.textColor}">${unified.score.toFixed(1)}</div>
                    <div class="text-sm ${style.textColor}">/ 10</div>
                </div>
            </div>

            ${unified.primary_concern ? `
                <div class="bg-white bg-opacity-60 rounded p-4 mb-4">
                    <h3 class="font-semibold ${style.textColor} mb-2">⚠️ Primary Concern:</h3>
                    <p class="text-sm ${style.textColor}">${unified.primary_concern}</p>
                </div>
            ` : ''}

            <div class="w-full bg-gray-300 rounded-full h-4 mb-4">
                <div class="${style.barColor} h-4 rounded-full transition-all duration-500"
                     style="width: ${unified.score * 10}%"></div>
            </div>

            <details class="text-sm ${style.textColor}">
                <summary class="cursor-pointer font-semibold mb-2">ℹ️ Understanding Your Score</summary>
                <div class="pl-4 mt-2 space-y-2">
                    <p><strong>Tier 1 Score (${tier1.overall_score.toFixed(1)}/10):</strong> ${unified.tier1_explanation}</p>
                    <p><strong>Tier 2 Analysis:</strong> ${unified.tier2_explanation}</p>
                    <p><strong>Why ${unified.score.toFixed(1)}?</strong> ${
                        unified.risk_level === 'critical' || unified.risk_level === 'high'
                            ? 'Safety/security risks detected by Tier 2 override structural quality from Tier 1.'
                            : unified.risk_level === 'moderate'
                            ? 'Score blends Tier 1 structure (30%) and Tier 2 semantics (70%).'
                            : 'Tier 1 structural quality validated by Tier 2 semantic analysis.'
                    }</p>
                </div>
            </details>
        </div>

        <div class="text-sm text-gray-600 bg-gray-50 rounded p-4 mb-4">
            <strong>📊 For Reference - Tier 1 Structural Score:</strong> ${tier1.overall_score.toFixed(1)}/10 (${tier1.quality_rating.toUpperCase()})
            <br>
            <em>This measures format, consistency, and completeness only - not safety or semantics.</em>
        </div>
    `;
}

function displayTier1Only(tier1) {
    const container = document.getElementById('overallQuality');

    container.innerHTML = `
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-6 border-2 border-blue-200">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center">
                    <i class="fas fa-chart-line text-blue-600 text-3xl mr-4"></i>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">Structural Quality</h2>
                        <p class="text-sm text-gray-600">Tier 1 Analysis Only</p>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-4xl font-bold text-gray-800">${tier1.overall_score.toFixed(1)}</div>
                    <div class="text-sm text-gray-600">/ 10</div>
                    <span class="px-3 py-1 rounded-full text-xs font-semibold ${getQualityBadgeClass(tier1.quality_rating.toUpperCase())}">${tier1.quality_rating.toUpperCase()}</span>
                </div>
            </div>

            <div class="w-full bg-gray-300 rounded-full h-4 mb-4">
                <div class="bg-blue-600 h-4 rounded-full transition-all duration-500"
                     style="width: ${tier1.overall_score * 10}%"></div>
            </div>

            ${tier1.is_fulfillable
                ? '<p class="text-green-600 font-medium"><i class="fas fa-check-circle mr-2"></i>Can fulfill request</p>'
                : '<p class="text-red-600 font-medium"><i class="fas fa-times-circle mr-2"></i>Cannot fulfill request</p>'
            }

            <div class="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                <p class="text-sm text-yellow-800">
                    <strong>ℹ️ Note:</strong> This score measures prompt structure, format, and internal consistency only.
                    It does NOT evaluate safety, security, or ethical concerns.
                    For comprehensive analysis including safety checks, enable <strong>Tier 1 + Tier 2</strong> mode.
                </p>
            </div>
        </div>
    `;
}

function displayComponentScores(scores, unified) {
    const container = document.getElementById('componentScores');
    container.innerHTML = '';

    // Add header with explanation
    const header = document.createElement('div');
    header.className = 'mb-4 pb-3 border-b border-gray-200';
    header.innerHTML = `
        <h3 class="text-lg font-semibold text-gray-800 mb-2">Component Breakdown (Tier 1)</h3>
        <p class="text-sm text-gray-600">
            ${unified
                ? '<em>These structural metrics are informational. Final score is based on unified analysis above.</em>'
                : '<em>These metrics combine to form the overall score above.</em>'
            }
        </p>
    `;
    container.appendChild(header);

    const components = [
        {
            name: 'Alignment',
            score: scores.alignment,
            icon: 'fa-sync-alt',
            tooltip: 'How well the system prompt can fulfill user requests'
        },
        {
            name: 'Consistency',
            score: scores.consistency,
            icon: 'fa-check-double',
            tooltip: 'Internal consistency - no contradictions or conflicts'
        },
        {
            name: 'Verbosity',
            score: scores.verbosity,
            icon: 'fa-text-height',
            tooltip: 'Appropriate length and clarity - not too verbose or terse'
        },
        {
            name: 'Completeness',
            score: scores.completeness,
            icon: 'fa-puzzle-piece',
            tooltip: 'All necessary information and constraints are specified'
        }
    ];

    components.forEach(comp => {
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between py-2';
        div.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas ${comp.icon} text-gray-600"></i>
                <span class="font-medium text-gray-800">${comp.name}</span>
                <i class="fas fa-info-circle text-gray-400 text-xs cursor-help"
                   title="${comp.tooltip}"></i>
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

function displayTier2Results(tier2, unified) {
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

    // If unified score exists, show collapsed detailed analysis
    const defaultOpen = !unified;

    container.innerHTML = `
        <div class="space-y-4">
            <details ${defaultOpen ? 'open' : ''}>
                <summary class="cursor-pointer font-semibold text-gray-800 mb-3 hover:text-blue-600">
                    📊 Detailed Tier 2 Analysis (Click to ${defaultOpen ? 'collapse' : 'expand'})
                </summary>

                <div class="bg-white rounded-lg p-4 shadow mt-3">
                    <h4 class="font-semibold text-gray-800 mb-3">Semantic & Safety Analysis</h4>
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <span class="text-sm text-gray-600">Risk Score</span>
                            <p class="text-2xl font-bold text-purple-600">${impossibility.score.toFixed(1)}/10</p>
                            <span class="text-xs text-gray-500">Higher = More Risky</span>
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
                            <h5 class="font-semibold text-red-800 mb-2">⚠️ Issue Detected</h5>
                            <p class="text-sm text-red-700">${impossibility.explanation}</p>
                        </div>
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h5 class="font-semibold text-blue-800 mb-2">💡 Recommendation</h5>
                            <p class="text-sm text-blue-700">${impossibility.recommendation}</p>
                        </div>
                    ` : `
                        <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                            <p class="text-green-800"><i class="fas fa-check-circle mr-2"></i>No safety or semantic issues detected</p>
                            <p class="text-sm text-green-700 mt-2">${impossibility.explanation}</p>
                        </div>
                    `}

                    <div class="mt-4 text-xs text-gray-500">
                        Confidence: ${(impossibility.confidence * 100).toFixed(0)}%
                    </div>
                </div>
            </details>

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
