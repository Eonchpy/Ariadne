import React, { useState, useEffect } from 'react';
import { Modal, Form, Select, Input, Radio, message } from 'antd';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { tablesApi } from '@/api/endpoints/tables';
import { lineageApi } from '@/api/endpoints/lineage';
import type { Table as MetadataTable } from '@/types/api';

const { Option } = Select;
const { TextArea } = Input;

const lineageSchema = z.object({
  type: z.enum(['table', 'field']),
  source_table_id: z.string().min(1, 'Source table is required'),
  target_table_id: z.string().min(1, 'Target table is required'),
  source_field_id: z.string().optional(),
  target_field_id: z.string().optional(),
  description: z.string().optional(),
  transformation: z.string().optional(),
}).refine((data) => {
  if (data.type === 'field') {
    return !!data.source_field_id && !!data.target_field_id;
  }
  return true;
}, {
  message: "Source and Target fields are required for field-level lineage",
  path: ["source_field_id"],
});

type LineageFormData = z.infer<typeof lineageSchema>;

interface Props {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialSourceTableId?: string;
  initialTargetTableId?: string;
}

const CreateLineageModal: React.FC<Props> = ({ visible, onClose, onSuccess, initialSourceTableId, initialTargetTableId }) => {
  const [tables, setTables] = useState<MetadataTable[]>([]);
  const [sourceFields, setSourceFields] = useState<any[]>([]);
  const [targetFields, setTargetFields] = useState<any[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const { control, handleSubmit, watch, reset, setValue, formState: { errors } } = useForm<LineageFormData>({
    resolver: zodResolver(lineageSchema),
    defaultValues: {
      type: 'table',
      source_table_id: initialSourceTableId || '',
      target_table_id: initialTargetTableId || '',
    },
  });

  const lineageType = watch('type');
  const sourceTableId = watch('source_table_id');
  const targetTableId = watch('target_table_id');

  useEffect(() => {
    if (visible) {
      loadTables();
      if (initialSourceTableId) setValue('source_table_id', initialSourceTableId);
      if (initialTargetTableId) setValue('target_table_id', initialTargetTableId);
    } else {
        reset();
    }
  }, [visible, initialSourceTableId, initialTargetTableId]);

  useEffect(() => {
    if (sourceTableId && lineageType === 'field') {
      loadFields(sourceTableId, setSourceFields);
    }
  }, [sourceTableId, lineageType]);

  useEffect(() => {
    if (targetTableId && lineageType === 'field') {
      loadFields(targetTableId, setTargetFields);
    }
  }, [targetTableId, lineageType]);

  const loadTables = async () => {
    try {
      const response = await tablesApi.list({ size: 100 });
      setTables(response.items);
    } catch (error) {
      message.error('Failed to load tables');
    }
  };

  const loadFields = async (tableId: string, setter: (fields: any[]) => void) => {
    try {
      const data = await tablesApi.get(tableId);
      setter(data.fields);
    } catch (error) {
      message.error('Failed to load fields');
    }
  };

  const onSubmit = async (data: LineageFormData) => {
    setSubmitting(true);
    try {
      if (data.type === 'table') {
        await lineageApi.createTableLineage({
          source_table_id: data.source_table_id,
          target_table_id: data.target_table_id,
          lineage_source: 'manual',
          metadata: { description: data.description },
          transformation_type: 'manual',
          transformation_logic: data.description || ''
        });
      } else {
        await lineageApi.createFieldLineage({
          source_field_id: data.source_field_id!,
          target_field_id: data.target_field_id!,
          lineage_source: 'manual',
          transformation_logic: data.transformation || '',
          metadata: { description: data.description }
        });
      }
      message.success('Lineage created');
      onSuccess();
      onClose();
    } catch (error: any) {
      message.error(error.response?.data?.error?.message || 'Failed to create lineage');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      title="Create Lineage"
      open={visible}
      onCancel={onClose}
      onOk={handleSubmit(onSubmit)}
      confirmLoading={submitting}
      width={600}
    >
      <Form layout="vertical">
        <Form.Item label="Lineage Type">
          <Controller
            name="type"
            control={control}
            render={({ field }) => (
              <Radio.Group {...field}>
                <Radio.Button value="table">Table Level</Radio.Button>
                <Radio.Button value="field">Field Level</Radio.Button>
              </Radio.Group>
            )}
          />
        </Form.Item>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Form.Item label="Source Table" validateStatus={errors.source_table_id ? 'error' : ''} help={errors.source_table_id?.message as any}>
            <Controller
              name="source_table_id"
              control={control}
              render={({ field }) => (
                <Select {...field} showSearch optionFilterProp="children" placeholder="Select Source">
                  {tables.map(t => <Option key={t.id} value={t.id}>{t.name}</Option>)}
                </Select>
              )}
            />
          </Form.Item>
          <Form.Item label="Target Table" validateStatus={errors.target_table_id ? 'error' : ''} help={errors.target_table_id?.message as any}>
            <Controller
              name="target_table_id"
              control={control}
              render={({ field }) => (
                <Select {...field} showSearch optionFilterProp="children" placeholder="Select Target">
                  {tables.map(t => <Option key={t.id} value={t.id}>{t.name}</Option>)}
                </Select>
              )}
            />
          </Form.Item>
        </div>

        {lineageType === 'field' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item label="Source Field" validateStatus={errors.source_field_id ? 'error' : ''} help={errors.source_field_id?.message as any}>
              <Controller
                name="source_field_id"
                control={control}
                render={({ field }) => (
                  <Select {...field} disabled={!sourceTableId} placeholder="Select Source Field">
                    {sourceFields.map(f => <Option key={f.id} value={f.id}>{f.name}</Option>)}
                  </Select>
                )}
              />
            </Form.Item>
            <Form.Item label="Target Field" validateStatus={errors.target_field_id ? 'error' : ''} help={errors.target_field_id?.message as any}>
              <Controller
                name="target_field_id"
                control={control}
                render={({ field }) => (
                  <Select {...field} disabled={!targetTableId} placeholder="Select Target Field">
                    {targetFields.map(f => <Option key={f.id} value={f.id}>{f.name}</Option>)}
                  </Select>
                )}
              />
            </Form.Item>
          </div>
        )}

        {lineageType === 'field' && (
          <Form.Item label="Transformation Logic">
            <Controller
              name="transformation"
              control={control}
              render={({ field }) => <Input {...field} placeholder="e.g. UPPER(email)" />}
            />
          </Form.Item>
        )}

        <Form.Item label="Description">
          <Controller
            name="description"
            control={control}
            render={({ field }) => <TextArea {...field} rows={2} />}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CreateLineageModal;
