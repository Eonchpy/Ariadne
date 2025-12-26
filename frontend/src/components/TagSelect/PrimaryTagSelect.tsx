import React from 'react';
import { Select } from 'antd';
import { StarFilled } from '@ant-design/icons';

interface Props {
  value?: string | null;
  selectedTagIds: string[];
  availableTags: any[]; // Flat list of all available tag objects for lookup
  onChange: (id: string) => void;
  placeholder?: string;
}

const PrimaryTagSelect: React.FC<Props> = ({ value, selectedTagIds, availableTags, onChange, placeholder }) => {
  // Map selected IDs to their corresponding tag objects to get names/paths
  const options = availableTags
    .filter(tag => selectedTagIds.includes(tag.id))
    .map(tag => ({
      label: (
        <span>
          <StarFilled style={{ color: '#faad14', marginRight: 8 }} />
          {tag.path || tag.name}
        </span>
      ),
      value: tag.id
    }));

  return (
    <Select
      placeholder={placeholder || "Select primary business domain"}
      value={value}
      onChange={onChange}
      options={options}
      style={{ width: '100%' }}
      allowClear
    />
  );
};

export default PrimaryTagSelect;
