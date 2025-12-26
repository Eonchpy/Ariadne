import { z } from 'zod';

export const oracleConfigSchema = z.object({
  host: z.string().min(1, 'Host is required'),
  port: z.coerce.number().int().min(1).max(65535),
  service_name: z.string().min(1, 'Service Name is required'),
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

export const mongoConfigSchema = z.object({
  database: z.string().min(1, 'Database name is required'),
  uri: z.string().min(1, 'Connection URI is required').refine((val) => val.startsWith('mongodb://') || val.startsWith('mongodb+srv://'), {
    message: 'Must start with mongodb:// or mongodb+srv://',
  }),
});

export const elasticConfigSchema = z.object({
  hosts: z.string().min(1, 'Hosts is required'),
  port: z.coerce.number().int().min(1).max(65535),
  username: z.string().optional(),
  password: z.string().optional(),
  use_ssl: z.boolean().default(false),
});

export const dataSourceFormSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters'),
  description: z.string().optional(),
  type: z.enum(['oracle', 'mongodb', 'elasticsearch']),
  connection_config: z.record(z.string(), z.any()),
}).superRefine((data, ctx) => {
  let result;
  if (data.type === 'oracle') {
    result = oracleConfigSchema.safeParse(data.connection_config);
  } else if (data.type === 'mongodb') {
    result = mongoConfigSchema.safeParse(data.connection_config);
  } else if (data.type === 'elasticsearch') {
    result = elasticConfigSchema.safeParse(data.connection_config);
  }

  if (result && !result.success) {
    result.error.issues.forEach((issue) => {
      ctx.addIssue({
        ...issue,
        path: ['connection_config', ...issue.path],
      });
    });
  }
});

export type DataSourceFormData = z.infer<typeof dataSourceFormSchema>;

// Table & Field Schemas

export const fieldSchema = z.object({
  name: z.string().min(1, 'Field name is required'),
  data_type: z.string().min(1, 'Data type is required'),
  description: z.string().optional(),
  is_nullable: z.boolean(),
  is_primary_key: z.boolean(),
});

export const tableFormSchema = z.object({
  name: z.string().min(1, 'Table name is required'),
  source_id: z.string().nullable().optional(),
  schema_name: z.string().optional(),
  type: z.string().min(1, 'Type is required'),
  description: z.string().optional(),
  fields: z.array(fieldSchema).min(1, 'At least one field is required'),
  tags: z.array(z.string()),
  primary_tag_id: z.string().nullable().optional(),
});

export type TableFormData = z.infer<typeof tableFormSchema>;