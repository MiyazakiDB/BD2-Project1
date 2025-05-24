
import React, { useState } from 'react';
import { Database, Play, Upload, CheckCircle, AlertCircle } from 'lucide-react';

import './QueryConsole.css';


export default function QueryConsole() {
  const [activeTab, setActiveTab] = useState('upload');
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [queryText, setQueryText] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [fileData, setFileData] = useState({
    file: null,
    tableName: '',
    delimiter: ',',
    encoding: '',
    indexType: '',
    indexColumn: '',
    hasHeader: true
  });

  const handleFileUpload = async () => {
    if (!fileData.file || !fileData.tableName) {
      setError("Por favor selecciona un archivo y nombre de tabla");
      return;
    }

    setIsProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', fileData.file);
    formData.append('table_name', fileData.tableName);
    formData.append('delimiter', fileData.delimiter);
    formData.append('encoding', fileData.encoding);
    formData.append('index_type', fileData.indexType);
    formData.append('index_column', fileData.indexColumn);
    formData.append('has_header', fileData.hasHeader);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock successful response
      const mockData = {
        message: "Archivo procesado correctamente",
        header: ['ID', 'Producto', 'Cantidad', 'Precio'],
        rows: [
          ['1', 'Laptop', '10', '$999.99'],
          ['2', 'Mouse', '25', '$29.99'],
          ['3', 'Teclado', '15', '$79.99']
        ]
      };

      setUploadResult(mockData);
      setShowUploadForm(false);
    } catch (error) {
      setError(error.message);
    }

    setIsProcessing(false);
  };

  const handleQueryExecution = async () => {
    if (!queryText.trim()) {
      setError("Por favor ingresa una consulta SQL");
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Mock query result
      const mockResult = {
        header: ['Producto', 'Total'],
        rows: [
          ['Laptops', '10'],
          ['Mouses', '25'],
          ['Teclados', '15']
        ]
      };

      setQueryResult(mockResult);
    } catch (error) {
      setError(error.message);
    }

    setIsProcessing(false);
  };

  const renderTable = (data) => {
    if (!data || !data.header || !data.rows) return null;
    
    return (
      <div className="qc-table-container">
        <table className="qc-table">
          <thead>
            <tr>
              {data.header.map((header, index) => (
                <th key={index}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="qc-container">
      <div className="qc-title">Query Console</div>
      <div className="qc-subtitle">Importa datos y ejecuta consultas SQL en tiempo real</div>

      {/* Tab Navigation */}
      <div className="qc-tabs">
        <button
          onClick={() => setActiveTab('upload')}
          className={`qc-tab-btn${activeTab === 'upload' ? ' active' : ''}`}
        >
          <Database className="inline-block w-4 h-4 mr-2" />
          Importar Datos
        </button>
        <button
          onClick={() => setActiveTab('query')}
          className={`qc-tab-btn${activeTab === 'query' ? ' active' : ''}`}
        >
          <Play className="inline-block w-4 h-4 mr-2" />
          Ejecutar Query
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="qc-error">
          <AlertCircle className="w-5 h-5 mr-2" />
          {error}
        </div>
      )}

      {/* Upload Tab */}
      {activeTab === 'upload' && (
        <div className="qc-upload-section">
          <button
            onClick={() => setShowUploadForm(!showUploadForm)}
            className="qc-upload-btn"
          >
            <Upload className="w-4 h-4 mr-2" />
            Subir archivo
          </button>

          {showUploadForm && (
            <div className="qc-upload-form">
              <div className="qc-form-group">
                <label className="qc-form-label">
                  Archivo CSV/TXT:
                </label>
                <input
                  type="file"
                  accept=".csv,.txt"
                  onChange={(e) => setFileData({...fileData, file: e.target.files[0]})}
                  className="qc-form-input"
                />
              </div>

              <div className="qc-form-group">
                <label className="qc-form-label">
                  Nombre de la tabla:
                </label>
                <input
                  type="text"
                  value={fileData.tableName}
                  onChange={(e) => setFileData({...fileData, tableName: e.target.value})}
                  className="qc-form-input"
                />
              </div>

              <div className="qc-form-group">
                <label className="qc-form-label">
                  Delimitador:
                </label>
                <select
                  value={fileData.delimiter}
                  onChange={(e) => setFileData({...fileData, delimiter: e.target.value})}
                  className="qc-form-select"
                >
                  <option value=",">Coma (,)</option>
                  <option value=";">Punto y coma (;)</option>
                  <option value="\t">Tabulación (\t)</option>
                  <option value="|">Pipe (|)</option>
                  <option value=":">Dos puntos (:)</option>
                </select>
              </div>

              <div className="qc-form-group">
                <label className="qc-form-label">
                  Codificación (opcional):
                </label>
                <input
                  type="text"
                  value={fileData.encoding}
                  onChange={(e) => setFileData({...fileData, encoding: e.target.value})}
                  placeholder="utf-8, latin1, etc."
                  className="qc-form-input"
                />
              </div>

              <div className="qc-form-group">
                <label className="qc-form-label">
                  Tipo de índice (opcional):
                </label>
                <select
                  value={fileData.indexType}
                  onChange={(e) => setFileData({...fileData, indexType: e.target.value})}
                  className="qc-form-select"
                >
                  <option value="">Ninguno</option>
                  <option value="BTree">B+Tree</option>
                  <option value="Hash">Hash</option>
                  <option value="RTree">R-Tree</option>
                </select>
              </div>

              <div className="qc-form-group">
                <label className="qc-form-label">
                  Columna índice (opcional):
                </label>
                <input
                  type="text"
                  value={fileData.indexColumn}
                  onChange={(e) => setFileData({...fileData, indexColumn: e.target.value})}
                  placeholder="ej: id"
                  className="qc-form-input"
                />
              </div>

              <div className="qc-checkbox-group">
                <input
                  type="checkbox"
                  checked={fileData.hasHeader}
                  onChange={(e) => setFileData({...fileData, hasHeader: e.target.checked})}
                />
                <label className="qc-form-label">
                  ¿El archivo tiene cabecera?
                </label>
              </div>

              <button
                onClick={handleFileUpload}
                disabled={isProcessing || !fileData.file || !fileData.tableName}
                className="qc-submit-btn"
              >
                {isProcessing ? 'Procesando...' : 'Subir y Crear Tabla'}
              </button>
            </div>
          )}

          {uploadResult && (
            <div className="qc-success">
              <CheckCircle className="w-5 h-5 mr-2" />
              {uploadResult.message || "Archivo procesado correctamente."}
            </div>
          )}
          {uploadResult && renderTable(uploadResult)}
        </div>
      )}

      {/* Query Tab */}
      {activeTab === 'query' && (
        <div className="qc-query-section">
          <label className="qc-query-label">
            Consulta SQL:
          </label>
          <textarea
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="SELECT * FROM tu_tabla WHERE columna = 'valor';"
            rows="6"
            className="qc-form-textarea"
          />

          <div className="qc-query-actions">
            <button
              onClick={handleQueryExecution}
              disabled={isProcessing || !queryText.trim()}
              className="qc-query-btn"
            >
              <Play className="w-4 h-4 mr-2" />
              {isProcessing ? 'Ejecutando...' : 'Ejecutar Query'}
            </button>

            <button
              onClick={() => setQueryText('')}
              className="qc-clear-btn"
            >
              Limpiar
            </button>
          </div>

          <div className="qc-examples">
            <div className="qc-examples-title">Ejemplos de consultas:</div>
            <div className="qc-examples-list">
              <div className="qc-examples-item" onClick={() => setQueryText('SELECT * FROM productos LIMIT 10;')}>
                • SELECT * FROM productos LIMIT 10;
              </div>
              <div className="qc-examples-item" onClick={() => setQueryText('SELECT COUNT(*) FROM inventario;')}>
                • SELECT COUNT(*) FROM inventario;
              </div>
              <div className="qc-examples-item" onClick={() => setQueryText('SELECT categoria, SUM(cantidad) FROM productos GROUP BY categoria;')}>
                • SELECT categoria, SUM(cantidad) FROM productos GROUP BY categoria;
              </div>
            </div>
          </div>

          {queryResult && (
            <div className="qc-query-success">
              <CheckCircle className="w-5 h-5 mr-2" />
              Consulta ejecutada exitosamente
            </div>
          )}
          {queryResult && renderTable(queryResult)}
        </div>
      )}
    </div>
  );
}