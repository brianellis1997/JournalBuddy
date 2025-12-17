'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { api } from '@/lib/api';

type RecordingState = 'idle' | 'recording' | 'processing';

interface UseVoiceRecordingReturn {
  isRecording: boolean;
  isProcessing: boolean;
  state: RecordingState;
  amplitude: number;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string | null>;
  cancelRecording: () => void;
  error: string | null;
}

export function useVoiceRecording(): UseVoiceRecordingReturn {
  const [state, setState] = useState<RecordingState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [amplitude, setAmplitude] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const cleanup = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    analyserRef.current = null;
    chunksRef.current = [];
    setAmplitude(0);
  }, []);

  const updateAmplitude = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    const sum = dataArray.reduce((acc, val) => acc + val, 0);
    const avg = sum / dataArray.length;
    const normalizedAmplitude = Math.min(avg / 128, 1);

    setAmplitude(normalizedAmplitude);

    if (state === 'recording') {
      animationFrameRef.current = requestAnimationFrame(updateAmplitude);
    }
  }, [state]);

  useEffect(() => {
    if (state === 'recording' && analyserRef.current) {
      animationFrameRef.current = requestAnimationFrame(updateAmplitude);
    }
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [state, updateAmplitude]);

  const startRecording = useCallback(async () => {
    setError(null);
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(100);
      setState('recording');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to access microphone. Please check permissions.'
      );
      cleanup();
    }
  }, [cleanup]);

  const stopRecording = useCallback(async (): Promise<string | null> => {
    if (!mediaRecorderRef.current || state !== 'recording') {
      return null;
    }

    setState('processing');

    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current!;

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        cleanup();

        try {
          const text = await api.transcribeAudio(audioBlob);
          setState('idle');
          resolve(text);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Transcription failed');
          setState('idle');
          resolve(null);
        }
      };

      mediaRecorder.stop();
    });
  }, [state, cleanup]);

  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    cleanup();
    setState('idle');
  }, [state, cleanup]);

  return {
    isRecording: state === 'recording',
    isProcessing: state === 'processing',
    state,
    amplitude,
    startRecording,
    stopRecording,
    cancelRecording,
    error,
  };
}
