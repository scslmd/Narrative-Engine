interface DraftFormProps {
  title: string;
  content: string;
  isPending: boolean;
  onTitleChange: (title: string) => void;
  onContentChange: (content: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isDark: boolean;
}

export function DraftForm({ title, content, isPending, onTitleChange, onContentChange, onSubmit, onCancel, isDark }: DraftFormProps) {
  const hasTitle = title.trim().length > 0;

  return (
    <div className={`p-2 rounded-md border ${isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-300'}`}>
      <input
        type="text"
        placeholder="Draft title"
        value={title}
        onChange={(e) => onTitleChange(e.target.value)}
        className={`w-full text-xs px-2 py-1.5 rounded border mb-1.5 outline-none focus:border-indigo-500 ${isDark ? 'bg-slate-800 border-slate-600 text-slate-200 placeholder:text-slate-500' : 'bg-white border-slate-200 text-slate-800 placeholder:text-slate-400'}`}
      />
      <textarea
        placeholder="Draft content (optional)"
        value={content}
        onChange={(e) => onContentChange(e.target.value)}
        className={`w-full text-xs px-2 py-1.5 rounded border outline-none focus:border-indigo-500 resize-none ${isDark ? 'bg-slate-800 border-slate-600 text-slate-200 placeholder:text-slate-500' : 'bg-white border-slate-200 text-slate-800 placeholder:text-slate-400'}`}
        rows={3}
      />
      <div className="flex gap-1.5 mt-1.5">
        <button
          onClick={onSubmit}
          disabled={!hasTitle || isPending}
          className="text-[10px] px-2 py-1 rounded bg-green-600 text-white hover:bg-green-500 disabled:opacity-40 font-medium"
        >
          {isPending ? 'Creating...' : 'Create'}
        </button>
        <button
          onClick={onCancel}
          className={`text-[10px] px-2 py-1 rounded font-medium ${isDark ? 'text-slate-400 hover:text-slate-200 bg-slate-700' : 'text-slate-500 hover:text-slate-700 bg-slate-200'}`}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
