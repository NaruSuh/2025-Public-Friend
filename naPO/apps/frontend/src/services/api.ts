import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('[API Error]', error);
        return Promise.reject(error);
      }
    );
  }

  // Query API
  async parseQuery(query: string) {
    const response = await this.client.post('/query', { query });
    return response.data;
  }

  async executeQuery(parsedQuery: any) {
    const response = await this.client.post('/query/execute', { parsedQuery });
    return response.data;
  }

  // Sources API
  async getSources() {
    // Backend endpoint is /sources/apis not /sources
    const response = await this.client.get('/sources/apis');
    return response.data;
  }

  async getSource(id: string) {
    const response = await this.client.get(`/sources/apis/${id}`);
    return response.data;
  }

  async addApiKey(sourceId: string, keyValue: string, label?: string) {
    const response = await this.client.post(`/sources/apis/${sourceId}/keys`, {
      keyValue,
      label,
    });
    return response.data;
  }

  async toggleApiKey(sourceId: string, keyId: string, isActive: boolean) {
    const response = await this.client.patch(`/sources/apis/${sourceId}/keys/${keyId}`, {
      isActive,
    });
    return response.data;
  }

  async deleteApiKey(sourceId: string, keyId: string) {
    const response = await this.client.delete(`/sources/apis/${sourceId}/keys/${keyId}`);
    return response.data;
  }

  // Crawl API
  async startCrawl(options: any) {
    const response = await this.client.post('/crawl', options);
    return response.data;
  }

  async getCrawlStatus(jobId: string) {
    const response = await this.client.get(`/crawl/${jobId}`);
    return response.data;
  }

  // Parse API
  async parsePdf(file: File, parserId: string, options?: any) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('parserId', parserId);
    if (options) {
      formData.append('options', JSON.stringify(options));
    }

    const response = await this.client.post('/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async getAvailableParsers() {
    const response = await this.client.get('/parse/parsers');
    return response.data;
  }

  // Export API
  async exportData(data: any[], format: string, options?: any) {
    const response = await this.client.post(
      '/export',
      {
        data,
        format,
        options,
      },
      {
        responseType: format === 'csv' || format === 'xlsx' ? 'blob' : 'json',
      }
    );
    return response.data;
  }

  // History API
  async getQueryHistory(limit = 50, offset = 0) {
    const response = await this.client.get('/history', {
      params: { limit, offset },
    });
    return response.data;
  }

  // Generic HTTP methods
  async get(url: string, config?: any) {
    const response = await this.client.get(url, config);
    return response;
  }

  async post(url: string, data?: any, config?: any) {
    const response = await this.client.post(url, data, config);
    return response;
  }

  async patch(url: string, data?: any, config?: any) {
    const response = await this.client.patch(url, data, config);
    return response;
  }

  async delete(url: string, config?: any) {
    const response = await this.client.delete(url, config);
    return response;
  }

  async put(url: string, data?: any, config?: any) {
    const response = await this.client.put(url, data, config);
    return response;
  }
}

export const apiService = new ApiService();
export default apiService;
