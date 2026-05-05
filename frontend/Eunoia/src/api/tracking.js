import client from './client';

//  Mood 
export const logMood      = (data)   => client.post('/mood/log',     data);
export const getMoodHistory = (page = 1, pageSize = 30) =>
  client.get('/mood/history', { params: { page, page_size: pageSize } });

//  Journal 
export const createJournal  = (data)   => client.post('/journal/entry', data);
export const getJournalHistory = (page = 1, pageSize = 20) =>
  client.get('/journal/history', { params: { page, page_size: pageSize } });

//  Assessments 
export const submitAssessment  = (data) => client.post('/assessments/submit',  data);
export const getAssessmentHistory = (page = 1, pageSize = 20) =>
  client.get('/assessments/history', { params: { page, page_size: pageSize } });