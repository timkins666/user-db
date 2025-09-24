import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
} from '@mui/material';
import { type User } from '../types/user';

interface DeleteUserDialogProps {
  user: User | null;
  onClose: () => void;
  onConfirm: () => void;
}

export const DeleteUserDialog = ({
  user,
  onClose,
  onConfirm,
}: DeleteUserDialogProps) => {
  return (
    <Dialog open={!!user} onClose={onClose}>
      <DialogTitle>Confirm delete</DialogTitle>
      <DialogContent>
        <Typography sx={{ display: 'inline' }}>
          Are you sure you want to delete{' '}
        </Typography>
        <Box sx={{ fontWeight: 'bold' }} display='inline'>
          {user?.firstname} {user?.lastname}
        </Box>
        <Typography sx={{ display: 'inline' }}>?</Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onConfirm} color='error' variant='contained'>
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
};
