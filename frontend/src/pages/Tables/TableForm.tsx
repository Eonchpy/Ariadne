import React, { useEffect, useState } from 'react';
import { Form, Input, Button, Select, Checkbox, Card, Space, message, Typography, Table, Divider } from 'antd';
import { useForm, Controller, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeftOutlined, SaveOutlined, CloudDownloadOutlined, DeleteOutlined, PlusOutlined, StarFilled } from '@ant-design/icons';
import { tableFormSchema } from '@/utils/validation';
import type { TableFormData } from '@/utils/validation';
import { tablesApi } from '@/api/endpoints/tables';
import { tagsApi } from '@/api/endpoints/tags';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import TagSelect from '@/components/TagSelect/TagSelect';
import PrimaryTagSelect from '@/components/TagSelect/PrimaryTagSelect';
import { Tooltip } from 'antd';
import type { Tag } from '@/types/tag';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const TableForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = !!id;
  const { sources, fetchSources } = useDataSourceStore();
  const [flatTags, setFlatTags] = useState<Tag[]>([]);
  
  const [fetchingColumns, setFetchingColumns] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const { control, handleSubmit, watch, reset, setValue, getValues, formState: { errors } } = useForm<TableFormData>({
    resolver: zodResolver(tableFormSchema),
    defaultValues: {
      name: '',
      type: 'table',
      description: '',
      source_id: null,
      schema_name: '',
      fields: [],
      tags: [],
      primary_tag_id: null,
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'fields',
  });

  const selectedSourceId = watch('source_id');
  const selectedTagIds = watch('tags');

  const fetchFullTags = async () => {
    try {
      const response = await tagsApi.list();
      const flatten = (items: Tag[]): Tag[] => {
        return items.reduce((acc: Tag[], item) => {
          return acc.concat([item], item.children ? flatten(item.children) : []);
        }, []);
      };
      setFlatTags(flatten(response.items));
    } catch (e) {
      console.error('Failed to fetch flat tags');
    }
  };

  useEffect(() => {
    fetchSources();
    fetchFullTags();
    if (isEditMode && id) {
      loadTable(id);
    }
  }, [id, isEditMode, fetchSources]);

  const loadTable = async (tableId: string) => {
    try {
      const [data, tagsData] = await Promise.all([
        tablesApi.get(tableId),
        tagsApi.getTableTags(tableId)
      ]);
      reset({
        name: data.name,
        type: data.type,
        description: data.description || '',
        source_id: data.source_id,
        schema_name: data.schema_name || '',
        primary_tag_id: data.primary_tag_id,
        // Load all tags into state to maintain data integrity
        tags: (tagsData.items || []).map(t => t.id),
        fields: (data.fields || []).map(f => ({
          name: f.name,
          data_type: f.data_type,
          description: f.description || '',
          is_nullable: f.is_nullable,
          is_primary_key: f.is_primary_key,
        })),
      });
    } catch (error) {
      message.error('Failed to load table');
      navigate('/metadata/tables');
    }
  };

  const onSubmit = async (data: TableFormData) => {
    setSubmitting(true);
    try {
      const { fields, tags, primary_tag_id, ...tableData } = data;

      // Ensure primary tag is in the tags list
      const finalTagIds = [...(tags || [])];
      if (primary_tag_id && !finalTagIds.includes(primary_tag_id)) {
        finalTagIds.push(primary_tag_id);
      }

      // --- AUTO-TAGGING LOGIC (System Tag) ---
      const selectedSource = sources.find(s => s.id === tableData.source_id);
      
      if (selectedSource) {
        try {
          const systemTagPath = `DataSource-${selectedSource.type}-${selectedSource.name}`;
          const allTags = await tagsApi.list();
          
          const findTagByPath = (items: any[], path: string): any => {
            for (const item of items) {
              if (item.path === path) return item;
              if (item.children) {
                const found = findTagByPath(item.children, path);
                if (found) return found;
              }
            }
            return null;
          };

          const systemTag = findTagByPath(allTags.items, systemTagPath);
          if (systemTag && !finalTagIds.includes(systemTag.id)) {
            finalTagIds.push(systemTag.id);
          }
        } catch (tagError) {
          console.error('Failed to auto-resolve system tag', tagError);
        }
      }
      // ---------------------------

      const payload = {
        ...tableData,
        primary_tag_id: primary_tag_id || null
      };

      if (isEditMode && id) {
        await tablesApi.update(id, payload);
        await tagsApi.addTableTags(id, finalTagIds);
        message.success('Table updated');
      } else {
        const table = await tablesApi.create(payload);
        if (fields.length > 0) {
          await tablesApi.batchCreateFields(table.id, fields);
        }
        if (finalTagIds.length > 0) {
          await tagsApi.addTableTags(table.id, finalTagIds);
        }
        message.success('Table created');
      }
      navigate('/metadata/tables');
    } catch (error: any) {
      message.error(error.response?.data?.error?.message || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFetchColumns = async () => {
    const sourceId = getValues('source_id');
    const tableName = getValues('name');
    const schemaName = getValues('schema_name');

    if (!sourceId) {
      message.warning('Please select a data source first');
      return;
    }
    if (!tableName) {
      message.warning('Please enter a table name');
      return;
    }

    setFetchingColumns(true);
    try {
      const result = await tablesApi.introspect(sourceId, { 
        table_name: tableName, 
        schema_name: schemaName || undefined 
      });
      
      // Populate fields
      const newFields = result.fields.map(f => ({
        name: f.name || '',
        data_type: f.data_type || 'VARCHAR',
        description: f.description || '',
        is_nullable: f.is_nullable ?? true,
        is_primary_key: f.is_primary_key ?? false,
      }));
      
      setValue('fields', newFields);
      message.success(`Fetched ${newFields.length} columns`);
    } catch (error: any) {
      message.error(error.response?.data?.error?.message || 'Failed to fetch columns');
    } finally {
      setFetchingColumns(false);
    }
  };

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/metadata/tables')}>Back</Button>
          <Title level={3} style={{ margin: 0 }}>{isEditMode ? 'Edit Table' : 'New Table'}</Title>
        </div>

        <Card>
          <Form layout="vertical" onFinish={handleSubmit(onSubmit)}>
            {/* Basic Info */}
            <Title level={5}>Basic Information</Title>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <Form.Item label="Data Source" help="Leave empty for manual documentation">
                <Controller
                  name="source_id"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} allowClear placeholder="Select Source (Optional)">
                      {sources.map(s => <Option key={s.id} value={s.id}>{s.name}</Option>)}
                    </Select>
                  )}
                />
              </Form.Item>
              <Form.Item label="Type">
                <Controller
                  name="type"
                  control={control}
                  render={({ field }) => (
                    <Select {...field}>
                      <Option value="table">Table</Option>
                      <Option value="view">View</Option>
                      <Option value="collection">Collection</Option>
                      <Option value="index">Index</Option>
                    </Select>
                  )}
                />
              </Form.Item>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <Form.Item 
                label={
                  <Space>
                    Primary Business Domain
                    <Tooltip title="This tag determines how the table is grouped in the blood lineage graph">
                      <StarFilled style={{ color: '#faad14' }} />
                    </Tooltip>
                  </Space>
                }
                required
                validateStatus={errors.primary_tag_id ? 'error' : ''}
                help={errors.primary_tag_id?.message as any}
              >
                <Controller
                  name="primary_tag_id"
                  control={control}
                  render={({ field }) => (
                    <PrimaryTagSelect 
                      {...field} 
                      selectedTagIds={selectedTagIds || []} 
                      availableTags={flatTags}
                    />
                  )}
                />
              </Form.Item>

              <Form.Item label="Additional Business Tags">
                <Controller
                  name="tags"
                  control={control}
                  render={({ field }) => (
                    <TagSelect 
                      {...field} 
                      value={(field.value || []).filter(id => {
                        const tag = flatTags.find(t => t.id === id);
                        return !tag?.path?.startsWith('DataSource');
                      })}
                      onChange={(newIds) => {
                        const systemIds = (field.value || []).filter(id => {
                          const tag = flatTags.find(t => t.id === id);
                          return tag?.path?.startsWith('DataSource');
                        });
                        field.onChange([...newIds, ...systemIds]);
                      }}
                      placeholder="Assign more business tags" 
                    />
                  )}
                />
              </Form.Item>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 16, alignItems: 'center' }}>
              <Form.Item label="Schema Name (Optional)">
                <Controller
                  name="schema_name"
                  control={control}
                  render={({ field }) => <Input {...field} placeholder="public" />}
                />
              </Form.Item>
              <Form.Item label="Table Name" validateStatus={errors.name ? 'error' : ''} help={errors.name?.message as any}>
                <Controller
                  name="name"
                  control={control}
                  render={({ field }) => <Input {...field} placeholder="users" />}
                />
              </Form.Item>
              
              {selectedSourceId && (
                <div style={{ marginTop: 6 }}>
                  <Button 
                    icon={<CloudDownloadOutlined />} 
                    onClick={handleFetchColumns}
                    loading={fetchingColumns}
                  >
                    Fetch Columns
                  </Button>
                </div>
              )}
            </div>

            <Form.Item label="Description">
              <Controller
                name="description"
                control={control}
                render={({ field }) => <TextArea {...field} rows={2} />}
              />
            </Form.Item>

            <Divider />

            {/* Fields Section */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <Title level={5}>Columns / Fields</Title>
              <Button type="dashed" icon={<PlusOutlined />} onClick={() => append({ name: '', data_type: '', is_nullable: true, is_primary_key: false })}>
                Add Field
              </Button>
            </div>

            <Table
              dataSource={fields}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                {
                  title: 'Name',
                  dataIndex: 'name',
                  render: (_, __, index) => (
                    <Controller
                      name={`fields.${index}.name`}
                      control={control}
                      render={({ field }) => <Input {...field} status={errors.fields?.[index]?.name ? 'error' : ''} />}
                    />
                  ),
                },
                {
                  title: 'Data Type',
                  dataIndex: 'data_type',
                  width: 150,
                  render: (_, __, index) => (
                    <Controller
                      name={`fields.${index}.data_type`}
                      control={control}
                      render={({ field }) => <Input {...field} status={errors.fields?.[index]?.data_type ? 'error' : ''} />}
                    />
                  ),
                },
                {
                  title: 'Nullable',
                  dataIndex: 'is_nullable',
                  width: 80,
                  align: 'center',
                  render: (_, __, index) => (
                    <Controller
                      name={`fields.${index}.is_nullable`}
                      control={control}
                      render={({ field }) => <Checkbox checked={field.value} {...field} />}
                    />
                  ),
                },
                {
                  title: 'PK',
                  dataIndex: 'is_primary_key',
                  width: 60,
                  align: 'center',
                  render: (_, __, index) => (
                    <Controller
                      name={`fields.${index}.is_primary_key`}
                      control={control}
                      render={({ field }) => <Checkbox checked={field.value} {...field} />}
                    />
                  ),
                },
                {
                  title: 'Description',
                  dataIndex: 'description',
                  render: (_, __, index) => (
                    <Controller
                      name={`fields.${index}.description`}
                      control={control}
                      render={({ field }) => <Input {...field} />}
                    />
                  ),
                },
                {
                  width: 50,
                  render: (_, __, index) => (
                    <Button type="text" danger icon={<DeleteOutlined />} onClick={() => remove(index)} />
                  ),
                },
              ]}
            />
            {errors.fields?.root && <Text type="danger">{errors.fields.root.message}</Text>}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 24 }}>
              <Button onClick={() => navigate('/metadata/tables')}>Cancel</Button>
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

export default TableForm;
