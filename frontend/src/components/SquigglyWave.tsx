import React, { useRef } from 'react';
import { motion } from 'framer-motion';

interface SquigglyWaveProps {
  progress: number; // 0 to 1
  isPlaying: boolean;
  color?: string;
  width?: number;
  onSeek?: (newProgress: number) => void;
}

export const SquigglyWave: React.FC<SquigglyWaveProps> = ({
  progress,
  isPlaying,
  color = '#f472b6',
  width = 460,
  onSeek
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const clampedProgress = Math.max(0, Math.min(1, progress));
  const playedWidth = Math.max(0, clampedProgress * width);

  // Generate smooth sine wave path for the played portion
  const wavelength = 16;
  const amplitude = 3.5;
  const height = 14;
  const midY = height / 2;

  let pathData = `M 0 ${midY}`;
  const numCycles = Math.ceil(playedWidth / wavelength);

  for (let i = 0; i < numCycles; i++) {
    const x0 = i * wavelength;
    const x1 = x0 + wavelength / 4;
    const xEnd = Math.min(playedWidth, (i + 1) * wavelength);

    if (xEnd <= playedWidth) {
      pathData += ` Q ${x1} ${midY - amplitude}, ${x0 + wavelength / 2} ${midY} T ${xEnd} ${midY}`;
    }
  }

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.stopPropagation();
    if (!onSeek || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const clickX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const newProgress = clickX / rect.width;
    onSeek(newProgress);
  };

  return (
    <div
      ref={containerRef}
      onPointerDown={handlePointerDown}
      className="relative w-full h-[14px] flex items-center select-none group cursor-pointer"
      title="Click or drag to seek track"
    >
      <svg
        width={width}
        height={height}
        className="overflow-visible w-full h-full"
        viewBox={`0 0 ${width} ${height}`}
      >
        {/* Unplayed Flat Line */}
        <line
          x1={playedWidth}
          y1={midY}
          x2={width}
          y2={midY}
          stroke="rgba(255, 255, 255, 0.18)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* Played Squiggly Sine Wave */}
        {playedWidth > 0 && (
          <motion.path
            d={pathData}
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            animate={isPlaying ? {
              opacity: [0.9, 1, 0.9]
            } : { opacity: 0.85 }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
          />
        )}

        {/* Vertical Scrubber Capsule Thumb */}
        <line
          x1={playedWidth}
          y1={midY - 5}
          x2={playedWidth}
          y2={midY + 5}
          stroke="#ffffff"
          strokeWidth="3.5"
          strokeLinecap="round"
          className="filter drop-shadow-[0_0_4px_rgba(255,255,255,0.7)]"
        />
      </svg>
    </div>
  );
};
