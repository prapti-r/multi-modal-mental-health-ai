import client from './client';
import { Platform } from 'react-native';

//  Sessions 

export const createSession = () => client.post('/chat/session');

export const listSessions = (page = 1, pageSize = 20) =>
  client.get('/chat/sessions', { params: { page, page_size: pageSize } });

// Text message 

export const sendTextMessage = (sessionId, content) =>
  client.post('/chat/message', { session_id: sessionId, content });

//  MIME normalisation 
// Maps what expo-av/ImagePicker actually produces → what the backend accepts.
// Backend ALLOWED_MIME_TYPES: video/mp4 | audio/wav | audio/mpeg
const normaliseMime = (rawMime = '', uri = '') => {
  // Video is always mp4 regardless of what the picker says
  if (
    rawMime.includes('video') ||
    rawMime.includes('quicktime') ||
    uri.endsWith('.mp4') ||
    uri.endsWith('.mov')
  ) {
    return 'video/mp4';
  }

  // Audio: map all variants to audio/mpeg (backend-accepted)
  // expo-av Android → audio/3gp or audio/x-m4a
  // expo-av iOS     → audio/x-m4a or audio/mp4
  if (
    rawMime.includes('3gp')  ||
    rawMime.includes('m4a')  ||
    rawMime.includes('aac')  ||
    rawMime.includes('mp4')  ||  // audio/mp4 ≠ video/mp4
    rawMime.includes('mpeg') ||
    rawMime.includes('mp3')  ||
    uri.endsWith('.3gp')     ||
    uri.endsWith('.m4a')     ||
    uri.endsWith('.aac')
  ) return 'audio/mpeg';

  if (rawMime.includes('wav') || uri.endsWith('.wav')) return 'audio/wav';

  // Unknown — default to audio/mpeg (Whisper can handle most formats via ffmpeg)
  return 'audio/mpeg';
};

// Media message — multipart/form-data 

export const sendMediaMessage = async (sessionId, fileUri, rawMimeType) => {
  // Normalise MIME before sending — prevents 422 from backend validation
  const mimeType = normaliseMime(rawMimeType, fileUri);

  const ext =  
  mimeType.includes('quicktime')? 'mov'
  : mimeType === 'video/mp4' ? 'mp4'
            : mimeType === 'audio/wav' ? 'wav'
            : 'mp3';

  const filename = `upload_${Date.now()}.${ext}`;

  // On iOS, strip the file:// prefix — React Native's fetch handles it,
  // but some Axios versions need the raw path
  const uri = Platform.OS === 'ios' ? fileUri.replace('file://', '') : fileUri;

  const body = new FormData();
  body.append('session_id', sessionId.toString().replace(/"/g, ''));
  body.append('file', {
    uri,
    name: filename, 
    type: mimeType,   
  });

  return client.post('/chat/message/media', body, {
    headers: { 'Accept': 'application/json',
      'Content-Type': 'multipart/form-data',
    },
    timeout: 90000,   // media processing takes longer — Whisper can be slow
  });
};

//  Message history (cursor-based) 

export const getMessages = (sessionId, limit = 20, cursor = null) =>
  client.get(`/chat/sessions/${sessionId}/messages`, {
    params: { limit, ...(cursor ? { cursor } : {}) },
  });