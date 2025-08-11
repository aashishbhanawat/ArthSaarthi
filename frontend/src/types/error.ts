export interface ApiErrorData {
  detail?: string | { msg: string }[];
}

export interface ApiError {
  response?: {
    data?: ApiErrorData;
  };
}
