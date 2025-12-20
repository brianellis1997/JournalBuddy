'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';

export type VoiceChatState = 'disconnected' | 'connecting' | 'idle' | 'listening' | 'thinking' | 'speaking';
export type AvatarEmotion = 'neutral' | 'happy' | 'warm' | 'concerned' | 'curious' | 'encouraging' | 'celebrating';

interface VoiceChatMessage {
  type: string;
  data?: Record<string, unknown>;
}

export interface ToolCall {
  tool: string;
  status: 'start' | 'done';
  timestamp: Date;
}

interface UseVoiceChatOptions {
  journalType?: 'morning' | 'evening';
  onTranscript?: (text: string, isFinal: boolean) => void;
  onAssistantText?: (text: string, isFinal: boolean) => void;
  onStateChange?: (state: VoiceChatState) => void;
  onError?: (error: string) => void;
  onConversationEnd?: () => void;
  onToolCall?: (toolCall: ToolCall) => void;
  onEmotionChange?: (emotion: AvatarEmotion) => void;
}

export function useVoiceChat(options: UseVoiceChatOptions = {}) {
  const { journalType, onTranscript, onAssistantText, onStateChange, onError, onConversationEnd, onToolCall, onEmotionChange } = options;
  const { token } = useAuthStore();

  const [state, setState] = useState<VoiceChatState>('disconnected');
  const [isConnected, setIsConnected] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [assistantText, setAssistantText] = useState('');
  const [conversationEnded, setConversationEnded] = useState(false);
  const [activeTools, setActiveTools] = useState<ToolCall[]>([]);
  const [emotion, setEmotion] = useState<AvatarEmotion>('neutral');

  const [amplitude, setAmplitude] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const nextPlayTimeRef = useRef(0);
  const inputAudioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

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
    if (isPlayingRef.current) return;

    isPlayingRef.current = true;

    while (audioQueueRef.current.length > 0) {
      const chunk = audioQueueRef.current.shift();
      if (chunk) {
        await playAudioChunk(chunk);
      }
    }

    isPlayingRef.current = false;

    if (audioQueueRef.current.length > 0) {
      processAudioQueue();
    }
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

  const updateAmplitude = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    const sum = dataArray.reduce((acc, val) => acc + val, 0);
    const avg = sum / dataArray.length;
    const normalizedAmplitude = Math.min(avg / 128, 1);

    setAmplitude(normalizedAmplitude);
    animationFrameRef.current = requestAnimationFrame(updateAmplitude);
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
          setCurrentTranscript(transcript);
          onTranscript?.(transcript, false);
          updateState('listening');
          break;

        case 'user_transcript':
          const finalText = message.data?.text as string || '';
          if (finalText.trim()) {
            onTranscript?.(finalText, true);
          }
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
          console.log('[VoiceChat] assistant_text received:', { text: text.substring(0, 50), isTextFinal });
          if (!isTextFinal && text) {
            setAssistantText(prev => {
              const newText = prev + text;
              console.log('[VoiceChat] assistantText updated:', newText.substring(0, 50));
              return newText;
            });
            onAssistantText?.(text, false);
          } else if (isTextFinal) {
            console.log('[VoiceChat] is_final received, calling onAssistantText');
            onAssistantText?.('', true);
            setAssistantText('');
          }
          break;

        case 'assistant_done':
          setAssistantText('');
          updateState('idle');
          break;

        case 'interrupted':
          stopAudioPlayback();
          updateState('listening');
          break;

        case 'error':
          onError?.(message.data?.message as string || 'Unknown error');
          break;

        case 'conversation_ended':
          setConversationEnded(true);
          onConversationEnd?.();
          break;

        case 'tool_call':
          const toolName = message.data?.tool as string;
          const toolStatus = message.data?.status as 'start' | 'done';
          const toolCall: ToolCall = {
            tool: toolName,
            status: toolStatus,
            timestamp: new Date(),
          };
          if (toolStatus === 'start') {
            setActiveTools(prev => [...prev, toolCall]);
          } else {
            setActiveTools(prev => prev.filter(t => t.tool !== toolName || t.status !== 'start'));
          }
          onToolCall?.(toolCall);
          break;

        case 'emotion':
          const newEmotion = message.data?.emotion as AvatarEmotion;
          if (newEmotion) {
            setEmotion(newEmotion);
            onEmotionChange?.(newEmotion);
          }
          break;

        case 'pong':
          break;
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  }, [onTranscript, onAssistantText, onError, onConversationEnd, onToolCall, onEmotionChange, updateState, processAudioQueue, stopAudioPlayback]);

  const connect = useCallback(async () => {
    if (!token) {
      onError?.('Not authenticated');
      return;
    }

    updateState('connecting');

    let wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/v1/voice/chat?token=${token}`;
    if (journalType) {
      wsUrl += `&journal_type=${journalType}`;
    }

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
  }, [token, journalType, handleWebSocketMessage, onError, updateState]);

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

      const inputAudioContext = new AudioContext();
      inputAudioContextRef.current = inputAudioContext;
      const source = inputAudioContext.createMediaStreamSource(stream);
      const analyser = inputAudioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      animationFrameRef.current = requestAnimationFrame(updateAmplitude);

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
  }, [onError, updateState, updateAmplitude]);

  const stopRecording = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (inputAudioContextRef.current) {
      inputAudioContextRef.current.close();
      inputAudioContextRef.current = null;
    }
    analyserRef.current = null;
    setAmplitude(0);

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
    amplitude,
    conversationEnded,
    activeTools,
    emotion,
    start,
    disconnect,
    interrupt,
    sendMessage,
  };
}
