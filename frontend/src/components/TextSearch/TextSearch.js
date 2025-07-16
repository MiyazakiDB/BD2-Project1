import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Row, 
  Col, 
  Card, 
  Form, 
  Button, 
  Alert, 
  Spinner, 
  Badge,
  ProgressBar,
  Modal,
  Accordion,
  Tab,
  Tabs
} from 'react-bootstrap';
import { 
  FaSearch, 
  FaUpload, 
  FaFile, 
  FaTrash, 
  FaEye, 
  FaClock,
  FaDatabase,
  FaChartBar,
  FaCloudUploadAlt,
  FaFileAlt,
  FaStar,
  FaDownload
} from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './TextSearch.css';

const TextSearch = () => {
  // State management
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [indexStats, setIndexStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  
  // Form states
  const [textContent, setTextContent] = useState('');
  const [filename, setFilename] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  
  // Modal states
  const [showDocModal, setShowDocModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [activeTab, setActiveTab] = useState('search');

  const API_BASE = process.env.NODE_ENV === 'development' ? '/text-api' : 'http://localhost:8001';

  // Fetch initial data
  useEffect(() => {
    fetchDocuments();
    fetchIndexStats();
  }, []);

  // API functions
  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/documents`);
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const fetchIndexStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/index/stats`);
      if (response.ok) {
        const data = await response.json();
        setIndexStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, k: 10 })
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.results);
        toast.success(`Found ${data.total_found} results in ${data.search_time_ms}ms!`);
      } else {
        toast.error('Search failed');
      }
    } catch (error) {
      toast.error('Error performing search');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleTextUpload = async (e) => {
    e.preventDefault();
    if (!textContent.trim()) return;

    setUploadLoading(true);
    try {
      const response = await fetch(`${API_BASE}/upload-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textContent,
          filename: filename || 'document.txt',
          metadata: { uploaded_via: 'web_ui', type: 'text' }
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Document "${data.filename}" uploaded successfully!`);
        setTextContent('');
        setFilename('');
        fetchDocuments();
        fetchIndexStats();
      } else {
        toast.error('Upload failed');
      }
    } catch (error) {
      toast.error('Error uploading document');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;

    setUploadLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/upload-file`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`File "${data.filename}" uploaded successfully!`);
        setSelectedFile(null);
        fetchDocuments();
        fetchIndexStats();
      } else {
        toast.error('File upload failed');
      }
    } catch (error) {
      toast.error('Error uploading file');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    try {
      const response = await fetch(`${API_BASE}/documents/${docId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        toast.success('Document deleted successfully!');
        fetchDocuments();
        fetchIndexStats();
      } else {
        toast.error('Delete failed');
      }
    } catch (error) {
      toast.error('Error deleting document');
    }
  };

  const handleFinalizeIndex = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/finalize-index`, {
        method: 'POST'
      });

      if (response.ok) {
        toast.success('Index finalized successfully!');
        fetchIndexStats();
      } else {
        toast.error('Finalization failed');
      }
    } catch (error) {
      toast.error('Error finalizing index');
    } finally {
      setLoading(false);
    }
  };

  const showDocumentDetails = async (docId) => {
    try {
      const response = await fetch(`${API_BASE}/documents/${docId}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedDoc(data);
        setShowDocModal(true);
      }
    } catch (error) {
      toast.error('Error fetching document details');
    }
  };

  return (
    <Container fluid className="text-search-container">
      <ToastContainer position="top-right" autoClose={3000} />
      
      {/* Header */}
      <Row className="mb-4">
        <Col>
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-4 bg-gradient-primary rounded-3 shadow"
          >
            <h1 className="display-4 text-white mb-2">
              <FaDatabase className="me-3" />
              Text Document Search
            </h1>
            <p className="lead text-white-50 mb-0">
              Intelligent document indexing and similarity search powered by TF-IDF
            </p>
          </motion.div>
        </Col>
      </Row>

      {/* Stats Cards */}
      {indexStats && (
        <Row className="mb-4">
          <Col md={3}>
            <Card className="stats-card border-0 shadow-sm">
              <Card.Body className="text-center">
                <FaFileAlt className="stats-icon text-primary mb-2" />
                <h4 className="mb-1">{indexStats.total_documents}</h4>
                <small className="text-muted">Documents</small>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="stats-card border-0 shadow-sm">
              <Card.Body className="text-center">
                <FaChartBar className="stats-icon text-success mb-2" />
                <h4 className="mb-1">{indexStats.total_terms}</h4>
                <small className="text-muted">Terms</small>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="stats-card border-0 shadow-sm">
              <Card.Body className="text-center">
                <FaDatabase className="stats-icon text-info mb-2" />
                <h4 className="mb-1">{indexStats.index_size_mb} MB</h4>
                <small className="text-muted">Index Size</small>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="stats-card border-0 shadow-sm">
              <Card.Body className="text-center">
                <Button 
                  variant="outline-primary" 
                  onClick={handleFinalizeIndex}
                  disabled={loading}
                  className="w-100"
                >
                  {loading ? <Spinner size="sm" /> : 'Finalize Index'}
                </Button>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Main Content Tabs */}
      <Tabs activeKey={activeTab} onSelect={setActiveTab} className="mb-4">
        
        {/* Search Tab */}
        <Tab eventKey="search" title={<><FaSearch className="me-2" />Search</>}>
          <Row>
            <Col lg={8}>
              <Card className="border-0 shadow-sm mb-4">
                <Card.Body>
                  <Form onSubmit={handleSearch}>
                    <Row>
                      <Col>
                        <Form.Control
                          type="text"
                          placeholder="Enter your search query... (e.g., 'Python programming', 'machine learning')"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          size="lg"
                          className="search-input"
                        />
                      </Col>
                      <Col xs="auto">
                        <Button 
                          type="submit" 
                          size="lg"
                          disabled={searchLoading}
                          className="search-button"
                        >
                          {searchLoading ? <Spinner size="sm" /> : <FaSearch />}
                        </Button>
                      </Col>
                    </Row>
                  </Form>
                </Card.Body>
              </Card>

              {/* Search Results */}
              <AnimatePresence>
                {searchResults.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <h5 className="mb-3">Search Results</h5>
                    {searchResults.map((result, index) => (
                      <motion.div
                        key={result.doc_id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <Card className="result-card border-0 shadow-sm mb-3">
                          <Card.Body>
                            <div className="d-flex justify-content-between align-items-start mb-2">
                              <h6 className="mb-1">
                                <FaFileAlt className="me-2 text-primary" />
                                {result.filename}
                              </h6>
                              <Badge bg="primary" className="similarity-badge">
                                <FaStar className="me-1" />
                                {(result.similarity_score * 100).toFixed(1)}%
                              </Badge>
                            </div>
                            <p className="text-muted mb-2 result-preview">
                              {result.text_preview}
                            </p>
                            <div className="d-flex justify-content-between align-items-center">
                              <small className="text-muted">
                                <FaClock className="me-1" />
                                {result.created_at}
                              </small>
                              <Button
                                variant="outline-primary"
                                size="sm"
                                onClick={() => showDocumentDetails(result.doc_id)}
                              >
                                <FaEye className="me-1" />
                                View Details
                              </Button>
                            </div>
                          </Card.Body>
                        </Card>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </Col>

            {/* Quick Actions Sidebar */}
            <Col lg={4}>
              <Card className="border-0 shadow-sm">
                <Card.Header className="bg-light">
                  <h6 className="mb-0">Quick Search Examples</h6>
                </Card.Header>
                <Card.Body>
                  <div className="d-grid gap-2">
                    {[
                      'Python programming',
                      'machine learning',
                      'web framework',
                      'database systems',
                      'artificial intelligence'
                    ].map((example, index) => (
                      <Button
                        key={index}
                        variant="outline-secondary"
                        size="sm"
                        onClick={() => setSearchQuery(example)}
                      >
                        {example}
                      </Button>
                    ))}
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>

        {/* Upload Tab */}
        <Tab eventKey="upload" title={<><FaUpload className="me-2" />Upload</>}>
          <Row>
            <Col lg={6}>
              <Card className="border-0 shadow-sm">
                <Card.Header className="bg-primary text-white">
                  <h6 className="mb-0">
                    <FaCloudUploadAlt className="me-2" />
                    Upload Text Content
                  </h6>
                </Card.Header>
                <Card.Body>
                  <Form onSubmit={handleTextUpload}>
                    <Form.Group className="mb-3">
                      <Form.Label>Filename</Form.Label>
                      <Form.Control
                        type="text"
                        placeholder="Enter filename (optional)"
                        value={filename}
                        onChange={(e) => setFilename(e.target.value)}
                      />
                    </Form.Group>
                    <Form.Group className="mb-3">
                      <Form.Label>Text Content</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={8}
                        placeholder="Paste your text content here..."
                        value={textContent}
                        onChange={(e) => setTextContent(e.target.value)}
                        required
                      />
                    </Form.Group>
                    <Button 
                      type="submit" 
                      className="w-100"
                      disabled={uploadLoading}
                    >
                      {uploadLoading ? <Spinner size="sm" className="me-2" /> : <FaUpload className="me-2" />}
                      Upload Text
                    </Button>
                  </Form>
                </Card.Body>
              </Card>
            </Col>

            <Col lg={6}>
              <Card className="border-0 shadow-sm">
                <Card.Header className="bg-success text-white">
                  <h6 className="mb-0">
                    <FaFile className="me-2" />
                    Upload File
                  </h6>
                </Card.Header>
                <Card.Body>
                  <div className="upload-dropzone text-center p-4 border-2 border-dashed rounded">
                    <FaFile className="upload-icon mb-3 text-muted" />
                    <p className="mb-3">
                      Drag & drop a file here, or click to select
                    </p>
                    <Form.Control
                      type="file"
                      accept=".txt,.md,.csv"
                      onChange={(e) => setSelectedFile(e.target.files[0])}
                      className="mb-3"
                    />
                    {selectedFile && (
                      <Alert variant="info" className="text-start">
                        <strong>Selected:</strong> {selectedFile.name}
                        <br />
                        <strong>Size:</strong> {(selectedFile.size / 1024).toFixed(2)} KB
                      </Alert>
                    )}
                    <Button 
                      onClick={() => handleFileUpload(selectedFile)}
                      disabled={!selectedFile || uploadLoading}
                      className="w-100"
                    >
                      {uploadLoading ? <Spinner size="sm" className="me-2" /> : <FaUpload className="me-2" />}
                      Upload File
                    </Button>
                  </div>
                  <small className="text-muted">
                    Supported formats: .txt, .md, .csv
                  </small>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>

        {/* Documents Tab */}
        <Tab eventKey="documents" title={<><FaFileAlt className="me-2" />Documents ({documents.length})</>}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-info text-white">
              <h6 className="mb-0">
                <FaDatabase className="me-2" />
                Indexed Documents
              </h6>
            </Card.Header>
            <Card.Body>
              {documents.length === 0 ? (
                <Alert variant="info" className="text-center">
                  <FaFileAlt className="mb-2" size={48} />
                  <h6>No documents indexed yet</h6>
                  <p className="mb-0">Upload some documents to get started!</p>
                </Alert>
              ) : (
                <Row>
                  {documents.map((doc, index) => (
                    <Col lg={6} key={doc.doc_id} className="mb-3">
                      <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <Card className="document-card border-0 shadow-sm h-100">
                          <Card.Body>
                            <div className="d-flex justify-content-between align-items-start mb-2">
                              <h6 className="mb-1 text-truncate">
                                <FaFileAlt className="me-2 text-primary" />
                                {doc.filename}
                              </h6>
                              <Button
                                variant="outline-danger"
                                size="sm"
                                onClick={() => handleDeleteDocument(doc.doc_id)}
                              >
                                <FaTrash />
                              </Button>
                            </div>
                            <p className="text-muted small mb-2">
                              {doc.text_preview}
                            </p>
                            <div className="d-flex justify-content-between align-items-center">
                              <small className="text-muted">
                                {doc.size} chars
                              </small>
                              <Button
                                variant="outline-primary"
                                size="sm"
                                onClick={() => showDocumentDetails(doc.doc_id)}
                              >
                                <FaEye className="me-1" />
                                View
                              </Button>
                            </div>
                          </Card.Body>
                        </Card>
                      </motion.div>
                    </Col>
                  ))}
                </Row>
              )}
            </Card.Body>
          </Card>
        </Tab>
      </Tabs>

      {/* Document Details Modal */}
      <Modal 
        show={showDocModal} 
        onHide={() => setShowDocModal(false)} 
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>
            <FaFileAlt className="me-2" />
            Document Details
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedDoc && (
            <>
              <h6>Filename: {selectedDoc.metadata.filename}</h6>
              <p className="text-muted mb-3">
                Document ID: <code>{selectedDoc.doc_id}</code>
              </p>
              <Form.Control
                as="textarea"
                rows={15}
                value={selectedDoc.text}
                readOnly
                className="mb-3"
              />
              <Alert variant="info">
                <strong>Metadata:</strong>
                <pre className="mb-0 mt-2">
                  {JSON.stringify(selectedDoc.metadata, null, 2)}
                </pre>
              </Alert>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDocModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default TextSearch;
