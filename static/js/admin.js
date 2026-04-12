// Admin Panel JavaScript

let editingCampId = null;

function showAddCampForm() {
    document.getElementById('campForm').style.display = 'block';
    document.getElementById('campFormElement').reset();
    document.getElementById('campId').value = '';
    editingCampId = null;
    document.getElementById('campForm').scrollIntoView({ behavior: 'smooth' });
}

function cancelCampForm() {
    document.getElementById('campForm').style.display = 'none';
    document.getElementById('campFormElement').reset();
    editingCampId = null;
}

async function editCamp(campId) {
    editingCampId = campId;
    document.getElementById('campForm').style.display = 'block';
    document.getElementById('campId').value = campId;
    
    try {
        const response = await fetch(`/admin/camps/${campId}`);
        const data = await response.json();
        
        if (data.success) {
            const camp = data.camp;
            document.getElementById('campName').value = camp.camp_name || '';
            document.getElementById('location').value = camp.location || '';
            document.getElementById('campDate').value = camp.date || '';
            document.getElementById('campTime').value = camp.time || '';
            document.getElementById('services').value = camp.services_offered || '';
            document.getElementById('contactInfo').value = camp.contact_info || '';
            
            document.getElementById('campForm').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert('Error loading camp data');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error loading camp data. Please try again.');
    }
}

async function deleteCamp(campId) {
    if (!confirm('Are you sure you want to delete this medical camp?')) {
        return;
    }
    
    try {
        const response = await fetch('/admin/camps', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'delete',
                id: campId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Camp deleted successfully!');
            location.reload();
        } else {
            alert('Error: ' + (data.message || 'Failed to delete camp'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
}

// Handle camp form submission
document.addEventListener('DOMContentLoaded', function() {
    const campForm = document.getElementById('campFormElement');
    if (campForm) {
        campForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                action: editingCampId ? 'update' : 'add',
                camp_name: document.getElementById('campName').value.trim(),
                location: document.getElementById('location').value.trim(),
                date: document.getElementById('campDate').value,
                time: document.getElementById('campTime').value.trim(),
                services_offered: document.getElementById('services').value.trim(),
                contact_info: document.getElementById('contactInfo').value.trim()
            };
            
            if (editingCampId) {
                formData.id = editingCampId;
            }
            
            try {
                const response = await fetch('/admin/camps', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert(data.message);
                    location.reload();
                } else {
                    alert('Error: ' + (data.message || 'Failed to save camp'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }
});

