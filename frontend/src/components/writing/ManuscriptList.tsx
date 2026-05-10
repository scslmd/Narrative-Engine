import { useState, useMemo } from 'react';
import { BookOpen, ChevronRight, ChevronDown, Text } from 'lucide-react';
import type { ManuscriptDocument } from '../../types/drafting';

/** Parse markdown headings and paragraphs from content into a flat list. */
interface ParsedLine {
  type: 'heading' | 'paragraph';
  level: number;
  text: string;
  lineIndex: number;
}

function parseContent(content: string, includeParagraphs: boolean): ParsedLine[] {
  const lines = content.split('\n');
  const results: ParsedLine[] = [];
  let lineIdx = 0;

  for (const raw of lines) {
    const trimmed = raw.trim();
    if (!trimmed) {
      lineIdx++;
      continue;
    }
    const match = trimmed.match(/^#{1,3}\s+(?:P-\d+\s*[|–-]\s*)?(.+)$/);
    if (match) {
      results.push({ type: 'heading', level: trimmed.startsWith('###') ? 3 : trimmed.startsWith('##') ? 2 : 1, text: match[1].trim(), lineIndex: lineIdx });
    } else if (includeParagraphs) {
      const preview = trimmed.slice(0, 60).replace(/\s+/g, ' ');
      results.push({ type: 'paragraph', level: 0, text: preview, lineIndex: lineIdx });
    }
    lineIdx++;
  }
  return results;
}

/** Build a unique anchor ID from heading text. */
function headingAnchor(text: string): string {
  return 'h-' + text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

interface OutlineNode {
  type: 'heading' | 'paragraph';
  level: number;
  text: string;
  lineIndex: number;
  anchor?: string;
  children: OutlineNode[];
}

function buildOutlineTree(parsed: ParsedLine[]): OutlineNode[] {
  const root: OutlineNode[] = [];
  // Stack tracks the current path of heading nodes: [h1, h2, h3]
  const stack: { level: number; node: OutlineNode }[] = [];

  for (const line of parsed) {
    if (line.type === 'heading') {
      const node: OutlineNode = { ...line, anchor: headingAnchor(line.text), children: [] };
      // Pop stack until we find a parent with lower level
      while (stack.length > 0 && stack[stack.length - 1].level >= line.level) {
        stack.pop();
      }
      if (stack.length === 0) {
        root.push(node);
      } else {
        stack[stack.length - 1].node.children.push(node);
      }
      stack.push({ level: line.level, node });
    } else {
      // Paragraph — attach to the deepest heading in the stack
      if (stack.length > 0) {
        stack[stack.length - 1].node.children.push({ ...line, children: [] });
      } else {
        // No heading yet — attach to root
        root.push({ ...line, children: [] });
      }
    }
  }
  return root;
}

/** Extract the first markdown heading from content. */
function extractHeading(content: string): string | null {
  const match = content.match(/^#\s+(?:P-\d+\s*[|–-]\s*)?(.+)$/m);
  return match?.[1]?.trim() || null;
}

interface OutlineItemProps {
  node: OutlineNode;
  depth: number;
  isDark: boolean;
  onNavigate?: (lineIndex: number) => void;
}

function OutlineItem({ node, depth, isDark, onNavigate }: OutlineItemProps) {
  const [expanded, setExpanded] = useState(node.type === 'heading' && node.level < 3);
  const hasChildren = node.children.length > 0;

  const handleClick = () => {
    if (hasChildren) {
      setExpanded(!expanded);
    }
    if (onNavigate && node.lineIndex !== undefined) {
      onNavigate(node.lineIndex);
    }
  };

  return (
    <div>
      <button
        onClick={handleClick}
        className={`w-full flex items-center gap-1 text-left py-0.5 rounded px-1 transition-colors ${
          isDark ? 'hover:bg-slate-800/40' : 'hover:bg-slate-50'
        }`}
        style={{ paddingLeft: `${depth * 12}px` }}
      >
        {hasChildren && (
          <span className="flex-shrink-0 text-muted">
            {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </span>
        )}
        {!hasChildren && <span className="w-3 flex-shrink-0" />}
        {node.type === 'paragraph' && <Text className="w-3 h-3 flex-shrink-0 text-muted" />}
        <span className={`truncate ${
          node.type === 'heading'
            ? node.level === 1
              ? 'text-sm font-medium'
              : node.level === 2
                ? 'text-xs font-medium'
                : 'text-xs'
            : 'text-xs text-muted italic'
        } ${isDark ? (node.type === 'heading' && node.level === 1 ? 'text-slate-200' : 'text-slate-400') : (node.type === 'heading' && node.level === 1 ? 'text-slate-800' : 'text-slate-600')}`}>
          {node.text}
        </span>
      </button>
      {expanded && hasChildren && (
        <div className="mt-0.5">
          {node.children.map((child, i) => (
            <OutlineItem key={i} node={child} depth={depth + 1} isDark={isDark} onNavigate={onNavigate} />
          ))}
        </div>
      )}
    </div>
  );
}

interface ManuscriptListProps {
  documents: ManuscriptDocument[];
  selectedDocumentId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
  isDark: boolean;
  includeParagraphs?: boolean;
  onNavigate?: (documentId: string, lineIndex: number) => void;
}

export function ManuscriptList({ documents, selectedDocumentId, isLoading, onSelect, isDark, includeParagraphs = false, onNavigate }: ManuscriptListProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const groups = useMemo(() => {
    const grouped = new Map<string | null, ManuscriptDocument[]>();
    for (const doc of documents) {
      const key = doc.chapter_id || 'ungrouped';
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key)!.push(doc);
    }
    return Array.from(grouped.entries())
      .sort((a, b) => {
        if (a[0] === null) return 1;
        if (b[0] === null) return -1;
        return String(a[0]).localeCompare(String(b[0]));
      })
      .map(([chapterId, docs]) => {
        const firstDoc = docs[0];
        return {
          chapterId,
          title: firstDoc?.title ?? 'Untitled',
          heading: firstDoc ? extractHeading(firstDoc.content) : null,
          documents: docs.sort((a, b) => a.version - b.version),
        };
      });
  }, [documents]);

  const toggleGroup = (key: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className={`h-8 rounded animate-shimmer ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`}></div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-6 text-muted">
        <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-40" />
        <p className="text-xs">No manuscript records yet</p>
        <p className="text-xs mt-1">Create manuscripts via the drafting workflow.</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {groups.map((group) => {
        const groupKey = group.chapterId ?? 'ungrouped';
        const isExpanded = expandedGroups.has(groupKey);
        const hasMultiple = group.documents.length > 1;

        return (
          <div key={groupKey}>
            {/* Chapter header */}
            <button
              onClick={() => toggleGroup(groupKey)}
              className={`w-full flex items-center gap-1.5 px-2 py-1.5 rounded-md text-left transition-colors ${
                isDark ? 'hover:bg-slate-800/60' : 'hover:bg-slate-50'
              }`}
            >
              {hasMultiple && (
                <span className="text-muted flex-shrink-0">
                  {isExpanded ? (
                    <ChevronDown className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5" />
                  )}
                </span>
              )}
              {!hasMultiple && <span className="w-4 flex-shrink-0" />}
              <span className={`text-sm font-medium truncate ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                {group.title}
              </span>
              {hasMultiple && (
                <span className={`ml-auto text-[10px] flex-shrink-0 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                  {group.documents.length}
                </span>
              )}
            </button>

            {/* Version items */}
            {(isExpanded || !hasMultiple) && (
              <div className="ml-4 pl-3 border-l space-y-1 mt-0.5" style={{ borderColor: isDark ? '#1e293b' : '#e2e8f0' }}>
                {group.documents.map((doc) => {
                  const parsed = parseContent(doc.content, includeParagraphs);
                  const tree = buildOutlineTree(parsed);
                  const hasOutline = tree.length > 0;

                  return (
                    <div key={doc.document_id}>
                      {/* Version label */}
                      <button
                        onClick={() => onSelect(doc.document_id)}
                        className={`w-full text-left px-2 py-0.5 rounded-md text-sm transition-all ${
                          selectedDocumentId === doc.document_id
                            ? isDark
                              ? 'bg-blue-950/40 text-blue-300'
                              : 'bg-blue-50 text-blue-700'
                            : isDark
                              ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                        }`}
                      >
                        <span className="truncate block">v{doc.version}</span>
                      </button>

                      {/* Outline tree under version */}
                      {hasOutline && (
                        <div className="mt-0.5">
                          {tree.map((node, i) => (
                            <OutlineItem
                              key={i}
                              node={node}
                              depth={1}
                              isDark={isDark}
                              onNavigate={(lineIndex) => onNavigate?.(doc.document_id, lineIndex)}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
