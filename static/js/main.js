// Main JavaScript for User Interface

document.addEventListener('DOMContentLoaded', async function() {
    // Load symptoms from API (always fresh from training_data.csv)
    await loadSymptomsIntoDropdown();
    // Load medical camps on page load
    loadMedicalCamps();
    // Initialize symptom selector from dropdown
    initSymptomSelector();
    // Handle symptom form submission
    const symptomForm = document.getElementById('symptomForm');
    if (symptomForm) {
        symptomForm.addEventListener('submit', handleSymptomSubmit);
    }
});

async function loadSymptomsIntoDropdown() {
    const selectEl = document.getElementById('symptomSelect');
    if (!selectEl) return;
    try {
        const response = await fetch('/api/symptoms');
        const data = await response.json();
        if (data.success && Array.isArray(data.symptoms) && data.symptoms.length > 0) {
            selectEl.innerHTML = '';
            data.symptoms.forEach(function(symptom) {
                const opt = document.createElement('option');
                opt.value = symptom;
                opt.textContent = symptom;
                selectEl.appendChild(opt);
            });
        }
    } catch (e) {
        console.error('Could not load symptoms list:', e);
    }
}

function initSymptomSelector() {
    const searchInput = document.getElementById('symptomSearch');
    const selectEl = document.getElementById('symptomSelect');
    const addBtn = document.getElementById('addSymptomBtn');
    const selectedContainer = document.getElementById('selectedSymptoms');

    if (!searchInput || !selectEl || !addBtn || !selectedContainer) {
        return;
    }

    // Filter dropdown options based on search text
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        Array.from(selectEl.options).forEach(option => {
            const text = option.text.toLowerCase();
            option.style.display = text.includes(query) ? '' : 'none';
        });
    });

    // Add selected option as a chip
    addBtn.addEventListener('click', () => {
        const value = selectEl.value;
        if (!value) return;
        addSymptomChip(value, selectedContainer);
    });

    // Also allow double-click on option to add symptom quickly
    selectEl.addEventListener('dblclick', () => {
        const value = selectEl.value;
        if (!value) return;
        addSymptomChip(value, selectedContainer);
    });

    // Delegate remove button clicks
    selectedContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-symptom')) {
            const chip = e.target.closest('.symptom-chip');
            if (chip) {
                chip.remove();
            }
        }
    });
}

function addSymptomChip(symptom, container) {
    // Avoid duplicates
    const existing = container.querySelector(`[data-symptom="${symptom}"]`);
    if (existing) {
        return;
    }

    const chip = document.createElement('div');
    chip.className = 'symptom-chip';
    chip.setAttribute('data-symptom', symptom);
    chip.style.display = 'inline-flex';
    chip.style.alignItems = 'center';
    chip.style.padding = '4px 8px';
    chip.style.margin = '3px';
    chip.style.borderRadius = '12px';
    chip.style.backgroundColor = '#e8f4ff';
    chip.style.border = '1px solid #3498db';
    chip.innerHTML = `
        <span class="symptom-name" data-symptom="${symptom}" style="margin-right: 6px;">${symptom}</span>
        <button type="button" class="remove-symptom" data-symptom="${symptom}" style="border:none;background:none;cursor:pointer;font-weight:bold;">×</button>
    `;
    container.appendChild(chip);
}

function getSelectedSymptoms() {
    const selectedContainer = document.getElementById('selectedSymptoms');
    if (!selectedContainer) return [];
    const chips = selectedContainer.querySelectorAll('.symptom-chip');
    return Array.from(chips).map(chip => chip.getAttribute('data-symptom')).filter(Boolean);
}

async function handleSymptomSubmit(e) {
    e.preventDefault();
    
    const selectedSymptoms = getSelectedSymptoms();
    
    const formData = {
        patient_name: document.getElementById('patientName').value.trim(),
        age: parseInt(document.getElementById('age').value),
        gender: document.getElementById('gender').value,
        symptoms: selectedSymptoms
    };
    
    // Validation
    if (!formData.patient_name || !formData.age || !formData.gender || formData.symptoms.length === 0) {
        alert('Please fill in all required fields');
        return;
    }
    
    // Show loading
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Analyzing...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Prediction successful:', data);
            console.log('Medicines received:', data.medicines);
            displayResults(data);
            // Load and display medicine suggestions
            if (data.medicines && data.medicines.length > 0) {
                console.log('Loading medicine suggestions...');
                loadMedicineSuggestions(data.medicines);
                // Scroll to medicine section after a short delay
                setTimeout(() => {
                    const medicineSection = document.getElementById('medicineSection');
                    if (medicineSection) {
                        medicineSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                }, 500);
            } else {
                console.log('No medicines received in response');
            }
            // Show a button to view receipt instead of auto-redirect
            const resultsContent = document.getElementById('resultsContent');
            const receiptButton = document.createElement('div');
            receiptButton.style.marginTop = '20px';
            receiptButton.innerHTML = `
                <a href="/receipt/${data.consultation_id}" class="btn btn-primary">View Digital Receipt</a>
            `;
            resultsContent.querySelector('.result-box').appendChild(receiptButton);
        } else {
            alert('Error: ' + (data.error || 'Failed to analyze symptoms'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');
    
    const confidenceClass = data.confidence >= 70 ? 'confidence-high' : 
                           data.confidence >= 50 ? 'confidence-medium' : 'confidence-low';
    
    // Handle both field names for backward compatibility
    const specialization = data.recommended_specialization || data.specialization || 'General Physician';
    const predictedDisease = data.predicted_disease || 'Unknown';
    const confidence = data.confidence || 0;
    const token = data.token || 'N/A';
    
    resultsContent.innerHTML = `
        <div class="result-box">
            <h3>Prediction Results</h3>
            <div class="result-item">
                <strong>Predicted Disease:</strong> ${predictedDisease}
                <span class="confidence-badge ${confidenceClass}">${confidence}% confidence</span>
            </div>
            <div class="result-item">
                <strong>Recommended Specialization:</strong> ${specialization}
            </div>
            <div class="result-item">
                <strong>Token Number:</strong> <span style="color: #e74c3c; font-weight: bold; font-size: 1.2em;">${token}</span>
            </div>
            <div style="margin-top: 15px; padding: 15px; background: #fff3cd; border-radius: 5px;">
                <strong>⚠️ Important:</strong> This is an advisory prediction. Please consult a healthcare professional for proper diagnosis.
            </div>
        </div>
    `;
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function loadMedicineSuggestions(medicines) {
    const medicineSection = document.getElementById('medicineSection');
    const medicineContent = document.getElementById('medicineContent');
    
    if (!medicines || medicines.length === 0) {
        medicineSection.style.display = 'none';
        return;
    }
    
    let html = '<div class="medicine-list">';
    medicines.forEach(medicine => {
        html += `
            <div class="medicine-item">
                <h4>💊 ${medicine.name}</h4>
                <div class="medicine-details">
                    <div class="medicine-detail">
                        <strong>Dosage:</strong> ${medicine.dosage}
                    </div>
                    <div class="medicine-detail">
                        <strong>Frequency:</strong> ${medicine.frequency}
                    </div>
                    <div class="medicine-detail">
                        <strong>Duration:</strong> ${medicine.duration}
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    medicineContent.innerHTML = html;
    medicineSection.style.display = 'block';
    
    // Ensure the section is visible
    medicineSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function loadMedicalCamps() {
    const campsContent = document.getElementById('campsContent');
    
    try {
        const response = await fetch('/api/camps');
        const data = await response.json();
        
        if (data.success && data.camps.length > 0) {
            let html = '<div class="camp-list">';
            data.camps.forEach(camp => {
                const campDate = new Date(camp.date);
                const today = new Date();
                const isUpcoming = campDate >= today;
                
                html += `
                    <div class="camp-item">
                        <h4>${camp.camp_name}</h4>
                        <div class="camp-details">
                            <div class="camp-detail">
                                <strong>📍 Location:</strong> ${camp.location}
                            </div>
                            <div class="camp-detail">
                                <strong>📅 Date:</strong> ${camp.date}
                            </div>
                            <div class="camp-detail">
                                <strong>🕐 Time:</strong> ${camp.time}
                            </div>
                            <div class="camp-detail">
                                <strong>🏥 Services:</strong> ${camp.services_offered}
                            </div>
                            ${camp.contact_info ? `
                                <div class="camp-detail">
                                    <strong>📞 Contact:</strong> ${camp.contact_info}
                                </div>
                            ` : ''}
                        </div>
                        ${isUpcoming ? '<span style="color: #27ae60; font-weight: bold;">Upcoming</span>' : ''}
                    </div>
                `;
            });
            html += '</div>';
            campsContent.innerHTML = html;
        } else {
            campsContent.innerHTML = '<p>No medical camps available at the moment. Please check back later.</p>';
        }
    } catch (error) {
        console.error('Error loading camps:', error);
        campsContent.innerHTML = '<p style="color: #e74c3c;">Error loading medical camp information. Please try again later.</p>';
    }
}

