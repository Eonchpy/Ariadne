import React, { useEffect, useState } from 'react';
import { Form, Input, Button, Select, Checkbox, Card, Space, message, Typography, InputNumber, Divider, Alert } from 'antd';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeftOutlined, SaveOutlined, SyncOutlined } from '@ant-design/icons';
import { dataSourceFormSchema } from '@/utils/validation';
import type { DataSourceFormData } from '@/utils/validation';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import { dataSourcesApi } from '@/api/endpoints/dataSources';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const DataSourceForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = !!id;
  const { fetchSources } = useDataSourceStore();
  
  const [testingConnection, setTestingConnection] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [testResult, setTestResult] = useState<{ status: 'success' | 'failed', message: string } | null>(null);

  const { control, handleSubmit, watch, reset, trigger, getValues, formState: { errors } } = useForm<DataSourceFormData>({
    resolver: zodResolver(dataSourceFormSchema),
    defaultValues: {
      name: '',
      type: 'oracle',
      description: '',
      connection_config: {
        host: '',
        port: 1521,
        uri: '',
        hosts: '',
        use_ssl: false,
      },
    },
  });

  const selectedType = watch('type');

  useEffect(() => {
    if (isEditMode && id) {
      loadDataSource(id);
    }
  }, [id, isEditMode]);

  const loadDataSource = async (sourceId: string) => {
    try {
      const data = await dataSourcesApi.get(sourceId);
      reset({
        name: data.name,
        type: data.type,
        description: data.description,
        connection_config: data.connection_config || {},
      });
    } catch (error) {
      message.error('Failed to load data source');
      navigate('/sources');
    }
  };

  const onSubmit = async (data: DataSourceFormData) => {
    setSubmitting(true);
    try {
      if (isEditMode && id) {
        await dataSourcesApi.update(id, data);
        message.success('Data source updated');
      } else {
        await dataSourcesApi.create({ ...data, is_active: true });
        message.success('Data source created');
      }
      fetchSources();
      navigate('/sources');
    } catch (error: any) {
      message.error(error.response?.data?.error?.message || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTestConnection = async () => {
    const isValid = await trigger();
    if (!isValid) {
      message.error('Please fix validation errors before testing');
      return;
    }

    setTestingConnection(true);
    setTestResult(null);
    try {
      const data = getValues();
      const payload = {
        name: data.name || 'Test Connection',
        type: data.type,
        connection_config: data.connection_config
      };
      const result = await dataSourcesApi.testConnectionConfig(payload);
      
      const isSuccess = result.success;
      
      setTestResult({ status: isSuccess ? 'success' : 'failed', message: result.message });
      
      if (isSuccess) {
        const latencyText = result.latency_ms ? ` (${result.latency_ms.toFixed(2)}ms)` : '';
        message.success(`${result.message}${latencyText}`);
      } else {
        message.error(result.message || 'Connection failed');
      }
    } catch (error: any) {
      const msg = error.response?.data?.error?.message || 'Connection test failed';
      setTestResult({ status: 'failed', message: msg });
      message.error(msg);
    } finally {
      setTestingConnection(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/sources')}>Back</Button>
          <Title level={3} style={{ margin: 0 }}>{isEditMode ? 'Edit Data Source' : 'New Data Source'}</Title>
        </div>

        <Card>
          <Form layout="vertical" onFinish={handleSubmit(onSubmit)}>
            {/* Basic Info */}
            <Title level={5}>Basic Information</Title>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <Form.Item label="Name" validateStatus={errors.name ? 'error' : ''} help={errors.name?.message}>
                <Controller
                  name="name"
                  control={control}
                  render={({ field }) => <Input {...field} placeholder="Production DB" />}
                />
              </Form.Item>
              <Form.Item label="Type" validateStatus={errors.type ? 'error' : ''} help={errors.type?.message}>
                <Controller
                  name="type"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} disabled={isEditMode}>
                      <Option value="oracle">Oracle</Option>
                      <Option value="mongodb">MongoDB</Option>
                      <Option value="elasticsearch">Elasticsearch</Option>
                      <Option value="mysql">MySQL</Option>
                    </Select>
                  )}
                />
              </Form.Item>
            </div>
            <Form.Item label="Description">
              <Controller
                name="description"
                control={control}
                render={({ field }) => <TextArea {...field} rows={2} />}
              />
            </Form.Item>

            <Divider />

            {/* Connection Config */}
            <Title level={5}>Connection Details</Title>
            
            {/* ORACLE CONFIG */}
            {selectedType === 'oracle' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
                  <Form.Item label="Host" validateStatus={errors.connection_config?.host ? 'error' : ''} help={errors.connection_config?.host?.message as any}>
                    <Controller
                      name="connection_config.host"
                      control={control}
                      render={({ field }) => <Input {...(field as any)} />}
                    />
                  </Form.Item>
                  <Form.Item label="Port" validateStatus={errors.connection_config?.port ? 'error' : ''} help={errors.connection_config?.port?.message as any}>
                    <Controller
                      name="connection_config.port"
                      control={control}
                      render={({ field }) => <InputNumber {...(field as any)} style={{ width: '100%' }} />}
                    />
                  </Form.Item>
                </div>
                <Form.Item label="Service Name" validateStatus={errors.connection_config?.service_name ? 'error' : ''} help={errors.connection_config?.service_name?.message as any}>
                  <Controller
                    name="connection_config.service_name"
                    control={control}
                    render={({ field }) => <Input {...(field as any)} />}
                  />
                </Form.Item>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <Form.Item label="Username" validateStatus={errors.connection_config?.username ? 'error' : ''} help={errors.connection_config?.username?.message as any}>
                    <Controller
                      name="connection_config.username"
                      control={control}
                      render={({ field }) => <Input {...(field as any)} />}
                    />
                  </Form.Item>
                  <Form.Item label="Password" validateStatus={errors.connection_config?.password ? 'error' : ''} help={errors.connection_config?.password?.message as any}>
                    <Controller
                      name="connection_config.password"
                      control={control}
                      render={({ field }) => <Input.Password {...(field as any)} />}
                    />
                  </Form.Item>
                </div>
              </>
            )}

            {/* MYSQL CONFIG */}
            {selectedType === 'mysql' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
                  <Form.Item label="Host" validateStatus={errors.connection_config?.host ? 'error' : ''} help={errors.connection_config?.host?.message as any}>
                    <Controller
                      name="connection_config.host"
                      control={control}
                      render={({ field }) => <Input {...(field as any)} placeholder="localhost" />}
                    />
                  </Form.Item>
                  <Form.Item label="Port" validateStatus={errors.connection_config?.port ? 'error' : ''} help={errors.connection_config?.port?.message as any}>
                    <Controller
                      name="connection_config.port"
                      control={control}
                      defaultValue={3306}
                      render={({ field }) => <InputNumber {...(field as any)} style={{ width: '100%' }} />}
                    />
                  </Form.Item>
                </div>
                <Form.Item label="Database (Optional)" validateStatus={errors.connection_config?.database ? 'error' : ''} help={errors.connection_config?.database?.message as any}>
                  <Controller
                    name="connection_config.database"
                    control={control}
                    render={({ field }) => <Input {...(field as any)} placeholder="my_database" />}
                  />
                </Form.Item>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <Form.Item label="Username" validateStatus={errors.connection_config?.username ? 'error' : ''} help={errors.connection_config?.username?.message as any}>
                    <Controller
                      name="connection_config.username"
                      control={control}
                      render={({ field }) => <Input {...(field as any)} />}
                    />
                  </Form.Item>
                  <Form.Item label="Password" validateStatus={errors.connection_config?.password ? 'error' : ''} help={errors.connection_config?.password?.message as any}>
                    <Controller
                      name="connection_config.password"
                      control={control}
                      render={({ field }) => <Input.Password {...(field as any)} />}
                    />
                  </Form.Item>
                </div>
                <Form.Item>
                  <Controller
                    name="connection_config.use_ssl"
                    control={control}
                    render={({ field }) => (
                      <Checkbox checked={field.value as any} {...(field as any)}>
                        Use SSL
                      </Checkbox>
                    )}
                  />
                </Form.Item>
              </>
            )}

            {/* MONGODB CONFIG */}
            {selectedType === 'mongodb' && (
              <>
                <Form.Item label="Connection String (URI)" extra="Format: mongodb://... or mongodb+srv://..." validateStatus={errors.connection_config?.uri ? 'error' : ''} help={errors.connection_config?.uri?.message as any}>
                  <Controller
                    name="connection_config.uri"
                    control={control}
                    render={({ field }) => <Input {...(field as any)} placeholder="mongodb://user:pass@host:port" />}
                  />
                </Form.Item>
                <Form.Item label="Database Name" validateStatus={errors.connection_config?.database ? 'error' : ''} help={errors.connection_config?.database?.message as any}>
                  <Controller
                    name="connection_config.database"
                    control={control}
                    render={({ field }) => <Input {...(field as any)} />}
                  />
                </Form.Item>
              </>
            )}

            {/* ELASTICSEARCH CONFIG */}
            {selectedType === 'elasticsearch' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
                  <Form.Item label="Hosts" validateStatus={errors.connection_config?.hosts ? 'error' : ''} help={errors.connection_config?.hosts?.message as any}>
                    <Controller
                      name="connection_config.hosts"
                      control={control}
                      render={({ field }) => <Input {...(field as any)} placeholder="http://localhost:9200" />}
                    />
                  </Form.Item>
                  <Form.Item label="Port" validateStatus={errors.connection_config?.port ? 'error' : ''} help={errors.connection_config?.port?.message as any}>
                    <Controller
                      name="connection_config.port"
                      control={control}
                      render={({ field }) => <InputNumber {...(field as any)} style={{ width: '100%' }} />}
                    />
                  </Form.Item>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <Form.Item label="Username (Optional)" validateStatus={errors.connection_config?.username ? 'error' : ''} help={errors.connection_config?.username?.message as any}>
                    <Controller
                      name="connection_config.username"
                      control={control}
                      render={({ field }) => <Input {...(field as any)} />}
                    />
                  </Form.Item>
                  <Form.Item label="Password (Optional)" validateStatus={errors.connection_config?.password ? 'error' : ''} help={errors.connection_config?.password?.message as any}>
                    <Controller
                      name="connection_config.password"
                      control={control}
                      render={({ field }) => <Input.Password {...(field as any)} />}
                    />
                  </Form.Item>
                </div>
                <Form.Item>
                  <Controller
                    name="connection_config.use_ssl"
                    control={control}
                    render={({ field }) => <Checkbox checked={field.value as any} {...(field as any)}>Use SSL/HTTPS</Checkbox>}
                  />
                </Form.Item>
              </>
            )}

            {testResult && (
              <Alert
                message={testResult.message}
                type={testResult.status === 'success' ? 'success' : 'error'}
                showIcon
                style={{ marginBottom: 24 }}
              />
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 24 }}>
              <Button 
                icon={<SyncOutlined spin={testingConnection} />} 
                onClick={handleTestConnection}
                loading={testingConnection}
              >
                Test Connection
              </Button>
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={submitting}>
                {isEditMode ? 'Update' : 'Create'}
              </Button>
            </div>
          </Form>
        </Card>
      </Space>
    </div>
  );
};

export default DataSourceForm;