import { useState, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
  LinearProgress,
} from '@mui/material';
import { CloudUpload as CloudUploadIcon } from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers';
import {
  type NewUser,
  type UserValidation,
  validateNewUser,
} from '../types/user';
import {
  type UploadState,
  ALLOWED_FILE_TYPES,
  ALLOWED_FILE_EXTENSIONS,
  MAX_FILE_SIZE,
  type PresignResponse,
} from '../types/document';
import {
  getPresignedUrl,
  uploadToS3,
  processDocument,
} from '../services/documentService';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import { MIN_USER_AGE } from '../config/constants';

interface CreateUserDialogProps {
  open: boolean;
  onClose: () => void;
  onCreateUser: (userData: NewUser) => Promise<boolean>;
}

export const CreateUserDialog = ({
  open,
  onClose,
  onCreateUser,
}: CreateUserDialogProps) => {
  const [formData, setFormData] = useState<NewUser>({
    firstname: '',
    lastname: '',
    dateOfBirth: null,
  });

  const [userValidation, setUserValidation] = useState<UserValidation>({});
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>({
    status: 'idle',
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      setUploadState({
        status: 'error',
        message: `Only ${ALLOWED_FILE_EXTENSIONS.join(', ')} files are allowed`,
      });
      return;
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setUploadState({
        status: 'error',
        message: `File size exceeds 5MB limit (${(file.size / 1024 / 1024).toFixed(2)}MB)`,
      });
      return;
    }

    setSelectedFile(file);
    setUploadState({ status: 'idle' });
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadState({ status: 'uploading', progress: 0 });

    let presignData: PresignResponse;
    try {
      // Get presigned URL from backend
      presignData = await getPresignedUrl(selectedFile.name, selectedFile.type);

      // Upload file to S3
      await uploadToS3(presignData.uploadUrl, selectedFile, (progress) => {
        setUploadState({ status: 'uploading', progress });
      });
      setUploadState({ status: 'success', uploadId: presignData.uploadId });
      await processUpload(presignData.uploadId);
    } catch (error) {
      setUploadState({
        status: 'error',
        message: 'Upload failed.',
      });
      return;
    }
  };

  const processUpload = async (uploadId: string) => {
    try {
      // After successful upload, trigger backend processing for the document
      const resp = await processDocument(uploadId);

      if (!resp.success) {
        setUploadState({
          status: 'error',
          message: 'Failed to process document.',
        });
        return;
      }

      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      const user_data: NewUser = resp.payload;
      let warnMsg = ['Failed to identify information for: '];

      if (!user_data.firstname) {
        warnMsg.push('first name');
      }
      if (!user_data.lastname) {
        warnMsg.push('last name');
      }
      if (!user_data.dateOfBirth) {
        warnMsg.push('date of birth');
      } else {
        user_data.dateOfBirth = dayjs(user_data.dateOfBirth);
      }

      if (warnMsg.length > 1) {
        setUploadState({
          status: 'warning',
          message: warnMsg.shift() + warnMsg.join(', '),
        });
      } else {
        setUploadState({ status: 'idle' });
      }

      setFormData(user_data);
      setUserValidation(validateNewUser(user_data));
    } catch (err) {
      setUploadState({
        status: 'error',
        message: 'Failed to process document.',
      });
    }
  };

  const handleDialogClose = () => {
    setFormData({ firstname: '', lastname: '', dateOfBirth: null });
    setSelectedFile(null);
    setUploadState({ status: 'idle' });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onClose();
  };

  const handleSubmit = async (e: React.SubmitEvent) => {
    e.preventDefault();

    if (!userValidation.ok) {
      return;
    }

    if (!(await onCreateUser(formData))) {
      return; // invalid or failed request
    }
    setFormData({ firstname: '', lastname: '', dateOfBirth: null });
    setSelectedFile(null);
    setUploadState({ status: 'idle' });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleDialogClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create User</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          <TextField
            fullWidth
            label="First name"
            value={formData.firstname}
            onChange={(e) => {
              const newData = { ...formData, firstname: e.target.value };
              setFormData(newData);
              setUserValidation(validateNewUser(newData));
            }}
            helperText={userValidation.firstname || ' '}
            required
            sx={{ mb: 2 }}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <TextField
            fullWidth
            label="Last name"
            value={formData.lastname}
            onChange={(e) => {
              const newData = { ...formData, lastname: e.target.value };
              setFormData(newData);
              setUserValidation(validateNewUser(newData));
            }}
            helperText={userValidation.lastname || ' '}
            required
            sx={{ mb: 2 }}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker
              sx={{ width: '100%' }}
              label="Date of birth"
              format="DD/MM/YYYY"
              value={formData.dateOfBirth}
              maxDate={dayjs().subtract(MIN_USER_AGE, 'year')}
              onChange={(newValue) => {
                const newData = { ...formData, dateOfBirth: newValue };
                setFormData(newData);
                setUserValidation(validateNewUser(newData));
              }}
              slotProps={{
                textField: {
                  required: true,
                  error: false,
                  InputLabelProps: { shrink: true },
                  helperText: userValidation.dateOfBirth || ' ',
                },
              }}
            />
          </LocalizationProvider>

          {/* Document Upload Section */}
          <Box sx={{ mt: 3, mb: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Upload Document (Optional)
            </Typography>
            <input
              ref={fileInputRef}
              type="file"
              accept={ALLOWED_FILE_EXTENSIONS.join(',')}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              id="document-upload-input"
            />
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <label htmlFor="document-upload-input">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                  disabled={uploadState.status === 'uploading'}
                >
                  Choose File
                </Button>
              </label>
              {selectedFile && (
                <>
                  <Typography variant="body2" sx={{ flex: 1 }}>
                    {selectedFile.name}
                  </Typography>
                  <Button
                    variant="contained"
                    onClick={handleUpload}
                    disabled={
                      uploadState.status === 'uploading' ||
                      uploadState.status === 'success'
                    }
                    size="small"
                  >
                    {uploadState.status === 'uploading' ? (
                      <CircularProgress size={20} color="inherit" />
                    ) : (
                      'Upload'
                    )}
                  </Button>
                </>
              )}
            </Box>

            {/* Upload Progress */}
            {uploadState.status === 'uploading' &&
              uploadState.progress !== undefined && (
                <Box sx={{ mt: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={uploadState.progress}
                  />
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ mt: 0.5 }}
                  >
                    {uploadState.progress}% uploaded
                  </Typography>
                </Box>
              )}

            {/* Success Message */}
            {uploadState.status === 'success' && (
              <Alert severity="success" sx={{ mt: 1 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    overflow: 'hidden',
                  }}
                >
                  <span>Document uploaded successfully: processing</span>
                  <CircularProgress size={16} />
                </Box>
              </Alert>
            )}

            {/* Error Message */}
            {(uploadState.status === 'error' ||
              uploadState.status === 'warning') &&
              uploadState.message && (
                <Alert severity={uploadState.status} sx={{ mt: 1 }}>
                  {uploadState.message}
                </Alert>
              )}

            {uploadState.status === 'idle' && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mt: 1 }}
              >
                Accepted formats: {ALLOWED_FILE_EXTENSIONS.join(', ')}. Max
                size: 5MB.
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={!validateNewUser(formData).ok}
          >
            Create
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
