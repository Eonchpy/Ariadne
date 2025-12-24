export interface Tag {
  id: string;
  name: string;
  parent_id: string | null;
  level: number;
  path: string;
  children?: Tag[];
  created_at: string;
  updated_at: string;
}

export interface TagCreateRequest {
  name: string;
  parent_id: string | null;
  level: number;
}

export interface TagUpdateRequest {
  name: string;
}

export interface TagUsage {
  tag_id: string;
  tag_name: string;
  table_count: number;
  tables: {
    id: string;
    name: string;
    source_id: string | null;
  }[];
}

export interface TagListResponse {
  items: Tag[];
}
