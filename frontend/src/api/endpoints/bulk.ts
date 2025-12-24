import client from '../client';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const bulkApi = {
  importData: async (formData: FormData, mode: 'validate' | 'preview' | 'execute' = 'execute') => {
    if (!formData.has('mode')) {
        formData.append('mode', mode);
    }
    
    if (USE_MOCKS) {
      await sleep(2000);
      if (mode === 'preview') {
          return {
              transaction_id: 'mock-trans-id',
              summary: { total_rows: 60, valid_rows: 60, invalid_rows: 0 },
              preview: { 
                  tables: [{ name: 'mock_table', row_index: 1 }],
                  lineage: []
              },
              errors: []
          };
      }
      return { 
        status: 'success', 
        summary: {
            tables_created: 10, 
            fields_created: 50, 
            lineage_created: 5
        },
        errors: [] 
      };
    }
    return client.post<any, any>('/bulk/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  exportData: async (params: { format: string; scope: string }) => {
    if (USE_MOCKS) {
      await sleep(1000);
      return;
    }
    const response = await client.get('/bulk/export', { 
      params, 
      responseType: 'blob' 
    });
    
    const url = window.URL.createObjectURL(new Blob([response as any]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `ariadne_export_${new Date().toISOString().split('T')[0]}.${params.format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
};