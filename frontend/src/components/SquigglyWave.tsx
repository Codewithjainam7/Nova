import React, { useRef, useState, useCallback } from 'react';
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
  width = 484,
  onSeek
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragProgress, setDragProgress] = useState<number | null>(null);

  const effectiveProgress = isDragging && dragProgress !== null
    ? dragProgress
    : Math.max(0, Math.min(1, progress));

  const clampedProgress = Math.max(0, Math.min(1, effectiveProgress));
  const playedWidth = Math.max(0, Math.min(width, clampedProgress * width));

  const height = 18;
  const midY = height / 2;
  const wavelength = 16;
  const amplitude = 3.2;

  // Generate continuous sine wave path across the entire width + 2 extra cycles for traveling animation
  const numCycles = Math.ceil((width + wavelength * 2) / wavelength) + 1;
  let fullWavePath = `M -${wavelength} ${midY}`;
  for (let i = 0; i < numCycles; i++) {
    const x0 = (i - 1) * wavelength;
    const xQuarter = x0 + wavelength / 4;
    const xMid = x0 + wavelength / 2;
    const xThreeQuarter = x0 + (wavelength * 3) / 4;
    const xEnd = x0 + wavelength;
    // Cubic Bézier sine curve approximation for silky smooth harmonics
    fullWavePath += ` C ${xQuarter} ${midY - amplitude * 1.3}, ${xMid - wavelength / 8} ${midY - amplitude * 1.3}, ${xMid} ${midY}`;
    fullWavePath += ` C ${xThreeQuarter} ${midY + amplitude * 1.3}, ${xEnd - wavelength / 8} ${midY + amplitude * 1.3}, ${xEnd} ${midY}`;
  }

  const computeProgressFromClientX = useCallback((clientX: number) => {
    if (!containerRef.current) return 0;
    const rect = containerRef.current.getBoundingClientRect();
    const offsetX = Math.max(0, Math.min(rect.width, clientX - rect.left));
    return rect.width > 0 ? offsetX / rect.width : 0;
  }, []);

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.stopPropagation();
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {}
    setIsDragging(true);
    const newProg = computeProgressFromClientX(e.clientX);
    setDragProgress(newProg);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    e.stopPropagation();
    const newProg = computeProgressFromClientX(e.clientX);
    setDragProgress(newProg);
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    e.stopPropagation();
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {}
    const finalProg = computeProgressFromClientX(e.clientX);
    setIsDragging(false);
    setDragProgress(null);
    if (onSeek) {
      onSeek(finalProg);
    }
  };

  const handlePointerCancel = () => {
    setIsDragging(false);
    setDragProgress(null);
  };

  return (
    <div
      ref={containerRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerCancel}
      className="relative w-full h-[18px] flex items-center select-none group cursor-pointer"
      title="Click or drag to seek track"
      style={{ touchAction: 'none' }}
    >
      <svg
        width={width}
        height={height}
        className="overflow-visible w-full h-full"
        viewBox={`0 0 ${width} ${height}`}
      >
        <defs>
          <clipPath id="squiggly-played-clip">
            <rect x={0} y={0} width={playedWidth} height={height} />
          </clipPath>
        </defs>

        {/* Unplayed Flat Line (Starts exactly at playedWidth with zero overlap) */}
        <line
          x1={Math.min(width, playedWidth + 1)}
          y1={midY}
          x2={width}
          y2={midY}
          stroke="rgba(255, 255, 255, 0.16)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* Played Squiggly Wave: Clipped exactly at playedWidth */}
        {playedWidth > 0 && (
          <g clipPath="url(#squiggly-played-clip)">
            <motion.path
              d={fullWavePath}
              fill="none"
              stroke={color}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              animate={isPlaying ? {
                x: [0, wavelength]
              } : { x: 0 }}
              transition={{
                x: {
                  repeat: Infinity,
                  duration: 1.2,
                  ease: "linear"
                }
              }}
            />
          </g>
        )}

        {/* Scrubber White Line Thumb: Centered exactly at playedWidth */}
        {playedWidth > 0 && playedWidth < width && (
          <line
            x1={playedWidth}
            y1={midY - 6}
            x2={playedWidth}
            y2={midY + 6}
            stroke="#ffffff"
            strokeWidth="3.5"
            strokeLinecap="round"
            className="transition-transform group-hover:scale-y-110"
            style={{
              filter: "drop-shadow(0 0 3px rgba(255, 255, 255, 0.8))"
            }}
          />
        )}
      </svg>
    </div>
  );
};
