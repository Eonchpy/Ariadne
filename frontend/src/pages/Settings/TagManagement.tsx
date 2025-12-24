import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Card, Input, Modal, Form, Typography, message, Popconfirm, Tag as AntdTag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { tagsApi } from '@/api/endpoints/tags';
import type { Tag, TagCreateRequest } from '@/types/tag';

const { Title } = Typography;

const TagManagement: React.FC = () => {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [parentId, setParentId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const fetchTags = async () => {
    setLoading(true);
    try {
      const response = await tagsApi.list();
      setTags(response.items);
    } catch (error) {
      message.error('Failed to load tags');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  const handleAdd = (parent?: Tag) => {
    setEditingTag(null);
    setParentId(parent ? parent.id : null);
    form.resetFields();
    form.setFieldsValue({ 
      level: parent ? parent.level + 1 : 1,
      parent_id: parent ? parent.id : null 
    });
    setIsModalOpen(true);
  };

  const handleEdit = (tag: Tag) => {
    setEditingTag(tag);
    setParentId(tag.parent_id);
    form.setFieldsValue({ name: tag.name });
    setIsModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await tagsApi.delete(id);
      message.success('Tag deleted');
      fetchTags();
    } catch (error: any) {
      message.error(error.response?.data?.error?.message || 'Failed to delete tag');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingTag) {
        await tagsApi.update(editingTag.id, { name: values.name });
        message.success('Tag updated');
      } else {
        const req: TagCreateRequest = {
          name: values.name,
          parent_id: parentId,
          level: values.level
        };
        await tagsApi.create(req);
        message.success('Tag created');
      }
      setIsModalOpen(false);
      fetchTags();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const columns = [
    {
      title: 'Tag Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Tag) => (
        <Space>
          <AntdTag color={record.level === 1 ? 'blue' : record.level === 2 ? 'cyan' : 'green'}>
            {text}
          </AntdTag>
        </Space>
      )
    },
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      width: 100,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 300,
      render: (_: any, record: Tag) => (
        <Space size="middle">
          {record.level < 3 && (
            <Button 
              type="link" 
              icon={<PlusOutlined />} 
              onClick={() => handleAdd(record)}
            >
              Add Child
            </Button>
          )}
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Delete this tag?"
            description="Deleting a tag will fail if it has children or is used by tables."
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Helper to filter tree data
  const filterTree = (list: Tag[]): Tag[] => {
    return list.reduce((acc: Tag[], tag) => {
      const nameMatch = tag.name.toLowerCase().includes(searchText.toLowerCase());
      const filteredChildren = tag.children ? filterTree(tag.children) : [];
      
      if (nameMatch || filteredChildren.length > 0) {
        acc.push({
          ...tag,
          children: filteredChildren.length > 0 ? filteredChildren : undefined
        });
      }
      return acc;
    }, []);
  };

  const filteredTags = searchText ? filterTree(tags) : tags;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3}>Tag Management</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleAdd()}>
          Add Root Tag
        </Button>
      </div>

      <Card size="small">
        <Input 
          placeholder="Search tags..." 
          prefix={<SearchOutlined />} 
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
          style={{ width: 300 }}
        />
      </Card>

      <Table 
        columns={columns} 
        dataSource={filteredTags} 
        rowKey="id" 
        loading={loading}
        pagination={false}
        expandable={{ defaultExpandAllRows: true }}
      />

      <Modal
        title={editingTag ? 'Edit Tag' : 'Create Tag'}
        open={isModalOpen}
        onOk={handleModalOk}
        onCancel={() => setIsModalOpen(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="name" 
            label="Tag Name" 
            rules={[{ required: true, message: 'Please input tag name' }]}
          >
            <Input placeholder="Enter tag name" />
          </Form.Item>
          {!editingTag && (
            <Form.Item name="level" hidden><Input /></Form.Item>
          )}
        </Form>
      </Modal>
    </Space>
  );
};

export default TagManagement;
