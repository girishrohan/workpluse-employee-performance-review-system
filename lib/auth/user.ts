import { createClient } from '@/lib/supabase/server';
import type { User, UserRole } from './types';

export async function createUser(
  email: string,
  passwordHash: string,
  role: UserRole,
  fullName: string
): Promise<User> {
  const supabase = await createClient();
  
  const { data, error } = await supabase
    .from('users')
    .insert({
      email,
      password_hash: passwordHash,
      role,
      full_name: fullName,
      employee_code: null,
    })
    .select()
    .single();

  if (error) {
    if (error.code === '23505') {
      throw new Error('User with this email already exists');
    }
    throw new Error(`Failed to create user: ${error.message}`);
  }

  return data;
}

export async function getUserByEmail(email: string): Promise<User | null> {
  const supabase = await createClient();
  
  const { data, error } = await supabase
    .from('users')
    .select('*')
    .eq('email', email.toLowerCase())
    .single();

  if (error) {
    if (error.code === 'PGRST116') return null; // Not found
    throw new Error(`Failed to get user: ${error.message}`);
  }

  return data;
}

export async function getUserById(id: string): Promise<User | null> {
  const supabase = await createClient();
  
  const { data, error } = await supabase
    .from('users')
    .select('*')
    .eq('id', id)
    .single();

  if (error) {
    if (error.code === 'PGRST116') return null;
    throw new Error(`Failed to get user: ${error.message}`);
  }

  return data;
}

export async function updateUserRole(userId: string, role: UserRole): Promise<void> {
  const supabase = await createClient();
  
  const { error } = await supabase
    .from('users')
    .update({ role, updated_at: new Date().toISOString() })
    .eq('id', userId);

  if (error) {
    throw new Error(`Failed to update user role: ${error.message}`);
  }
}

export async function seedDefaultAdmin(): Promise<void> {
  const { hashPassword } = await import('./password');
  
  const adminEmail = 'admin@workpulse.local';
  const adminPassword = 'Admin@WorkPulse2024';
  const adminName = 'Admin';
  
  const existing = await getUserByEmail(adminEmail);
  if (existing) {
    // Ensure admin has correct role
    if (existing.role !== 'admin') {
      await updateUserRole(existing.id, 'admin');
    }
    return;
  }
  
  const passwordHash = await hashPassword(adminPassword);
  await createUser(adminEmail, passwordHash, 'admin', adminName);
}