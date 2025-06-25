"use client";

import React, { useEffect, useRef, useCallback } from 'react';
import { motion } from 'motion/react';

interface VoiceWaveformProps {
  isActive: boolean;
  audioLevel: number;
  frequencyData?: Uint8Array | null;
  mode?: 'bars' | 'circle' | 'line' | 'orb';
  color?: string;
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

export function VoiceWaveform({
  isActive,
  audioLevel,
  frequencyData,
  mode = 'orb',
  color = '#3B82F6',
  size = 'medium',
  className = '',
}: VoiceWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);

  const sizeConfig = {
    small: { width: 60, height: 60, barCount: 12 },
    medium: { width: 100, height: 100, barCount: 20 },
    large: { width: 150, height: 150, barCount: 32 },
  };

  const config = sizeConfig[size];

  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = canvas;
    const centerX = width / 2;
    const centerY = height / 2;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Set drawing style
    ctx.fillStyle = color;
    ctx.strokeStyle = color;

    if (mode === 'orb') {
      // Pulsating orb mode (like ChatGPT)
      const baseRadius = Math.min(width, height) * 0.15;
      const pulseRadius = baseRadius + (audioLevel * 20);
      
      // Outer glow
      const gradient = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, pulseRadius * 2
      );
      gradient.addColorStop(0, color + '80');
      gradient.addColorStop(0.7, color + '20');
      gradient.addColorStop(1, color + '00');
      
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, pulseRadius * 2, 0, Math.PI * 2);
      ctx.fill();

      // Main orb
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
      ctx.fill();

      // Inner highlight
      const highlightGradient = ctx.createRadialGradient(
        centerX - pulseRadius * 0.3, centerY - pulseRadius * 0.3, 0,
        centerX, centerY, pulseRadius
      );
      highlightGradient.addColorStop(0, '#FFFFFF40');
      highlightGradient.addColorStop(1, '#FFFFFF00');
      
      ctx.fillStyle = highlightGradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
      ctx.fill();

    } else if (mode === 'circle') {
      // Circular bars (like Google Assistant)
      const radius = Math.min(width, height) * 0.3;
      const barWidth = 3;
      const barCount = config.barCount;

      for (let i = 0; i < barCount; i++) {
        const angle = (i / barCount) * Math.PI * 2;
        const dataIndex = frequencyData ? Math.floor(i * frequencyData.length / barCount) : i;
        const amplitude = frequencyData ? frequencyData[dataIndex] / 255 : audioLevel;
        
        const barHeight = (amplitude * 30) + 5;
        const x1 = centerX + Math.cos(angle) * radius;
        const y1 = centerY + Math.sin(angle) * radius;
        const x2 = centerX + Math.cos(angle) * (radius + barHeight);
        const y2 = centerY + Math.sin(angle) * (radius + barHeight);

        ctx.lineWidth = barWidth;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }

    } else if (mode === 'bars') {
      // Traditional frequency bars
      const barCount = config.barCount;
      const barWidth = width / barCount - 2;

      for (let i = 0; i < barCount; i++) {
        const dataIndex = frequencyData ? Math.floor(i * frequencyData.length / barCount) : i;
        const amplitude = frequencyData ? frequencyData[dataIndex] / 255 : Math.random() * audioLevel;
        
        const barHeight = amplitude * height * 0.8;
        const x = i * (barWidth + 2);
        const y = height - barHeight;

        ctx.fillRect(x, y, barWidth, barHeight);
      }

    } else if (mode === 'line') {
      // Waveform line
      const points = 64;
      const step = width / points;

      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();

      for (let i = 0; i < points; i++) {
        const dataIndex = frequencyData ? Math.floor(i * frequencyData.length / points) : i;
        const amplitude = frequencyData ? frequencyData[dataIndex] / 255 : Math.sin(i * 0.1) * audioLevel;
        
        const x = i * step;
        const y = centerY + (amplitude - 0.5) * height * 0.6;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      ctx.stroke();
    }
  }, [audioLevel, frequencyData, mode, color, config]);

  useEffect(() => {
    if (isActive) {
      const animate = () => {
        drawWaveform();
        animationFrameRef.current = requestAnimationFrame(animate);
      };
      animate();
    } else {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      // Draw static state
      drawWaveform();
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isActive, drawWaveform]);

  return (
    <motion.div
      className={`flex items-center justify-center ${className}`}
      animate={{
        scale: isActive ? [1, 1.05, 1] : 1,
        opacity: isActive ? [0.8, 1, 0.8] : 0.6,
      }}
      transition={{
        duration: isActive ? 2 : 0.3,
        repeat: isActive ? Infinity : 0,
        ease: "easeInOut",
      }}
    >
      <canvas
        ref={canvasRef}
        width={config.width}
        height={config.height}
        className="rounded-full"
        style={{
          filter: isActive ? 'drop-shadow(0 0 10px rgba(59, 130, 246, 0.5))' : 'none',
        }}
      />
    </motion.div>
  );
}

// Simple pulsating dot for minimal UI
export function VoicePulse({
  isActive,
  size = 'medium',
  color = '#3B82F6',
  className = '',
}: {
  isActive: boolean;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
}) {
  const sizeClasses = {
    small: 'w-3 h-3',
    medium: 'w-4 h-4',
    large: 'w-6 h-6',
  };

  return (
    <motion.div
      className={`${sizeClasses[size]} rounded-full ${className}`}
      style={{ backgroundColor: color }}
      animate={{
        scale: isActive ? [1, 1.5, 1] : 1,
        opacity: isActive ? [0.6, 1, 0.6] : 0.4,
      }}
      transition={{
        duration: isActive ? 1.5 : 0.3,
        repeat: isActive ? Infinity : 0,
        ease: "easeInOut",
      }}
    />
  );
}