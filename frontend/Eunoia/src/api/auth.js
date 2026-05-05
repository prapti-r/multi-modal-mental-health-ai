import client from './client';

export const register     = (data) => client.post('/auth/register',   data);
export const verifyOtp    = (data) => client.post('/auth/verify-otp', data);
export const resendOtp    = (data) => client.post('/auth/resend-otp', data);
export const login        = (data) => client.post('/auth/login',      data);
export const logout       = ()     => client.post('/auth/logout');
export const getProfile   = ()     => client.get('/user/profile');
export const updateProfile = (data) => client.patch('/user/profile',  data);
export const getSettings  = ()     => client.get('/user/settings');
export const updateSettings = (data) => client.put('/user/settings',  data);
export const changePassword = (data) => client.put('/user/change-password', data);
export const deleteAccount  = ()     => client.delete('/user/account');