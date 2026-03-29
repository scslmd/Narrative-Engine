/**
 * FE-026: Selection hook
 * 
 * React hook for managing text selections with keyboard shortcuts and mouse events.
 */

import { useCallback, useRef } from 'react';
import { useSelectionStore } from '../stores/selectionStore';
import type { SelectionRecord } from '../types/aids';
import { createSelectionRecord } from '../lib/selection';

interface UseSelectionOptions {
  projectId: string;
  sourceType: 'MANUSCRIPT' | 'DRAFT' | 'SUGGESTION';
  sourceId: string;
  sourceText: string;
  onSelectionChange?: (selection: SelectionRecord | null) => void;
}

export function useSelection(options: UseSelectionOptions) {
  const { projectId, sourceType, sourceId, sourceText, onSelectionChange } = options;
  const textareaRef = useRef<HTMLTextAreaElement | HTMLDivElement>(null);
  
  const { setActiveSelection, addSelectionToHistory, clearSelections } = useSelectionStore();

  const handleSelect = useCallback((event: Event) => {
    const target = event.target as HTMLTextAreaElement | HTMLDivElement;
    const selection = window.getSelection();
    
    if (!selection || selection.rangeCount === 0) {
      return;
    }
    
    const range = selection.getRangeAt(0);
    const selectionStart = target instanceof HTMLTextAreaElement 
      ? target.selectionStart 
      : getTextNodeOffset(target, range.startContainer, range.startOffset);
    
    const selectionEnd = target instanceof HTMLTextAreaElement
      ? target.selectionEnd
      : getTextNodeOffset(target, range.endContainer, range.endOffset);
    
    if (selectionStart === selectionEnd) {
      return; // No actual selection
    }
    
    const selectedText = sourceText.slice(selectionStart, selectionEnd);
    
    if (!selectedText.trim()) {
      return; // Empty selection
    }
    
    const selectionRecord = createSelectionRecord(
      projectId,
      sourceType,
      sourceId,
      selectionStart,
      selectionEnd,
      selectedText,
    );
    
    setActiveSelection(selectionRecord);
    addSelectionToHistory(selectionRecord);
    
    if (onSelectionChange) {
      onSelectionChange(selectionRecord);
    }
  }, [projectId, sourceType, sourceId, sourceText, setActiveSelection, addSelectionToHistory, onSelectionChange]);

  const handleClear = useCallback(() => {
    clearSelections();
    if (onSelectionChange) {
      onSelectionChange(null);
    }
  }, [clearSelections, onSelectionChange]);

  const handleDoubleClick = useCallback((event: React.MouseEvent) => {
    // Word selection on double-click is handled by browser
    // This just ensures the selection event fires
    setTimeout(() => {
      handleSelect({ target: event.target as EventTarget } as Event);
    }, 0);
  }, [handleSelect]);

  const getSelectionBounds = useCallback((): { top: number; bottom: number } | null => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return null;
    }
    
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    return {
      top: rect.top,
      bottom: rect.bottom,
    };
  }, []);

  return {
    textareaRef,
    handleSelect,
    handleClear,
    handleDoubleClick,
    getSelectionBounds,
  };
}

// Helper to get offset from text node for contenteditable divs
function getTextNodeOffset(
  root: Element,
  node: Node,
  offset: number,
): number {
  let totalOffset = 0;
  
  const traverse = (n: Node): number => {
    let nodeOffset = 0;
    let current: Node | null = n;
    
    while (current && current !== root) {
      if (current.previousSibling) {
        current = current.previousSibling;
        nodeOffset += getLength(current);
      } else {
        current = current.parentNode;
        if (current === root) {
          nodeOffset += offset;
          break;
        }
      }
    }
    
    return nodeOffset;
  };
  
  totalOffset = traverse(node);
  return totalOffset;
}

function getLength(node: Node): number {
  if (node.nodeType === Node.TEXT_NODE) {
    return node.textContent?.length || 0;
  }
  
  if (node.nodeType === Node.ELEMENT_NODE) {
    const element = node as Element;
    if (element.tagName === 'BR') {
      return 1;
    }
    
    let length = 0;
    for (let i = 0; i < element.childNodes.length; i++) {
      length += getLength(element.childNodes[i]);
    }
    return length;
  }
  
  return 0;
}
