'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';

export type VoiceChatState = 'disconnected' | 'connecting' | 'idle' | 'listening' | 'thinking' | 'speaking';

interface VoiceChatMessage {
  type: string;
  data?: Record<string, unknown>;
}

interface UseVoiceChatOptions {
  onTranscript?: (text: string, isFinal: boolean) => void;
  onAssistantText?: (text: string, isFinal: boolean) => void;
  onStateChange?: (state: VoiceChatState) => void;
  onError?: (error: string) => void;
}

export function useVoiceChat(options: UseVoiceChatOptions = {}) {
  const { onTranscript, onAssistantText, onStateChange, onError } = options;
  const { token } = useAuthStore();

  const [state, setState] = useState<VoiceChatState>('disconnected');
  const [isConnected, setIsConnected] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [assistantText, setAssistantText] = useState('');

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const nextPlayTimeRef = useRef(0);

  const updateState = useCallback((newState: VoiceChatState) => {
    setState(newState);
    onStateChange?.(newState);
  }, [onStateChange]);

  const playAudioChunk = useCallback(async (audioData: ArrayBuffer) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext({ sampleRate: 24000 });
    }

    const ctx = audioContextRef.current;

    const pcmData = new Int16Array(audioData);
    const floatData = new Float32Array(pcmData.length);
    for (let i = 0; i < pcmData.length; i++) {
      floatData[i] = pcmData[i] / 32768;
    }

    const audioBuffer = ctx.createBuffer(1, floatData.length, 24000);
    audioBuffer.getChannelData(0).set(floatData);

    const source = ctx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(ctx.destination);

    const currentTime = ctx.currentTime;
    const startTime = Math.max(currentTime, nextPlayTimeRef.current);
    source.start(startTime);
    nextPlayTimeRef.current = startTime + audioBuffer.duration;
  }, []);

  const processAudioQueue = useCallback(async () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;

    isPlayingRef.current = true;

    while (audioQueueRef.current.length > 0) {
      const chunk = audioQueueRef.current.shift();
      if (chunk) {
        await playAudioChunk(chunk);
      }
    }

    isPlayingRef.current = false;
  }, [playAudioChunk]);

  const stopAudioPlayback = useCallback(() => {
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    nextPlayTimeRef.current = 0;

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((type: string, data?: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...data }));
    }
  }, []);

  const handleWebSocketMessage = useCallback(async (event: MessageEvent) => {
    if (event.data instanceof Blob) {
      const arrayBuffer = await event.data.arrayBuffer();
      audioQueueRef.current.push(arrayBuffer);
      processAudioQueue();
      return;
    }

    try {
      const message: VoiceChatMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'connected':
          setIsConnected(true);
          break;

        case 'ready':
          updateState('idle');
          break;

        case 'interim_transcript':
          const transcript = message.data?.text as string || '';
          const isFinal = message.data?.is_final as boolean || false;
          setCurrentTranscript(transcript);
          onTranscript?.(transcript, isFinal);
          if (!isFinal) {
            updateState('listening');
          }
          break;

        case 'user_transcript':
          setCurrentTranscript('');
          break;

        case 'assistant_thinking':
          updateState('thinking');
          setAssistantText('');
          break;

        case 'assistant_speaking':
          updateState('speaking');
          break;

        case 'assistant_text':
          const text = message.data?.text as string || '';
          const isTextFinal = message.data?.is_final as boolean || false;
          if (!isTextFinal && text) {
            setAssistantText(prev => prev + text);
            onAssistantText?.(text, false);
          } else if (isTextFinal) {
            onAssistantText?.('', true);
          }
          break;

        case 'assistant_done':
          updateState('idle');
          break;

        case 'interrupted':
          stopAudioPlayback();
          updateState('listening');
          break;

        case 'error':
          onError?.(message.data?.message as string || 'Unknown error');
          break;

        case 'pong':
          break;
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  }, [onTranscript, onAssistantText, onError, updateState, processAudioQueue, stopAudioPlayback]);

  const connect = useCallback(async () => {
    if (!token) {
      onError?.('Not authenticated');
      return;
    }

    updateState('connecting');

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/v1/voice/chat?token=${token}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = handleWebSocketMessage;

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.('Connection error');
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      setIsConnected(false);
      updateState('disconnected');
      cleanup();
    };
  }, [token, handleWebSocketMessage, onError, updateState]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          const arrayBuffer = await event.data.arrayBuffer();
          wsRef.current.send(arrayBuffer);
        }
      };

      mediaRecorder.start(100);
      updateState('listening');
    } catch (err) {
      console.error('Failed to start recording:', err);
      onError?.('Failed to access microphone');
    }
  }, [onError, updateState]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
  }, []);

  const interrupt = useCallback(() => {
    sendMessage('interrupt');
    stopAudioPlayback();
  }, [sendMessage, stopAudioPlayback]);

  const cleanup = useCallback(() => {
    stopRecording();
    stopAudioPlayback();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, [stopRecording, stopAudioPlayback]);

  const disconnect = useCallback(() => {
    cleanup();
    updateState('disconnected');
  }, [cleanup, updateState]);

  const start = useCallback(async () => {
    await connect();
    await startRecording();
  }, [connect, startRecording]);

  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      sendMessage('ping');
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [isConnected, sendMessage]);

  return {
    state,
    isConnected,
    currentTranscript,
    assistantText,
    start,
    disconnect,
    interrupt,
    sendMessage,
  };
}
