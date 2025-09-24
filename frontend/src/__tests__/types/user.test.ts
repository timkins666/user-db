import dayjs from 'dayjs';
import { validateNewUser, type NewUser } from '../../types/user';

const validData: NewUser = {
  firstname: 'Alvin',
  lastname: 'Simon-Théodore',
  dateOfBirth: dayjs('1980-01-01'),
};

describe('validateNewUser', () => {
  test('valid new user data', () => {
    const result = validateNewUser(validData);

    expect(result.ok).toBe(true);
    expect(result.firstname).toBe(undefined);
    expect(result.lastname).toBe(undefined);
    expect(result.dateOfBirth).toBe(undefined);
  });

  test('empty firstname', () => {
    const result = validateNewUser({ ...validData, firstname: '' });

    expect(result.ok).toBe(false);
    expect(result.firstname).toBe(undefined);
    expect(result.lastname).toBe(undefined);
    expect(result.dateOfBirth).toBe(undefined);
  });
  test('empty lastname', () => {
    const result = validateNewUser({ ...validData, lastname: '' });

    expect(result.ok).toBe(false);
    expect(result.firstname).toBe(undefined);
    expect(result.lastname).toBe(undefined);
    expect(result.dateOfBirth).toBe(undefined);
  });
  test('bad chars firstname', () => {
    const result = validateNewUser({ ...validData, firstname: 'B1lly' });

    expect(result.ok).toBe(false);
    expect(result.firstname).toBe('Invalid first name');
    expect(result.lastname).toBe(undefined);
    expect(result.dateOfBirth).toBe(undefined);
  });
  test('bad chars lastname', () => {
    const result = validateNewUser({ ...validData, lastname: 'B_lly' });

    expect(result.ok).toBe(false);
    expect(result.firstname).toBe(undefined);
    expect(result.lastname).toBe('Invalid last name');
    expect(result.dateOfBirth).toBe(undefined);
  });
  test('dob oldest ok', () => {
    const result = validateNewUser({
      ...validData,
      dateOfBirth: dayjs('1900-01-01'),
    });

    expect(result.ok).toBe(true);
    expect(result.firstname).toBe(undefined);
    expect(result.lastname).toBe(undefined);
    expect(result.dateOfBirth).toBe(undefined);
  });
  test('dob to old', () => {
    const result = validateNewUser({
      ...validData,
      dateOfBirth: dayjs('1899-12-31'),
    });

    expect(result.ok).toBe(false);
    expect(result.firstname).toBe(undefined);
    expect(result.lastname).toBe(undefined);
    expect(result.dateOfBirth).toBe('Invalid date');
  });
  test('dob too young', () => {
    const result = validateNewUser({
      ...validData,
      dateOfBirth: dayjs().subtract(1, 'day'),
    });

    expect(result.ok).toBe(false);
    expect(result.firstname).toBe(undefined);
    expect(result.lastname).toBe(undefined);
    expect(result.dateOfBirth).toBe('Invalid date');
  });
  test('dob unset', () => {
    const result = validateNewUser({
      ...validData,
      dateOfBirth: null,
    });

    expect(result.ok).toBe(false);
    expect(result.firstname).toBe(undefined);
    expect(result.lastname).toBe(undefined);
    expect(result.dateOfBirth).toBe(undefined);
  });
  test('all bad', () => {
    const result = validateNewUser({
      firstname: '3',
      lastname: '_',
      dateOfBirth: dayjs(),
    });

    expect(result.ok).toBe(false);
    expect(result.firstname).toBe('Invalid first name');
    expect(result.lastname).toBe('Invalid last name');
    expect(result.dateOfBirth).toBe('Invalid date');
  });
  test('all unset', () => {
    const result = validateNewUser({
      firstname: '',
      lastname: '',
      dateOfBirth: null,
    });

    expect(result.ok).toBe(false);
    expect(result.firstname).toBe(undefined);
    expect(result.lastname).toBe(undefined);
    expect(result.dateOfBirth).toBe(undefined);
  });
});
