import axios, { AxiosResponse, AxiosRequestConfig } from 'axios';

interface ApiResponse<T = any> {
    data: T;
    status: number;
}

class ApiService {
    private baseUrl: string;

    constructor(baseUrl: string = '') {
        this.baseUrl = baseUrl || import.meta.env.VITE_API_BASE_URL || '';
        console.log(baseUrl);
    }

    private getHeaders(authToken?: string): Record<string, string> {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };

        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        return headers;
    }

    async get<T>(endpoint: string, authToken?: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
        try {
            const response: AxiosResponse<T> = await axios.get(
                `${this.baseUrl}${endpoint}`,
                {
                    ...config,
                    headers: this.getHeaders(authToken),
                }
            );
            return {
                data: response.data,
                status: response.status,
            };
        } catch (error: any) {
            throw error;
        }
    }

    async post<T>(endpoint: string, data: any, authToken?: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
        try {
            const response: AxiosResponse<T> = await axios.post(
                `${this.baseUrl}${endpoint}`,
                data,
                {
                    ...config,
                    headers: this.getHeaders(authToken),
                }
            );
            return {
                data: response.data,
                status: response.status,
            };
        } catch (error: any) {
            throw error;
        }
    }

    async put<T>(endpoint: string, data: any, authToken?: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
        try {
            const response: AxiosResponse<T> = await axios.put(
                `${this.baseUrl}${endpoint}`,
                data,
                {
                    ...config,
                    headers: this.getHeaders(authToken),
                }
            );
            return {
                data: response.data,
                status: response.status,
            };
        } catch (error: any) {
            throw error;
        }
    }

    async delete<T>(endpoint: string, authToken?: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
        try {
            const response: AxiosResponse<T> = await axios.delete(
                `${this.baseUrl}${endpoint}`,
                {
                    ...config,
                    headers: this.getHeaders(authToken),
                }
            );
            return {
                data: response.data,
                status: response.status,
            };
        } catch (error: any) {
            throw error;
        }
    }
}

export const api = new ApiService();
export default ApiService;