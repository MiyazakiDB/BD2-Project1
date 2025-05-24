// API base URL - change this to match your backend URL
const API_BASE_URL = 'http://localhost:8000';
let authToken = localStorage.getItem('authToken');

// Check API status
function checkApiStatus() {
    const statusElement = document.getElementById('api-status');
    
    fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            statusElement.innerHTML = '<span class="status-ok">API is running</span>';
        } else {
            statusElement.innerHTML = '<span class="status-error">API is not responding correctly</span>';
        }
    })
    .catch(error => {
        statusElement.innerHTML = `<span class="status-error">Cannot connect to API: ${error.message}</span>`;
    });
}

// Setup query form
function setupQueryForm() {
    const queryForm = document.getElementById('query-form');
    if (!queryForm) return;
    
    queryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const queryText = document.getElementById('query').value;
        const format = document.querySelector('input[name="format"]:checked').value;
        const resultContainer = document.getElementById('query-result');
        
        resultContainer.innerHTML = '<p>Loading results...</p>';
        
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        };
        
        if (format === 'csv') {
            headers['Accept'] = 'text/csv';
        } else {
            headers['Accept'] = 'application/json';
        }
        
        fetch(`${API_BASE_URL}/inventory/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ query: queryText })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error: ${response.status} ${response.statusText}`);
            }
            
            if (format === 'csv') {
                return response.text();
            } else {
                return response.json();
            }
        })
        .then(data => {
            if (format === 'csv') {
                resultContainer.innerHTML = `<pre>${data}</pre>`;
            } else {
                resultContainer.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            }
        })
        .catch(error => {
            resultContainer.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        });
    });
}

// Load files for table creation
function loadFiles() {
    const filesList = document.getElementById('files-list');
    const fileSelect = document.getElementById('file-id');
    
    if (!filesList || !fileSelect) return;
    
    fetch(`${API_BASE_URL}/files/`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.files && data.files.length > 0) {
            // Populate files list
            let filesHtml = '<ul>';
            data.files.forEach(file => {
                filesHtml += `<li>${file.filename} (${file.id})</li>`;
                
                // Add to select dropdown
                const option = document.createElement('option');
                option.value = file.id;
                option.textContent = file.filename;
                fileSelect.appendChild(option);
            });
            filesHtml += '</ul>';
            filesList.innerHTML = filesHtml;
        } else {
            filesList.innerHTML = '<p>No files available. Upload files first.</p>';
        }
    })
    .catch(error => {
        filesList.innerHTML = `<p class="error">Error loading files: ${error.message}</p>`;
    });
}

// Setup table creation form
function setupTableForm() {
    const tableForm = document.getElementById('create-table-form');
    if (!tableForm) return;
    
    tableForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const tableName = document.getElementById('table-name').value;
        const fileId = document.getElementById('file-id').value;
        const indexType = document.getElementById('index-type').value;
        const indexColumn = document.getElementById('index-column').value;
        const resultContainer = document.getElementById('create-result');
        
        resultContainer.innerHTML = '<p>Creating table...</p>';
        
        const payload = {
            table_name: tableName,
            file_id: fileId
        };
        
        if (indexType && indexColumn) {
            payload.index_type = indexType;
            payload.index_column = indexColumn;
        }
        
        fetch(`${API_BASE_URL}/inventory/create-table-from-file`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            resultContainer.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        })
        .catch(error => {
            resultContainer.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        });
    });
}

// Simple login function
function login(username, password) {
    fetch(`${API_BASE_URL}/auth/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        },
        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Login failed: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);
        alert('Login successful');
    })
    .catch(error => {
        alert(`Login error: ${error.message}`);
    });
}
