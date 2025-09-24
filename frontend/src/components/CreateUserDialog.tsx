import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import {
  type NewUser,
  type UserValidation,
  validateNewUser,
} from '../types/user';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import { MIN_USER_AGE } from '../types/constants';

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!userValidation.ok) {
      return;
    }

    if (!(await onCreateUser(formData))) {
      return; // invalid or failed request
    }
    setFormData({ firstname: '', lastname: '', dateOfBirth: null });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth='sm' fullWidth>
      <DialogTitle>Create New User</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          <TextField
            fullWidth
            label='First name'
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
            label='Last name'
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
              label='Date of birth'
              format='DD/MM/YYYY'
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
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type='submit'
            variant='contained'
            disabled={!validateNewUser(formData).ok}
          >
            Create
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
