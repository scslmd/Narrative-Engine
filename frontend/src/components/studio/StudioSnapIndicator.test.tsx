import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { detectSnapZone, StudioSnapIndicator } from './StudioSnapIndicator';

describe('detectSnapZone', () => {
  it('detects left-edge snap zone', () => {
    const result = detectSnapZone('panel-1', 10, 100, 200, 300, 1200, 800);
    expect(result).not.toBeNull();
    expect(result!.id).toBe('left-edge');
    expect(result!.position.x).toBe(16);
  });

  it('detects right-edge snap zone', () => {
    const result = detectSnapZone('panel-1', 1050, 100, 200, 300, 1200, 800);
    expect(result).not.toBeNull();
    expect(result!.id).toBe('right-edge');
  });

  it('detects top snap zone', () => {
    const result = detectSnapZone('panel-1', 500, 10, 200, 300, 1200, 800);
    expect(result).not.toBeNull();
    expect(result!.id).toBe('top');
    expect(result!.position.y).toBe(40);
  });

  it('detects bottom snap zone', () => {
    const result = detectSnapZone('panel-1', 500, 650, 200, 300, 1200, 800);
    expect(result).not.toBeNull();
    expect(result!.id).toBe('bottom');
  });

  it('detects center snap zone', () => {
    const result = detectSnapZone('panel-1', 500, 250, 200, 300, 1200, 800);
    expect(result).not.toBeNull();
    expect(result!.id).toBe('center');
  });

  it('returns null when no snap zone is near', () => {
    const result = detectSnapZone('panel-1', 500, 400, 200, 300, 1200, 800);
    expect(result).toBeNull();
  });
});

describe('StudioSnapIndicator', () => {
  it('renders nothing when no snap zone', () => {
    const { container } = render(
      <StudioSnapIndicator snapZone={null} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders center snap indicator', () => {
    render(
      <StudioSnapIndicator snapZone={{ id: 'center', position: { x: 500, y: 300 } }} />
    );
    const indicator = document.querySelector('[class*="rounded-full"]');
    expect(indicator).toBeInTheDocument();
  });

  it('renders edge snap indicator', () => {
    render(
      <StudioSnapIndicator snapZone={{ id: 'left-edge', position: { x: 16, y: 40 } }} />
    );
    const indicator = document.querySelector('[class*="absolute"]');
    expect(indicator).toBeInTheDocument();
  });
});
