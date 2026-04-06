export const getApiErrorMessage = (error: unknown, fallback: string): string => {
  const candidate = (
    error as {
      response?: { data?: { error?: unknown; message?: unknown } };
      message?: unknown;
    }
  );

  const apiError = candidate?.response?.data?.error;
  if (typeof apiError === 'string' && apiError.trim().length > 0) {
    return apiError;
  }

  const apiMessage = candidate?.response?.data?.message;
  if (typeof apiMessage === 'string' && apiMessage.trim().length > 0) {
    return apiMessage;
  }

  const genericMessage = candidate?.message;
  if (typeof genericMessage === 'string' && genericMessage.trim().length > 0) {
    return genericMessage;
  }

  return fallback;
};

