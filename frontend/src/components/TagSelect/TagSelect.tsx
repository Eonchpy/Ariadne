import React, { useEffect, useState } from 'react';
import { TreeSelect, message } from 'antd';
import { tagsApi } from '@/api/endpoints/tags';
import type { Tag } from '@/types/tag';

interface Props {
  value?: string[];
  onChange?: (value: string[]) => void;
  placeholder?: string;
  style?: React.CSSProperties;
}

const TagSelect: React.FC<Props> = ({ value, onChange, placeholder, style }) => {
  const [treeData, setTreeData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const formatTreeData = (tags: Tag[]): any[] => {
    return tags
      .filter(tag => tag.name !== 'DataSource' && !tag.path?.startsWith('DataSource'))
      .map(tag => ({
        title: tag.name,
        value: tag.id,
        key: tag.id,
        children: tag.children && tag.children.length > 0 ? formatTreeData(tag.children) : undefined,
      }));
  };

  const fetchTags = async () => {
    setLoading(true);
    try {
      const response = await tagsApi.list();
      setTreeData(formatTreeData(response.items));
    } catch (error) {
      message.error('Failed to load tag tree');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  return (
    <TreeSelect
      style={style}
      value={value}
      dropdownStyle={{ maxHeight: 400, overflow: 'auto' }}
      placeholder={placeholder || 'Select tags'}
      allowClear
      multiple
      treeDefaultExpandAll
      treeData={treeData}
      loading={loading}
      onChange={onChange}
      treeCheckable={true}
      showCheckedStrategy={TreeSelect.SHOW_ALL}
      showSearch
      filterTreeNode={(search, item) => 
        (item?.title as string)?.toLowerCase().indexOf(search.toLowerCase()) >= 0
      }
    />
  );
};

export default TagSelect;
