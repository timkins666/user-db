import { render, screen, fireEvent } from '@testing-library/react';
import { UserTable } from '../../components/UserTable';
import { type User } from '../../types/user';
import dayjs from 'dayjs';

const mockUsers: User[] = [
  {
    id: '1',
    firstname: 'John',
    lastname: 'Doe',
    dateOfBirth: dayjs('1990-01-01'),
    age: 34,
  },
  {
    id: '2',
    firstname: 'Jane',
    lastname: 'Smith',
    dateOfBirth: dayjs('1985-05-15'),
    age: 39,
  },
];

const mockProps = {
  users: mockUsers,
  onDeleteUser: jest.fn(),
  sortField: 'firstname' as const,
  sortOrder: 'asc' as const,
  onSort: jest.fn(),
  searchText: '',
};

describe('UserTable', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders user data correctly', () => {
    render(<UserTable {...mockProps} />);

    expect(screen.getByText('John')).toBeInTheDocument();
    expect(screen.getByText('Doe')).toBeInTheDocument();
    expect(screen.getByText('01/01/1990')).toBeInTheDocument();

    expect(screen.getByText('Jane')).toBeInTheDocument();
    expect(screen.getByText('Smith')).toBeInTheDocument();
    expect(screen.getByText('15/05/1985')).toBeInTheDocument();

    expect(screen.getAllByTestId('DeleteIcon').length).toEqual(2);
  });

  test('renders user data correctly with search', () => {
    render(<UserTable {...{...mockProps, searchText: 'd'}} />);

    expect(screen.getByText('John')).toBeInTheDocument();
    expect(screen.getByText('Doe')).toBeInTheDocument();
    expect(screen.getByText('01/01/1990')).toBeInTheDocument();

    expect(screen.queryByText('Jane')).not.toBeInTheDocument();
    expect(screen.queryByText('Smith')).not.toBeInTheDocument();
    expect(screen.queryByText('15/05/1985')).not.toBeInTheDocument();

    expect(screen.getAllByTestId('DeleteIcon').length).toEqual(1);
  });

  test('calls onDeleteUser when delete button is clicked', () => {
    render(<UserTable {...mockProps} />);

    const deleteButtons = screen.getAllByTestId('DeleteIcon');
    fireEvent.click(deleteButtons[0]);

    expect(mockProps.onDeleteUser).toHaveBeenCalledWith(mockUsers[0]);
  });

  test('calls onSort when column header is clicked', () => {
    render(<UserTable {...mockProps} />);

    const firstNameHeader = screen.getByText('First Name');
    fireEvent.click(firstNameHeader);

    expect(mockProps.onSort).toHaveBeenCalledWith('firstname');
  });
});
