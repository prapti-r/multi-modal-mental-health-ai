import client from './client';

export const getWeeklyReport = () => client.get('/reports/weekly');
export const getTherapists   = () => client.get('/therapists');