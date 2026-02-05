export interface PresignResponse {
  uploadUrl: string;
  uploadId: string;
}

export type UploadStatus =
  | 'idle'
  | 'uploading'
  | 'success'
  | 'error'
  | 'warning';

export interface UploadState {
  status: UploadStatus;
  progress?: number;
  message?: string;
  uploadId?: string;
}

export const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
];
export const ALLOWED_FILE_EXTENSIONS = [
  '.pdf',
  '.png',
  '.jpg',
  '.jpeg',
  '.txt',
];
export const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB in bytes
