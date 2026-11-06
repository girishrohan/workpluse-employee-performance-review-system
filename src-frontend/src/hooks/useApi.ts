import { useQuery, useMutation, useQueryClient, type UseMutationResult, type UseQueryResult } from '@tanstack/react-query';
import axios, { AxiosError } from 'axios';

axios.defaults.baseURL = '/api';

export function useApi<T>(key: string, url: string): UseQueryResult<T, AxiosError> {
  return useQuery<T, AxiosError>({
    queryKey: [key],
    queryFn: async (): Promise<T> => {
      const response = await axios.get<T>(url);
      return response.data;
    },
  });
}

export function useApiMutation<T = unknown, TVariables = unknown>(
  key: string,
  url: string,
  method: 'POST' | 'PUT' | 'DELETE' = 'POST'
): UseMutationResult<T, AxiosError, TVariables> {
  const queryClient = useQueryClient();

  const mutationFn = async (data: TVariables): Promise<T> => {
    const response = await axios.request<T>({
      method,
      url,
      data,
    });
    return response.data;
  };

  return useMutation<T, AxiosError, TVariables>({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [key] });
    },
  });
}

interface LoginResponse {
  success: boolean;
  user?: { user_id: number; email: string; full_name: string; role: string };
  error?: string;
}

export function useAuth() {
  const queryClient = useQueryClient();

  const loginMutation = useMutation<LoginResponse, AxiosError, { email: string; password: string }>({
    mutationFn: async (credentials): Promise<LoginResponse> => {
      const response = await axios.post<LoginResponse>('/auth/login', credentials);
      return response.data;
    },
    onSuccess: (data): void => {
      localStorage.setItem('access_token', 'demo-token');
      localStorage.setItem('user', JSON.stringify(data.user));
      queryClient.setQueryData(['user'], data.user);
    },
  });

  const logoutMutation = useMutation<void, AxiosError, void>({
    mutationFn: async (): Promise<void> => {
      await axios.post('/auth/logout');
    },
    onSuccess: (): void => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      queryClient.removeQueries();
    },
  });

  return {
    login: loginMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    isLoginPending: loginMutation.isPending,
    isLogoutPending: logoutMutation.isPending,
  };
}