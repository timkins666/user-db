import dayjs, { type Dayjs } from 'dayjs';
import { MIN_USER_AGE } from './constants';

export interface UserBase {
  firstname: string;
  lastname: string;
}

export interface NewUser extends UserBase {
  dateOfBirth: Dayjs | null;
}

export interface User extends UserBase {
  id: string;
  dateOfBirth: Dayjs;
  age: number;
}

export interface UserValidation {
  ok?: boolean;
  firstname?: string;
  lastname?: string;
  dateOfBirth?: string;
}

export const validateNewUser = (userData: NewUser): UserValidation => {
  const name_validator = /^[A-Za-zÀ-ÖØ-öø-ÿ- ]{1,100}$/;
  const results: UserValidation = { ok: true };

  if (!userData.firstname.match(name_validator)) {
    results.ok = false;
    results.firstname = userData.firstname ? 'Invalid first name' : undefined;
  }
  if (!userData.lastname.match(name_validator)) {
    results.ok = false;
    results.lastname = userData.lastname ? 'Invalid last name' : undefined;
  }
  if (
    !userData.dateOfBirth ||
    dayjs().diff(userData.dateOfBirth, 'year') < MIN_USER_AGE ||
    userData.dateOfBirth.isBefore(dayjs('1900-01-01'))
  ) {
    results.ok = false;
    results.dateOfBirth = userData.dateOfBirth ? 'Invalid date' : undefined;
  }

  return results;
};
