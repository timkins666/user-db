import { useState } from 'react';
import {
  Container,
  Typography,
  Button,
  OutlinedInput,
  InputAdornment,
} from '@mui/material';
import { Add, PersonSearch } from '@mui/icons-material';
import { type User } from './types/user';
import { useUsers } from './hooks/useUsers';
import {
  UserTable,
  type SortField,
  type SortOrder,
} from './components/UserTable';
import { CreateUserDialog } from './components/CreateUserDialog';
import { DeleteUserDialog } from './components/DeleteUserDialog';

function App() {
  const { users, createUser, deleteUser } = useUsers();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [sortField, setSortField] = useState<SortField>('lastname');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [searchText, setSearchText] = useState<string>('');

  const handleSort = (field: SortField) => {
    const newOrder =
      sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
    setSortField(field);
    setSortOrder(newOrder);
  };

  const sortedUsers = users.sort((a, b) => {
    const aVal = a[sortField];
    const bVal = b[sortField];
    let modifier = sortOrder === 'asc' ? 1 : -1;
    return aVal < bVal ? -modifier : aVal > bVal ? modifier : 0;
  });

  const handleDeleteConfirm = () => {
    if (userToDelete) {
      deleteUser(userToDelete.id);
      setUserToDelete(null);
    }
  };

  return (
    <Container maxWidth='lg' sx={{ py: 4 }}>
      <Typography variant='h4' sx={{ mb: 4 }}>
        User Management
      </Typography>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <OutlinedInput
          id='user-search'
          endAdornment={
            <InputAdornment position='end'>
              <PersonSearch />
            </InputAdornment>
          }
          placeholder='search'
          value={searchText}
          onInput={(e) => setSearchText((e.target as HTMLInputElement).value)}
          size='small'
        />

        <Button
          variant='outlined'
          startIcon={<Add />}
          onClick={() => setShowCreateModal(true)}
        >
          Create New User
        </Button>
      </div>

      <UserTable
        users={sortedUsers}
        onDeleteUser={setUserToDelete}
        sortField={sortField}
        sortOrder={sortOrder}
        onSort={handleSort}
        searchText={searchText.toLowerCase()}
      />

      <CreateUserDialog
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreateUser={createUser}
      />

      <DeleteUserDialog
        user={userToDelete}
        onClose={() => setUserToDelete(null)}
        onConfirm={handleDeleteConfirm}
      />
    </Container>
  );
}

export default App;
