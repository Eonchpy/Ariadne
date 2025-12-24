import React, { useState } from 'react';
import { Card, Upload, Button, Select, Radio, Progress, Tag, message, Typography, Space, Tabs, Divider } from 'antd';
import { InboxOutlined, DownloadOutlined, UploadOutlined, EyeOutlined } from '@ant-design/icons';
import { bulkApi } from '@/api/endpoints/bulk';
import { useDataSourceStore } from '@/stores/dataSourceStore';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;
const { Option } = Select;

const BulkOperations: React.FC = () => {
  const { sources } = useDataSourceStore();
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importFormat, setImportFormat] = useState('csv');
  const [importStatus, setImportStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [importResult, setImportResult] = useState<any>(null);
  const [progress, setProgress] = useState(0);

  const [exportScope, setExportScope] = useState('all');
  const [exportSourceId, setExportSourceId] = useState<string | undefined>(undefined);
  const [exportFormat, setExportFormat] = useState('csv');
  const [exporting, setExporting] = useState(false);

  const handleImport = async (mode: 'preview' | 'execute') => {
    if (!importFile) {
      message.error('Please select a file to import');
      return;
    }

    setImportStatus(mode === 'preview' ? 'uploading' : 'processing');
    setProgress(10);

    const formData = new FormData();
    formData.append('file', importFile);
    formData.append('format', importFormat);

    try {
      const interval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const result = await bulkApi.importData(formData, mode);
      
      clearInterval(interval);
      setProgress(100);
      setImportStatus('success');
      setImportResult({ ...result, mode }); // Attach mode to result for UI logic
      
      if (mode === 'preview') {
          message.success('Preview generated');
      } else {
          message.success('Import completed successfully');
      }
    } catch (error: any) {
      setImportStatus('error');
      message.error(error.response?.data?.error?.message || 'Operation failed');
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await bulkApi.exportData({
        format: exportFormat,
        scope: exportScope === 'source' && exportSourceId ? `source:${exportSourceId}` : 'all',
      });
      message.success('Export started');
    } catch (error) {
      message.error('Export failed');
    } finally {
      setExporting(false);
    }
  };

  const importProps = {
    name: 'file',
    multiple: false,
    beforeUpload: (file: File) => {
      setImportFile(file);
      return false;
    },
    onRemove: () => {
      setImportFile(null);
      setImportStatus('idle');
      setImportResult(null);
      setProgress(0);
    },
    fileList: importFile ? [importFile as any] : [],
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Title level={3}>Bulk Operations</Title>
        
        <Card>
          <Tabs
            defaultActiveKey="import"
            items={[
              {
                key: 'import',
                label: <span><UploadOutlined />Import Metadata</span>,
                children: (
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <Paragraph>
                      Upload a file to bulk import tables, fields, and lineage relationships.
                      Supported formats: CSV, JSON, YAML, Excel.
                    </Paragraph>
                    
                    <Dragger {...importProps} style={{ padding: 20 }}>
                      <p className="ant-upload-drag-icon">
                        <InboxOutlined />
                      </p>
                      <p className="ant-upload-text">Click or drag file to this area to upload</p>
                      <p className="ant-upload-hint">
                        Support for a single or bulk upload.
                      </p>
                    </Dragger>

                    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                      <Text strong>Format:</Text>
                      <Select value={importFormat} onChange={setImportFormat} style={{ width: 120 }}>
                        <Option value="csv">CSV</Option>
                        <Option value="json">JSON</Option>
                        <Option value="yaml">YAML</Option>
                        <Option value="excel">Excel</Option>
                      </Select>
                      
                      <Button icon={<EyeOutlined />} onClick={() => handleImport('preview')} disabled={!importFile || importStatus === 'processing'} loading={importStatus === 'uploading'}>
                        Preview
                      </Button>
                      
                      <Button type="primary" onClick={() => handleImport('execute')} disabled={!importFile || importStatus === 'processing'} loading={importStatus === 'processing'}>
                        Import Now
                      </Button>
                    </div>

                    {importStatus !== 'idle' && (
                      <div>
                        <Progress percent={progress} status={importStatus === 'error' ? 'exception' : importStatus === 'success' ? 'success' : 'active'} />
                      </div>
                    )}

                    {importResult && (
                      <Card 
                        size="small" 
                        title={importResult.mode === 'preview' ? "Preview Results" : "Import Results"} 
                        style={{ background: '#f6ffed', borderColor: '#b7eb8f' }}
                      >
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <Space size="large">
                            {importResult.summary && (
                                <>
                                <Space><Tag color="blue">Tables: {importResult.summary.tables_created ?? 0}</Tag></Space>
                                <Space><Tag color="cyan">Fields: {importResult.summary.fields_created ?? 0}</Tag></Space>
                                <Space><Tag color="purple">Lineage: {importResult.summary.lineage_created ?? 0}</Tag></Space>
                                </>
                            )}
                            </Space>
                            
                            {importResult.mode === 'preview' && (
                                <Button type="primary" onClick={() => handleImport('execute')} style={{ marginTop: 8 }}>
                                    Confirm & Execute Import
                                </Button>
                            )}
                        </Space>
                      </Card>
                    )}
                  </Space>
                ),
              },
              {
                key: 'export',
                label: <span><DownloadOutlined />Export Metadata</span>,
                children: (
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <Paragraph>
                      Export metadata to a file for backup or migration purposes.
                    </Paragraph>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                      <Space direction="vertical">
                        <Text strong>Export Scope</Text>
                        <Radio.Group value={exportScope} onChange={e => setExportScope(e.target.value)}>
                          <Space direction="vertical">
                            <Radio value="all">All Metadata</Radio>
                            <Radio value="source">Specific Data Source</Radio>
                          </Space>
                        </Radio.Group>
                        {exportScope === 'source' && (
                          <Select 
                            style={{ width: '100%', marginTop: 8 }} 
                            placeholder="Select Source"
                            onChange={setExportSourceId}
                            value={exportSourceId}
                          >
                            {sources.map(s => <Option key={s.id} value={s.id}>{s.name}</Option>)}
                          </Select>
                        )}
                      </Space>

                      <Space direction="vertical">
                        <Text strong>Format</Text>
                        <Radio.Group value={exportFormat} onChange={e => setExportFormat(e.target.value)}>
                          <Space direction="vertical">
                            <Radio value="csv">CSV</Radio>
                            <Radio value="json">JSON</Radio>
                            <Radio value="yaml">YAML</Radio>
                            <Radio value="excel">Excel (.xlsx)</Radio>
                          </Space>
                        </Radio.Group>
                      </Space>
                    </div>

                    <Divider />

                    <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport} loading={exporting}>
                      Export Data
                    </Button>
                  </Space>
                ),
              },
            ]}
          />
        </Card>
      </Space>
    </div>
  );
};

export default BulkOperations;