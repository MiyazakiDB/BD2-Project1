// API Configuration
const API_BASE_URL = 'http://localhost:8000';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// Navigation helpers
function setActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath.endsWith(href)) {
            link.classList.add('active');
        }
    });
}

// Authentication functions
function checkAuthStatus() {
    const userDisplay = document.getElementById('user-display');
    const loginLink = document.getElementById('login-link');
    const logoutLink = document.getElementById('logout-link');
    
    if (authToken) {
        // Make API call to verify token and get user info
        fetch(`${API_BASE_URL}/users/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Accept': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                // Token invalid, clear it
                localStorage.removeItem('authToken');
                authToken = null;
                window.location.href = 'login.html';
                throw new Error('Invalid authentication');
            }
        })
        .then(data => {
            currentUser = data;
            if (userDisplay) {
                userDisplay.textContent = data.email || data.username;
                userDisplay.style.display = 'block';
            }
            if (loginLink) loginLink.style.display = 'none';
            if (logoutLink) logoutLink.style.display = 'block';
        })
        .catch(error => {
            console.error('Auth check failed:', error);
            if (userDisplay) userDisplay.style.display = 'none';
            if (loginLink) loginLink.style.display = 'block';
            if (logoutLink) logoutLink.style.display = 'none';
        });
    } else {
        // No token, show login link
        if (userDisplay) userDisplay.style.display = 'none';
        if (loginLink) loginLink.style.display = 'block';
        if (logoutLink) logoutLink.style.display = 'none';
        
        // Redirect to login if trying to access protected pages
        const protectedPages = ['dashboard.html', 'query.html', 'table-from-file.html', 'file-upload.html'];
        const currentPage = window.location.pathname.split('/').pop();
        
        if (protectedPages.includes(currentPage)) {
            window.location.href = 'login.html';
        }
    }
}

function login(username, password) {
    const loginStatus = document.getElementById('login-status');
    
    if (loginStatus) loginStatus.innerHTML = '<div class="loader"></div> Authenticating...';
    
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
        
        if (loginStatus) {
            loginStatus.innerHTML = '<span class="status-ok">Login successful! Redirecting...</span>';
        }
        
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1000);
    })
    .catch(error => {
        console.error('Login error:', error);
        if (loginStatus) {
            loginStatus.innerHTML = `<span class="status-error">Login failed: ${error.message}</span>`;
        }
    });
}

function logout() {
    localStorage.removeItem('authToken');
    authToken = null;
    window.location.href = 'login.html';
}

// API Helper Functions
function showLoading(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="loader"></div> ${message}`;
    }
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="status-error">${message}</div>`;
    }
}

function handleApiError(error, elementId) {
    console.error('API Error:', error);
    showError(elementId, `Error: ${error.message}`);
}

// Dashboard functions
function loadDashboardStats() {
    if (!authToken) return;
    
    showLoading('tables-count', 'Loading statistics...');
    showLoading('files-count');
    
    // Get table count
    fetch(`${API_BASE_URL}/inventory/tables`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const tablesCount = document.getElementById('tables-count');
        if (tablesCount) {
            tablesCount.innerHTML = data.tables ? data.tables.length : 0;
        }
    })
    .catch(error => handleApiError(error, 'tables-count'));
    
    // Get files count
    fetch(`${API_BASE_URL}/files/`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const filesCount = document.getElementById('files-count');
        if (filesCount) {
            filesCount.innerHTML = data.files ? data.files.length : 0;
        }
    })
    .catch(error => handleApiError(error, 'files-count'));
}

// SQL Query Functions
function setupQueryForm() {
    const queryForm = document.getElementById('query-form');
    if (!queryForm) return;
    
    queryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const queryText = document.getElementById('query').value;
        const format = document.querySelector('input[name="format"]:checked').value;
        const resultContainer = document.getElementById('query-result');
        
        showLoading('query-result', 'Executing query...');
        
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
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            
            if (format === 'csv') {
                return response.text();
            } else {
                return response.json();
            }
        })
        .then(data => {
            if (resultContainer) {
                if (format === 'csv') {
                    resultContainer.innerHTML = `<pre>${data}</pre>`;
                } else {
                    // Create a formatted result display
                    if (data.result && Array.isArray(data.result) && data.result.length > 0) {
                        // Display as table for SELECT results
                        let tableHtml = '<table class="data-table">';
                        
                        // Headers
                        tableHtml += '<thead><tr>';
                        for (const key of Object.keys(data.result[0])) {
                            tableHtml += `<th>${key}</th>`;
                        }
                        tableHtml += '</tr></thead>';
                        
                        // Body
                        tableHtml += '<tbody>';
                        for (const row of data.result) {
                            tableHtml += '<tr>';
                            for (const value of Object.values(row)) {
                                tableHtml += `<td>${value !== null ? value : 'NULL'}</td>`;
                            }
                            tableHtml += '</tr>';
                        }
                        tableHtml += '</tbody></table>';
                        
                        resultContainer.innerHTML = tableHtml;
                    } else {
                        // Display as JSON for other results
                        resultContainer.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    }
                }
            }
        })
        .catch(error => {
            handleApiError(error, 'query-result');
        });
    });
}

// File functions
function loadFiles() {
    if (!authToken) return;
    
    const filesList = document.getElementById('files-list');
    const fileSelect = document.getElementById('file-id');
    
    if (!filesList && !fileSelect) return;
    
    if (filesList) showLoading('files-list', 'Loading files...');
    
    fetch(`${API_BASE_URL}/files/`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.files && data.files.length > 0) {
            // Populate files list if it exists
            if (filesList) {
                let filesHtml = '<table class="data-table">';
                filesHtml += '<thead><tr><th>File Name</th><th>Size</th><th>Uploaded</th><th>Actions</th></tr></thead>';
                filesHtml += '<tbody>';
                
                data.files.forEach(file => {
                    const fileSize = formatFileSize(file.size || 0);
                    const uploadDate = new Date(file.created_at || new Date()).toLocaleString();
                    
                    filesHtml += `<tr>
                        <td>${file.filename}</td>
                        <td>${fileSize}</td>
                        <td>${uploadDate}</td>
                        <td>
                            <button class="btn btn-sm" onclick="previewFile('${file.id}')">Preview</button>
                        </td>
                    </tr>`;
                });
                
                filesHtml += '</tbody></table>';
                filesList.innerHTML = filesHtml;
            }
            
            // Populate select dropdown if it exists
            if (fileSelect) {
                // Clear existing options except the first one
                while (fileSelect.options.length > 1) {
                    fileSelect.remove(1);
                }
                
                data.files.forEach(file => {
                    const option = document.createElement('option');
                    option.value = file.id;
                    option.textContent = file.filename;
                    fileSelect.appendChild(option);
                });
            }
        } else {
            const message = '<div class="text-center mt-20 mb-20">No files available. Please upload files first.</div>';
            if (filesList) filesList.innerHTML = message;
            if (fileSelect && fileSelect.options.length <= 1) {
                const option = document.createElement('option');
                option.value = "";
                option.textContent = "No files available";
                option.disabled = true;
                fileSelect.appendChild(option);
            }
        }
    })
    .catch(error => {
        handleApiError(error, filesList ? 'files-list' : 'file-id');
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function previewFile(fileId) {
    // Implement file preview functionality
    alert(`Preview for file ${fileId} would be shown here.`);
}

// File upload function
function setupFileUpload() {
    const uploadForm = document.getElementById('upload-form');
    if (!uploadForm) return;
    
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('file');
        const uploadStatus = document.getElementById('upload-status');
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showError('upload-status', 'Please select a file to upload');
            return;
        }
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        showLoading('upload-status', 'Uploading file...');
        
        fetch(`${API_BASE_URL}/files/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (uploadStatus) {
                uploadStatus.innerHTML = `
                    <div class="status-ok">
                        File "${file.name}" uploaded successfully!
                    </div>
                `;
                // Reset form
                uploadForm.reset();
                
                // If we're on the upload page, reload file list
                if (document.getElementById('files-list')) {
                    setTimeout(() => loadFiles(), 1000);
                }
            }
        })
        .catch(error => {
            handleApiError(error, 'upload-status');
        });
    });
}

// Create table form
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
        
        showLoading('create-result', 'Creating table...');
        
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
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="status-ok mb-10">Table "${tableName}" created successfully!</div>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                `;
                
                // Reset form
                document.getElementById('table-name').value = '';
                document.getElementById('file-id').selectedIndex = 0;
                document.getElementById('index-type').selectedIndex = 0;
                document.getElementById('index-column').value = '';
            }
        })
        .catch(error => {
            handleApiError(error, 'create-result');
        });
    });
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    setActiveNavLink();
    checkAuthStatus();
    
    // Setup logout functionality
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
    
    // Initialize page-specific functionality
    const currentPage = window.location.pathname.split('/').pop();
    
    switch (currentPage) {
        case 'dashboard.html':
            loadDashboardStats();
            break;
        case 'query.html':
            setupQueryForm();
            break;
        case 'table-from-file.html':
            loadFiles();
            setupTableForm();
            break;
        case 'file-upload.html':
            setupFileUpload();
            loadFiles();
            break;
        case 'login.html':
            // Handle login form
            const loginForm = document.getElementById('login-form');
            if (loginForm) {
                loginForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    login(username, password);
                });
            }
            break;
    }
});
