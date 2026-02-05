import axios from 'axios';
import { api } from './api';
import type { PresignResponse } from '../types/document';

/**
 * Get a presigned S3 URL for uploading a document
 * @param filename - The name of the file to upload
 * @param contentType - The MIME type of the file (e.g., 'application/pdf', 'image/png')
 * @returns Promise with presigned URL and metadata
 */
export const getPresignedUrl = async (
  filename: string,
  contentType: string,
): Promise<PresignResponse> => {
  const response = await api.post<PresignResponse>('/document/presign', {
    filename,
    contentType,
  });
  return response.data;
};

/**
 * Upload a file directly to S3 using a presigned URL
 * @param presignedUrl - The presigned URL from the backend
 * @param file - The file to upload
 * @param onProgress - Optional callback for upload progress
 */
export const uploadToS3 = async (
  presignedUrl: string,
  file: File,
  onProgress?: (progress: number) => void,
): Promise<void> => {
  await axios.put(presignedUrl, file, {
    headers: {
      'Content-Type': file.type,
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total,
        );
        onProgress(percentCompleted);
      }
    },
  });
};

/**
 * Trigger backend processing for an uploaded document
 * @param uploadId - the id returned by the presign endpoint
 */
export const processDocument = async (uploadId: string) => {
  const resp = await api.post(`/document/${uploadId}/process`);
  return resp.data;
};
