export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

export interface DataSourceConnectionConfig {
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  service_name?: string; // Oracle
  database?: string; // MongoDB
  use_ssl?: boolean; // Elasticsearch
  [key: string]: any;
}

export type DataSourceType = 'oracle' | 'mongodb' | 'elasticsearch';

export interface DataSource {
  id: string;
  name: string;
  type: DataSourceType;
  description?: string;
  connection_config?: DataSourceConnectionConfig; // Usually redacted in responses
  is_active: boolean;
  last_tested_at?: string;
  last_test_status?: 'success' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface CreateDataSourceRequest {
  name: string;
  type: DataSourceType;
  description?: string;
  connection_config: DataSourceConnectionConfig;
  is_active?: boolean;
}

export interface UpdateDataSourceRequest extends Partial<CreateDataSourceRequest> {}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  tested_at: string;
  latency_ms?: number;
}

export interface DataSourceListResponse {
  total: number;
  page: number;
  size: number;
  items: DataSource[];
}

// --- Table & Field Types ---

export interface Field {
  id: string;
  table_id: string;
  name: string;
  data_type: string;
  description?: string | null;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  ordinal_position?: number;
  created_at: string;
  updated_at: string;
}

export interface Table {
  id: string;
  source_id?: string | null;
  source_name?: string | null;
  name: string;
  schema_name?: string | null;
  qualified_name?: string | null;
  type: string;
  description?: string | null;
  tags?: string[];
  row_count?: number | null;
  field_count?: number;
  created_at: string;
  updated_at: string;
}

export interface TableDetail extends Table {
  fields: Field[];
}

export interface TableListResponse {
  total: number;
  page: number;
  size: number;
  items: Table[];
}

export interface CreateTableRequest {
  name: string;
  source_id?: string | null;
  schema_name?: string | null;
  qualified_name?: string | null;
  type: string;
  description?: string;
  tags?: string[];
}

export interface UpdateTableRequest extends Partial<CreateTableRequest> {}

export interface CreateFieldRequest {
  name: string;
  data_type: string;
  description?: string;
  is_nullable?: boolean;
  is_primary_key?: boolean;
  is_foreign_key?: boolean;
  ordinal_position?: number;
}

export type BatchCreateFieldsRequest = CreateFieldRequest[];

export interface IntrospectTableRequest {
  table_name: string;
  schema_name?: string;
}

export interface IntrospectTableResponse {
  table: Partial<Table>;
  fields: Partial<Field>[];
}

// --- Lineage Types ---

export interface LineageGraphNode {
  id: string;
  label: string;
  type: string;
  source_name?: string | null;
  parent_id?: string | null;
}

export interface LineageGraphEdge {
  id: string;
  from: string;
  to: string;
  lineage_source: 'manual' | 'approved' | 'inferred';
}

export interface LineageGraphResponse {
  root_id: string;
  nodes: LineageGraphNode[];
  edges: LineageGraphEdge[];
}

export interface TableLineageCreateRequest {
  source_table_id: string;
  target_table_id: string;
  lineage_source: string;
  metadata?: any;
  transformation_type?: string;
  transformation_logic?: string;
}

export interface FieldLineageCreateRequest {
  source_field_id: string;
  target_field_id: string;
  lineage_source: string;
  transformation_logic?: string;
  metadata?: any;
}

export interface LineageRelationship {
  id: string;
  source_node_id: string;
  target_node_id: string;
  type: 'table' | 'field';
  lineage_source: string;
  status: string;
}