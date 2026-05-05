
import client from './client';

//  Sessions 
export const createSession  = ()     => client.post('/chat/session');
export const listSessions   = (page = 1, pageSize = 20) =>
  client.get('/chat/sessions', { params: { page, page_size: pageSize } });

//  Text message 
export const sendTextMessage = (sessionId, content) =>
  client.post('/chat/message', { session_id: sessionId, content });

//  Media message — multipart/form-data 
export const sendMediaMessage = async (sessionId, fileUri, mimeType) => {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('file', {
    uri:  fileUri,
    name: `upload.${mimeType === 'video/mp4' ? 'mp4' : mimeType.includes('wav') ? 'wav' : 'mp3'}`,
    type: mimeType,
  });
  return client.post('/chat/message/media', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30_000,   // media processing takes longer
  });
};

//  Message history 
export const getMessages = (sessionId, limit = 20, cursor = null) =>
  client.get(`/chat/sessions/${sessionId}/messages`, {
    params: { limit, ...(cursor ? { cursor } : {}) },
  });